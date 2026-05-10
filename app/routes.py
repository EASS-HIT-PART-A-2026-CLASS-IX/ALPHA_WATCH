from fastapi import APIRouter, HTTPException, status

from app.company_lookup import (
    CompanyLookupConfigError,
    CompanyLookupNotFoundError,
    CompanyLookupServiceError,
    lookup_company_by_symbol,
)
from app.repository import repository
from app.schemas import CompanyLookupRead, StockCreate, StockRead, StockUpdate


router = APIRouter(prefix="/stocks", tags=["stocks"])


@router.get("", response_model=list[StockRead])
def list_stocks() -> list[StockRead]:
    return repository.list()


@router.get("/lookup/{symbol}", response_model=CompanyLookupRead)
def lookup_stock_company(symbol: str) -> CompanyLookupRead:
    clean_symbol = symbol.strip().upper()

    if not clean_symbol:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Symbol is required",
        )

    try:
        return lookup_company_by_symbol(clean_symbol)
    except CompanyLookupConfigError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(error),
        ) from error
    except CompanyLookupNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error
    except CompanyLookupServiceError as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(error),
        ) from error


@router.get("/{stock_id}", response_model=StockRead)
def get_stock(stock_id: int) -> StockRead:
    stock = repository.get(stock_id)
    if stock is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stock not found")
    return stock


@router.post("", response_model=StockRead, status_code=status.HTTP_201_CREATED)
def create_stock(stock_data: StockCreate) -> StockRead:
    return repository.create(stock_data)


@router.put("/{stock_id}", response_model=StockRead)
def update_stock(stock_id: int, stock_data: StockUpdate) -> StockRead:
    updated_stock = repository.update(stock_id, stock_data)
    if updated_stock is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stock not found")
    return updated_stock


@router.delete("/{stock_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_stock(stock_id: int) -> None:
    deleted = repository.delete(stock_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stock not found")
