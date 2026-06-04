"""
company_lookup.py — yfinance-based company lookup, no API key required.
"""


class CompanyLookupConfigError(Exception):
    pass


class CompanyLookupNotFoundError(Exception):
    pass


class CompanyLookupServiceError(Exception):
    pass


def _yf_ticker(symbol: str):
    """Lazy-import yfinance so the rest of the app starts even if it's missing."""
    try:
        import yfinance as yf
    except ImportError as e:
        raise CompanyLookupConfigError("yfinance is not installed") from e
    return yf.Ticker(symbol)


def lookup_company_by_symbol(symbol: str) -> dict:
    """Returns symbol, company_name, sector — used by /stocks/lookup."""
    clean = symbol.strip().upper()
    try:
        ticker = _yf_ticker(clean)
        info = ticker.info or {}
    except CompanyLookupConfigError:
        raise
    except Exception as exc:
        raise CompanyLookupServiceError(f"Lookup request failed: {exc}") from exc

    name = info.get("longName") or info.get("shortName")
    if not name:
        raise CompanyLookupNotFoundError(f"Company not found for symbol '{clean}'")

    return {
        "symbol": clean,
        "company_name": name,
        "sector": info.get("sector") or "Unknown",
    }
