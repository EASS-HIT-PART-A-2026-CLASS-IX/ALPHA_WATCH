"""
market_routes.py

Uses yfinance (free, no API key) as the primary market data provider.
Falls back to built-in mock data when the call fails or returns empty.
Every response includes source_mode: "live" | "mock".

Key design notes:
- Quote uses ticker.fast_info (fast, lightweight, doesn't hit slow endpoints)
- Profile uses ticker.info (full info, slower but only needed for description/sector)
- History uses ticker.history() (reliable daily candles)
- News uses ticker.news (reliable)
"""
import logging
from datetime import datetime

from fastapi import APIRouter, Depends

from app.auth import get_current_user
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


def _yf_ticker(symbol: str):
    """Lazy-import yfinance."""
    import yfinance as yf
    return yf.Ticker(symbol)


def _to_float(value) -> float | None:
    """Convert a value to float, treating zero/None/NaN as None."""
    if value is None:
        return None
    try:
        f = float(value)
        if f != f or f == 0:  # NaN or zero
            return None
        return f
    except (TypeError, ValueError):
        return None


# ── Profile ───────────────────────────────────────────────────────────────────

@router.get("/profile/{symbol}", response_model=MarketProfileRead)
def get_market_profile(symbol: str, _user: User = Depends(get_current_user)) -> MarketProfileRead:
    sym = _sym(symbol)
    try:
        ticker = _yf_ticker(sym)
        info = ticker.info or {}
        name = info.get("longName") or info.get("shortName")
        if not name:
            raise ValueError(f"No profile name for {sym}")

        market_cap_raw = info.get("marketCap")
        market_cap = int(market_cap_raw) if market_cap_raw else None

        description = (
            info.get("longBusinessSummary")
            or info.get("summary")
            or f"{name} operates in the {info.get('industry', 'N/A')} industry."
        )

        return MarketProfileRead(
            symbol=sym,
            company_name=name,
            sector=info.get("sector") or "Unknown",
            industry=info.get("industry") or "Unknown",
            website=info.get("website") or "",
            description=description,
            market_cap=market_cap,
            country=info.get("country") or "United States",
            source_mode="live",
        )
    except Exception as exc:
        logger.warning("Profile fallback for %s: %r", sym, exc)
        return MarketProfileRead(**mock_profile(sym))


# ── Quote ─────────────────────────────────────────────────────────────────────

@router.get("/quote/{symbol}", response_model=MarketQuoteRead)
def get_quote(symbol: str, _user: User = Depends(get_current_user)) -> MarketQuoteRead:
    """
    Uses ticker.fast_info — a lightweight Yahoo endpoint that returns the
    current quote without the heavy .info call. This is reliable and fast.
    """
    sym = _sym(symbol)
    try:
        ticker = _yf_ticker(sym)
        fast = ticker.fast_info

        # fast_info is a dict-like with attribute access. Try both forms.
        def _get(*keys):
            for k in keys:
                # try as attribute
                try:
                    v = getattr(fast, k, None)
                    if v is not None:
                        return v
                except Exception:
                    pass
                # try as key
                try:
                    v = fast[k]
                    if v is not None:
                        return v
                except Exception:
                    pass
            return None

        price = _to_float(_get("last_price", "lastPrice", "regular_market_price"))
        prev_close = _to_float(_get("previous_close", "previousClose", "regular_market_previous_close"))
        open_p = _to_float(_get("open", "regular_market_open"))
        day_high = _to_float(_get("day_high", "dayHigh", "regular_market_day_high"))
        day_low = _to_float(_get("day_low", "dayLow", "regular_market_day_low"))
        volume_raw = _get("last_volume", "lastVolume", "regular_market_volume")
        volume = int(volume_raw) if volume_raw else None

        if price is None:
            raise ValueError(f"No price for {sym}")

        change = round(price - prev_close, 4) if prev_close else 0.0
        change_pct = round((change / prev_close) * 100, 4) if prev_close else 0.0

        return MarketQuoteRead(
            symbol=sym,
            price=price,
            change=change,
            change_percent=change_pct,
            previous_close=prev_close,
            open=open_p,
            day_high=day_high,
            day_low=day_low,
            volume=volume,
            source_mode="live",
        )
    except Exception as exc:
        logger.warning("Quote fallback for %s: %r", sym, exc)
        return MarketQuoteRead(**mock_quote(sym))


# ── History ───────────────────────────────────────────────────────────────────

@router.get("/history/{symbol}", response_model=MarketHistoryRead)
def get_history(symbol: str, _user: User = Depends(get_current_user)) -> MarketHistoryRead:
    sym = _sym(symbol)
    try:
        ticker = _yf_ticker(sym)
        hist = ticker.history(period="1mo", auto_adjust=False)
        if hist is None or hist.empty:
            raise ValueError(f"Empty history for {sym}")

        series = []
        for idx, row in hist.iterrows():
            try:
                close = float(row["Close"])
            except (KeyError, TypeError, ValueError):
                continue
            if close != close:  # NaN
                continue
            ts = idx.date().isoformat() if hasattr(idx, "date") else str(idx)[:10]
            series.append(HistoryPoint(timestamp=ts, close=round(close, 4)))

        if not series:
            raise ValueError(f"No usable history rows for {sym}")

        series = series[-30:]
        return MarketHistoryRead(symbol=sym, interval="1day", range="30d", series=series, source_mode="live")
    except Exception as exc:
        logger.warning("History fallback for %s: %r", sym, exc)
        raw = mock_history(sym)
        series = [HistoryPoint(**p) for p in raw["series"]]
        return MarketHistoryRead(symbol=sym, interval="1day", range="30d", series=series, source_mode="mock")


# ── News ──────────────────────────────────────────────────────────────────────

@router.get("/news/{symbol}", response_model=MarketNewsRead)
def get_news(symbol: str, _user: User = Depends(get_current_user)) -> MarketNewsRead:
    sym = _sym(symbol)
    try:
        ticker = _yf_ticker(sym)
        raw_news = ticker.news or []
        if not raw_news:
            raise ValueError(f"No news for {sym}")

        items = []
        for article in raw_news[:10]:
            # yfinance returns dicts in 2 shapes — try both
            content = article.get("content") if isinstance(article.get("content"), dict) else article

            title = content.get("title") or article.get("title") or ""

            # URL: try multiple possible locations
            url = ""
            for url_key in ("canonicalUrl", "clickThroughUrl"):
                u = content.get(url_key)
                if isinstance(u, dict):
                    url = u.get("url", "") or url
                elif isinstance(u, str):
                    url = u or url
            url = url or content.get("link") or article.get("link") or ""

            # Source
            provider = content.get("provider")
            if isinstance(provider, dict):
                source = provider.get("displayName", "Yahoo Finance")
            else:
                source = article.get("publisher") or "Yahoo Finance"

            # Published time
            pub_date = ""
            pub_raw = content.get("pubDate") or content.get("displayTime")
            if pub_raw and isinstance(pub_raw, str):
                pub_date = pub_raw[:16].replace("T", " ")
            elif article.get("providerPublishTime"):
                try:
                    pub_date = datetime.fromtimestamp(int(article["providerPublishTime"])).strftime("%Y-%m-%d %H:%M")
                except (TypeError, ValueError):
                    pub_date = ""

            summary = content.get("summary") or content.get("description") or None

            if title and url:
                items.append(NewsItem(
                    title=title,
                    source=source,
                    published_at=pub_date,
                    url=url,
                    summary=summary,
                ))

        if not items:
            raise ValueError(f"No usable news items for {sym}")

        return MarketNewsRead(symbol=sym, items=items, source_mode="live")
    except Exception as exc:
        logger.warning("News fallback for %s: %r", sym, exc)
        raw = mock_news(sym)
        items = [NewsItem(**i) for i in raw["items"]]
        return MarketNewsRead(symbol=sym, items=items, source_mode="mock")
