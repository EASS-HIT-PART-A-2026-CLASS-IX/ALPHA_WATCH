import json

import pytest
from sqlmodel import Session, SQLModel, create_engine, select
from sqlmodel.pool import StaticPool

from app.models import MarketSnapshot
from app.refresh import refresh_symbol
from app.schemas import (
    HistoryPoint,
    MarketHistoryRead,
    MarketNewsRead,
    MarketProfileRead,
    MarketQuoteRead,
    NewsItem,
)


class FakeRedis:
    def __init__(self, locked: bool = False):
        self.keys = {"alphawatch:refresh:AAPL"} if locked else set()

    async def set(self, name: str, value: str, nx: bool = False, ex: int | None = None):
        if nx and name in self.keys:
            return False
        self.keys.add(name)
        return True

    async def delete(self, *names: str):
        for name in names:
            self.keys.discard(name)

    async def aclose(self):
        return None


def session_factory():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)

    def factory() -> Session:
        return Session(engine)

    return factory


def fake_profile(symbol: str) -> MarketProfileRead:
    return MarketProfileRead(
        symbol=symbol,
        company_name="Apple Inc.",
        sector="Technology",
        industry="Consumer Electronics",
        website="https://www.apple.com",
        description="Apple designs consumer technology.",
        market_cap=1_000_000,
        country="United States",
        source_mode="mock",
    )


def fake_quote(symbol: str) -> MarketQuoteRead:
    return MarketQuoteRead(
        symbol=symbol,
        price=190.0,
        change=1.5,
        change_percent=0.8,
        previous_close=188.5,
        open=189.0,
        day_high=191.0,
        day_low=188.0,
        volume=10_000,
        source_mode="mock",
    )


def fake_history(symbol: str) -> MarketHistoryRead:
    return MarketHistoryRead(
        symbol=symbol,
        interval="1day",
        range="30d",
        series=[HistoryPoint(timestamp="2026-06-01", close=190.0)],
        source_mode="mock",
    )


def fake_news(symbol: str) -> MarketNewsRead:
    return MarketNewsRead(
        symbol=symbol,
        items=[
            NewsItem(
                title=f"{symbol} update",
                source="AlphaWatch Mock",
                published_at="2026-06-01 09:00",
                url="https://example.com",
            )
        ],
        source_mode="mock",
    )


@pytest.mark.anyio
async def test_refresh_symbol_uses_redis_idempotency(monkeypatch: pytest.MonkeyPatch) -> None:
    called = False

    def should_not_run(symbol: str):
        nonlocal called
        called = True
        return fake_profile(symbol)

    monkeypatch.setattr("app.refresh.get_market_profile", should_not_run)

    result = await refresh_symbol("aapl", FakeRedis(locked=True), session_factory=session_factory())

    assert result.status == "skipped"
    assert result.refreshed is False
    assert called is False


@pytest.mark.anyio
async def test_refresh_symbol_retries_and_persists_snapshot(monkeypatch: pytest.MonkeyPatch) -> None:
    factory = session_factory()
    quote_calls = 0

    def flaky_quote(symbol: str) -> MarketQuoteRead:
        nonlocal quote_calls
        quote_calls += 1
        if quote_calls == 1:
            raise RuntimeError("temporary quote failure")
        return fake_quote(symbol)

    monkeypatch.setattr("app.refresh.get_market_profile", fake_profile)
    monkeypatch.setattr("app.refresh.get_quote", flaky_quote)
    monkeypatch.setattr("app.refresh.get_history", fake_history)
    monkeypatch.setattr("app.refresh.get_news", fake_news)

    result = await refresh_symbol(
        "aapl",
        FakeRedis(),
        session_factory=factory,
        retries=2,
        retry_delay_seconds=0,
    )

    assert result.status == "ok"
    assert result.refreshed is True
    assert quote_calls == 2

    with factory() as session:
        snapshot = session.exec(select(MarketSnapshot)).one()
        assert snapshot.symbol == "AAPL"
        assert snapshot.status == "ok"
        assert json.loads(snapshot.quote_json)["price"] == 190.0
