from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from app.auth import get_current_user
from app.company_lookup import (
    CompanyLookupConfigError,
    CompanyLookupNotFoundError,
    CompanyLookupServiceError,
    lookup_company_by_symbol,
)
from app.database import get_session
from app.models import Stock, User
from app.schemas import CompanyLookupRead, StockCreate, StockRead, StockUpdate

router = APIRouter(prefix="/stocks", tags=["stocks"])


@router.get("", response_model=list[StockRead])
def list_stocks(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> list[StockRead]:
    return session.exec(select(Stock).where(Stock.user_id == current_user.id)).all()


@router.get("/lookup/{symbol}", response_model=CompanyLookupRead)
def lookup_stock_company(
    symbol: str,
    _user: User = Depends(get_current_user),
) -> CompanyLookupRead:
    clean_symbol = symbol.strip().upper()
    if not clean_symbol:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Symbol is required")
    try:
        return lookup_company_by_symbol(clean_symbol)
    except CompanyLookupConfigError as error:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(error)) from error
    except CompanyLookupNotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
    except CompanyLookupServiceError as error:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(error)) from error


@router.get("/{stock_id}", response_model=StockRead)
def get_stock(
    stock_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> StockRead:
    stock = session.get(Stock, stock_id)
    if stock is None or stock.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stock not found")
    return stock


@router.post("", response_model=StockRead, status_code=status.HTTP_201_CREATED)
def create_stock(
    stock_data: StockCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> StockRead:
    duplicate = session.exec(
        select(Stock).where(Stock.user_id == current_user.id, Stock.symbol == stock_data.symbol.upper())
    ).first()
    if duplicate:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"{stock_data.symbol.upper()} is already in your watchlist",
        )
    stock = Stock(**stock_data.model_dump(), user_id=current_user.id)
    session.add(stock)
    session.commit()
    session.refresh(stock)
    return stock


@router.put("/{stock_id}", response_model=StockRead)
def update_stock(
    stock_id: int,
    stock_data: StockUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> StockRead:
    stock = session.get(Stock, stock_id)
    if stock is None or stock.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stock not found")
    for key, value in stock_data.model_dump().items():
        setattr(stock, key, value)
    session.add(stock)
    session.commit()
    session.refresh(stock)
    return stock


@router.delete("/{stock_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_stock(
    stock_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> None:
    stock = session.get(Stock, stock_id)
    if stock is None or stock.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stock not found")
    session.delete(stock)
    session.commit()
