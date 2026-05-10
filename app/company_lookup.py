import os

import requests


ALPHA_VANTAGE_OVERVIEW_URL = "https://www.alphavantage.co/query"


class CompanyLookupConfigError(Exception):
    pass


class CompanyLookupNotFoundError(Exception):
    pass


class CompanyLookupServiceError(Exception):
    pass


def lookup_company_by_symbol(symbol: str) -> dict:
    clean_symbol = symbol.strip().upper()
    api_key = os.getenv("ALPHAVANTAGE_API_KEY")

    if not api_key:
        raise CompanyLookupConfigError("ALPHAVANTAGE_API_KEY is not configured")

    try:
        response = requests.get(
            ALPHA_VANTAGE_OVERVIEW_URL,
            params={
                "function": "OVERVIEW",
                "symbol": clean_symbol,
                "apikey": api_key,
            },
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as error:
        raise CompanyLookupServiceError("External lookup request failed") from error
    except ValueError as error:
        raise CompanyLookupServiceError("External lookup returned invalid JSON") from error

    company_name = data.get("Name")
    sector = data.get("Sector")

    if not company_name:
        raise CompanyLookupNotFoundError(f"Company not found for symbol {clean_symbol}")

    return {
        "symbol": data.get("Symbol", clean_symbol).upper(),
        "company_name": company_name,
        "sector": sector or "Unknown",
    }
