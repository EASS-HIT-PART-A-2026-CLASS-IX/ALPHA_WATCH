from fastapi import APIRouter, Depends

from app.auth import get_current_user
from app.models import User

router = APIRouter(prefix="/market", tags=["market"])

# These routes are stubs prepared for a future market-data integration phase.
# Each endpoint is authenticated so the integration slot is ready to use.


@router.get("/profile/{symbol}")
def get_market_profile(symbol: str, _user: User = Depends(get_current_user)) -> dict:
    # TODO: call a market-data provider (e.g. Alpha Vantage OVERVIEW)
    return {"symbol": symbol.upper(), "detail": "Market profile not yet implemented"}


@router.get("/quote/{symbol}")
def get_quote(symbol: str, _user: User = Depends(get_current_user)) -> dict:
    # TODO: call a real-time quote endpoint
    return {"symbol": symbol.upper(), "detail": "Live quote not yet implemented"}


@router.get("/history/{symbol}")
def get_history(symbol: str, _user: User = Depends(get_current_user)) -> dict:
    # TODO: call a historical price endpoint
    return {"symbol": symbol.upper(), "detail": "Price history not yet implemented"}


@router.get("/news/{symbol}")
def get_news(symbol: str, _user: User = Depends(get_current_user)) -> dict:
    # TODO: call a news/sentiment feed
    return {"symbol": symbol.upper(), "detail": "News feed not yet implemented"}
