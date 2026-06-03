import os

import requests

ALPHA_VANTAGE_BASE_URL = "https://www.alphavantage.co/query"


class CompanyLookupConfigError(Exception):
    pass


class CompanyLookupNotFoundError(Exception):
    pass


class CompanyLookupServiceError(Exception):
    pass


def _get_api_key() -> str:
    key = os.getenv("ALPHAVANTAGE_API_KEY")
    if not key:
        raise CompanyLookupConfigError("ALPHAVANTAGE_API_KEY is not configured")
    return key


def _av_get(params: dict) -> dict:
    """Make a GET request to Alpha Vantage and return parsed JSON."""
    try:
        response = requests.get(ALPHA_VANTAGE_BASE_URL, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as error:
        raise CompanyLookupServiceError("External request failed") from error
    except ValueError as error:
        raise CompanyLookupServiceError("External API returned invalid JSON") from error


def lookup_company_by_symbol(symbol: str) -> dict:
    """Used by /stocks/lookup — returns symbol, company_name, sector only."""
    clean = symbol.strip().upper()
    data = _av_get({"function": "OVERVIEW", "symbol": clean, "apikey": _get_api_key()})

    company_name = data.get("Name")
    if not company_name:
        raise CompanyLookupNotFoundError(f"Company not found for symbol '{clean}'")

    return {
        "symbol": data.get("Symbol", clean).upper(),
        "company_name": company_name,
        "sector": data.get("Sector") or "Unknown",
    }


def fetch_company_overview(symbol: str) -> dict:
    """Used by /market/profile — returns the full richer profile."""
    clean = symbol.strip().upper()
    data = _av_get({"function": "OVERVIEW", "symbol": clean, "apikey": _get_api_key()})

    company_name = data.get("Name")
    if not company_name:
        raise CompanyLookupNotFoundError(f"Company not found for symbol '{clean}'")

    raw_cap = data.get("MarketCapitalization")
    market_cap = int(raw_cap) if raw_cap and raw_cap.isdigit() else None

    return {
        "symbol": data.get("Symbol", clean).upper(),
        "company_name": company_name,
        "sector": data.get("Sector") or "Unknown",
        "industry": data.get("Industry") or "Unknown",
        "description": data.get("Description") or "",
        "market_cap": market_cap,
    }
