"""
market_routes.py

Each endpoint tries to fetch real data from Alpha Vantage.
If the API key is missing OR the external request fails for any reason,
it falls back to built-in mock data instead of returning an error.
The response always includes source_mode: "live" | "mock" so the UI
can optionally show a banner when demo data is being used.
"""
import logging

from fastapi import APIRouter, Depends

from app.auth import get_current_user
from app.company_lookup import (
    CompanyLookupConfigError,
    CompanyLookupNotFoundError,
    CompanyLookupServiceError,
    _av_get,
    _get_api_key,
    fetch_company_overview,
)
from app.mock_data import mock_history, mock_news, mock_profile, mock_quote
from app.models import User
from app.schemas import (
    HistoryPoint,
    MarketHistoryRead,
    MarketNewsRead,
    MarketProfileRead,
    MarketQuoteRead,
    NewsItem,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/market", tags=["market"])


def _sym(raw: str) -> str:
    return raw.strip().upper()


# ── Profile ───────────────────────────────────────────────────────────────────

@router.get("/profile/{symbol}", response_model=MarketProfileRead)
def get_market_profile(
    symbol: str,
    _user: User = Depends(get_current_user),
) -> MarketProfileRead:
    """Company profile — falls back to mock when API key is absent or call fails."""
    sym = _sym(symbol)
    try:
        data = fetch_company_overview(sym)
        return MarketProfileRead(**data, source_mode="live")
    except (CompanyLookupConfigError, CompanyLookupNotFoundError, CompanyLookupServiceError) as exc:
        logger.info("Profile fallback for %s: %s", sym, exc)
        return MarketProfileRead(**mock_profile(sym))


# ── Quote ─────────────────────────────────────────────────────────────────────

@router.get("/quote/{symbol}", response_model=MarketQuoteRead)
def get_quote(
    symbol: str,
    _user: User = Depends(get_current_user),
) -> MarketQuoteRead:
    """Live quote — falls back to mock when API key is absent or call fails."""
    sym = _sym(symbol)
    try:
        api_key = _get_api_key()
        data = _av_get({"function": "GLOBAL_QUOTE", "symbol": sym, "apikey": api_key})
        quote = data.get("Global Quote", {})
        price_raw = quote.get("05. price")
        if not price_raw:
            raise CompanyLookupNotFoundError(f"No quote for '{sym}'")

        def _f(key: str) -> float:
            raw = quote.get(key, "0").replace("%", "").strip()
            try:
                return float(raw)
            except ValueError:
                return 0.0

        return MarketQuoteRead(
            symbol=sym,
            price=_f("05. price"),
            change=_f("09. change"),
            change_percent=_f("10. change percent"),
            previous_close=_f("08. previous close") or None,
            source_mode="live",
        )
    except (CompanyLookupConfigError, CompanyLookupNotFoundError, CompanyLookupServiceError) as exc:
        logger.info("Quote fallback for %s: %s", sym, exc)
        return MarketQuoteRead(**mock_quote(sym))


# ── History ───────────────────────────────────────────────────────────────────

@router.get("/history/{symbol}", response_model=MarketHistoryRead)
def get_history(
    symbol: str,
    _user: User = Depends(get_current_user),
) -> MarketHistoryRead:
    """30-day price history — falls back to mock when API key is absent or call fails."""
    sym = _sym(symbol)
    try:
        api_key = _get_api_key()
        data = _av_get({
            "function": "TIME_SERIES_DAILY",
            "symbol": sym,
            "outputsize": "compact",
            "apikey": api_key,
        })
        time_series = data.get("Time Series (Daily)")
        if not time_series:
            raise CompanyLookupNotFoundError(f"No history for '{sym}'")

        sorted_dates = sorted(time_series.keys(), reverse=True)[:30]
        series = [
            HistoryPoint(date=d, close=float(time_series[d]["4. close"]))
            for d in reversed(sorted_dates)
        ]
        return MarketHistoryRead(symbol=sym, series=series, source_mode="live")
    except (CompanyLookupConfigError, CompanyLookupNotFoundError, CompanyLookupServiceError) as exc:
        logger.info("History fallback for %s: %s", sym, exc)
        raw = mock_history(sym)
        series = [HistoryPoint(**p) for p in raw["series"]]
        return MarketHistoryRead(symbol=sym, series=series, source_mode="mock")


# ── News ──────────────────────────────────────────────────────────────────────

@router.get("/news/{symbol}", response_model=MarketNewsRead)
def get_news(
    symbol: str,
    _user: User = Depends(get_current_user),
) -> MarketNewsRead:
    """Recent news — falls back to mock when API key is absent or call fails."""
    sym = _sym(symbol)
    try:
        api_key = _get_api_key()
        data = _av_get({
            "function": "NEWS_SENTIMENT",
            "tickers": sym,
            "limit": 10,
            "apikey": api_key,
        })
        feed = data.get("feed", [])
        items = []
        for article in feed[:10]:
            raw_dt = article.get("time_published", "")
            published_at = (
                f"{raw_dt[:4]}-{raw_dt[4:6]}-{raw_dt[6:8]} {raw_dt[9:11]}:{raw_dt[11:13]}"
                if len(raw_dt) >= 13
                else raw_dt
            )
            items.append(NewsItem(
                title=article.get("title", ""),
                source=article.get("source", ""),
                published_at=published_at,
                url=article.get("url", ""),
                summary=article.get("summary") or None,
            ))
        return MarketNewsRead(symbol=sym, items=items, source_mode="live")
    except (CompanyLookupConfigError, CompanyLookupServiceError) as exc:
        logger.info("News fallback for %s: %s", sym, exc)
        raw = mock_news(sym)
        items = [NewsItem(**i) for i in raw["items"]]
        return MarketNewsRead(symbol=sym, items=items, source_mode="mock")
