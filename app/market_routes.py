from fastapi import APIRouter, Depends, HTTPException, status

from app.auth import get_current_user
from app.company_lookup import (
    CompanyLookupConfigError,
    CompanyLookupNotFoundError,
    CompanyLookupServiceError,
    _av_get,
    _get_api_key,
    fetch_company_overview,
)
from app.models import User
from app.schemas import (
    HistoryPoint,
    MarketHistoryRead,
    MarketNewsRead,
    MarketProfileRead,
    MarketQuoteRead,
    NewsItem,
)

router = APIRouter(prefix="/market", tags=["market"])


def _symbol(raw: str) -> str:
    return raw.strip().upper()


def _handle_lookup_error(error: Exception) -> None:
    """Convert company_lookup exceptions into HTTP responses."""
    if isinstance(error, CompanyLookupConfigError):
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(error))
    if isinstance(error, CompanyLookupNotFoundError):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error))
    if isinstance(error, CompanyLookupServiceError):
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(error))


# ── Profile ───────────────────────────────────────────────────────────────────

@router.get("/profile/{symbol}", response_model=MarketProfileRead)
def get_market_profile(
    symbol: str,
    _user: User = Depends(get_current_user),
) -> MarketProfileRead:
    """Return a rich company profile from Alpha Vantage OVERVIEW."""
    try:
        data = fetch_company_overview(_symbol(symbol))
    except Exception as exc:
        _handle_lookup_error(exc)
        raise
    return MarketProfileRead(**data)


# ── Quote ─────────────────────────────────────────────────────────────────────

@router.get("/quote/{symbol}", response_model=MarketQuoteRead)
def get_quote(
    symbol: str,
    _user: User = Depends(get_current_user),
) -> MarketQuoteRead:
    """Return the latest price quote from Alpha Vantage GLOBAL_QUOTE."""
    sym = _symbol(symbol)
    try:
        api_key = _get_api_key()
        data = _av_get({"function": "GLOBAL_QUOTE", "symbol": sym, "apikey": api_key})
    except CompanyLookupConfigError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    except CompanyLookupServiceError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

    quote = data.get("Global Quote", {})
    price_raw = quote.get("05. price")
    if not price_raw:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No quote data found for symbol '{sym}'",
        )

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
    )


# ── History ───────────────────────────────────────────────────────────────────

@router.get("/history/{symbol}", response_model=MarketHistoryRead)
def get_history(
    symbol: str,
    _user: User = Depends(get_current_user),
) -> MarketHistoryRead:
    """Return the last 30 trading days of daily close prices."""
    sym = _symbol(symbol)
    try:
        api_key = _get_api_key()
        data = _av_get({
            "function": "TIME_SERIES_DAILY",
            "symbol": sym,
            "outputsize": "compact",
            "apikey": api_key,
        })
    except CompanyLookupConfigError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    except CompanyLookupServiceError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

    time_series = data.get("Time Series (Daily)")
    if not time_series:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No history data found for symbol '{sym}'",
        )

    # Sort descending, take last 30 days, return ascending for charting
    sorted_dates = sorted(time_series.keys(), reverse=True)[:30]
    series = [
        HistoryPoint(date=date, close=float(time_series[date]["4. close"]))
        for date in reversed(sorted_dates)
    ]
    return MarketHistoryRead(symbol=sym, series=series)


# ── News ──────────────────────────────────────────────────────────────────────

@router.get("/news/{symbol}", response_model=MarketNewsRead)
def get_news(
    symbol: str,
    _user: User = Depends(get_current_user),
) -> MarketNewsRead:
    """Return up to 10 recent news items from Alpha Vantage NEWS_SENTIMENT."""
    sym = _symbol(symbol)
    try:
        api_key = _get_api_key()
        data = _av_get({
            "function": "NEWS_SENTIMENT",
            "tickers": sym,
            "limit": 10,
            "apikey": api_key,
        })
    except CompanyLookupConfigError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    except CompanyLookupServiceError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

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

    return MarketNewsRead(symbol=sym, items=items)
