import asyncio
import json
import logging
import os
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from datetime import datetime, timezone

from pydantic import BaseModel
from sqlmodel import Session, col, select

from app.database import engine
from app.market_routes import get_history, get_market_profile, get_news, get_quote
from app.models import MarketSnapshot, Stock
from app.redis_client import AsyncRedisLike, get_redis_client

logger = logging.getLogger(__name__)

DEFAULT_CONCURRENCY = int(os.getenv("REFRESH_CONCURRENCY", "4"))
DEFAULT_RETRIES = int(os.getenv("REFRESH_RETRIES", "2"))
IDEMPOTENCY_TTL_SECONDS = int(os.getenv("REFRESH_IDEMPOTENCY_TTL_SECONDS", "300"))


@dataclass(frozen=True)
class RefreshResult:
    symbol: str
    refreshed: bool
    attempts: int
    status: str
    error: str | None = None


def normalize_symbols(symbols: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    normalized: list[str] = []
    for raw in symbols:
        symbol = raw.strip().upper()
        if symbol and symbol not in seen:
            seen.add(symbol)
            normalized.append(symbol)
    return normalized


def saved_symbols(session_factory: Callable[[], Session] | None = None) -> list[str]:
    factory = session_factory or (lambda: Session(engine))
    with factory() as session:
        rows = session.exec(select(Stock.symbol).order_by(col(Stock.symbol))).all()
    return normalize_symbols(rows)


def _dump_model(value: BaseModel) -> str:
    return json.dumps(value.model_dump(mode="json"), sort_keys=True)


async def _call_with_retry(
    symbol: str,
    fetcher: Callable[[str], BaseModel],
    retries: int,
    delay_seconds: float,
) -> tuple[BaseModel, int]:
    attempt = 0
    while True:
        attempt += 1
        try:
            return await asyncio.to_thread(fetcher, symbol), attempt
        except Exception:
            if attempt > retries:
                raise
            await asyncio.sleep(delay_seconds * attempt)


async def refresh_symbol(
    symbol: str,
    redis_client: AsyncRedisLike,
    session_factory: Callable[[], Session] | None = None,
    retries: int = DEFAULT_RETRIES,
    idempotency_ttl_seconds: int = IDEMPOTENCY_TTL_SECONDS,
    retry_delay_seconds: float = 0.25,
) -> RefreshResult:
    clean_symbol = symbol.strip().upper()
    if not clean_symbol:
        return RefreshResult(symbol=symbol, refreshed=False, attempts=0, status="skipped", error="empty symbol")

    lock_key = f"alphawatch:refresh:{clean_symbol}"
    acquired = await redis_client.set(lock_key, "running", nx=True, ex=idempotency_ttl_seconds)
    if not acquired:
        return RefreshResult(symbol=clean_symbol, refreshed=False, attempts=0, status="skipped")

    factory = session_factory or (lambda: Session(engine))
    attempts = 0
    try:
        profile, used = await _call_with_retry(clean_symbol, get_market_profile, retries, retry_delay_seconds)
        attempts += used
        quote, used = await _call_with_retry(clean_symbol, get_quote, retries, retry_delay_seconds)
        attempts += used
        history, used = await _call_with_retry(clean_symbol, get_history, retries, retry_delay_seconds)
        attempts += used
        news, used = await _call_with_retry(clean_symbol, get_news, retries, retry_delay_seconds)
        attempts += used

        snapshot = MarketSnapshot(
            symbol=clean_symbol,
            refreshed_at=datetime.now(timezone.utc),
            status="ok",
            quote_source_mode=quote.source_mode,
            profile_source_mode=profile.source_mode,
            history_source_mode=history.source_mode,
            news_source_mode=news.source_mode,
            quote_json=_dump_model(quote),
            profile_json=_dump_model(profile),
            history_json=_dump_model(history),
            news_json=_dump_model(news),
        )
        with factory() as session:
            session.add(snapshot)
            session.commit()

        logger.info("refreshed %s quote=%s profile=%s history=%s news=%s", clean_symbol, quote.source_mode, profile.source_mode, history.source_mode, news.source_mode)
        return RefreshResult(symbol=clean_symbol, refreshed=True, attempts=attempts, status="ok")
    except Exception as exc:
        message = str(exc)
        with factory() as session:
            session.add(
                MarketSnapshot(
                    symbol=clean_symbol,
                    refreshed_at=datetime.now(timezone.utc),
                    status="error",
                    error=message,
                )
            )
            session.commit()
        logger.exception("refresh failed for %s", clean_symbol)
        return RefreshResult(symbol=clean_symbol, refreshed=False, attempts=attempts, status="error", error=message)
    finally:
        await redis_client.delete(lock_key)


async def refresh_symbols(
    symbols: Iterable[str],
    redis_client: AsyncRedisLike | None = None,
    session_factory: Callable[[], Session] | None = None,
    concurrency: int = DEFAULT_CONCURRENCY,
    retries: int = DEFAULT_RETRIES,
) -> list[RefreshResult]:
    clean_symbols = normalize_symbols(symbols)
    owns_redis = redis_client is None
    redis_instance = redis_client or get_redis_client()
    semaphore = asyncio.Semaphore(max(1, concurrency))

    async def run_one(symbol: str) -> RefreshResult:
        async with semaphore:
            return await refresh_symbol(symbol, redis_instance, session_factory=session_factory, retries=retries)

    try:
        return await asyncio.gather(*(run_one(symbol) for symbol in clean_symbols))
    finally:
        if owns_redis:
            await redis_instance.aclose()


async def refresh_saved_stocks(
    symbols: Iterable[str] | None = None,
    redis_client: AsyncRedisLike | None = None,
    session_factory: Callable[[], Session] | None = None,
    concurrency: int = DEFAULT_CONCURRENCY,
    retries: int = DEFAULT_RETRIES,
) -> list[RefreshResult]:
    target_symbols = normalize_symbols(symbols) if symbols else saved_symbols(session_factory)
    return await refresh_symbols(
        target_symbols,
        redis_client=redis_client,
        session_factory=session_factory,
        concurrency=concurrency,
        retries=retries,
    )
