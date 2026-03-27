from fastapi import APIRouter, HTTPException, status

from app.repository import repository
from app.schemas import StockCreate, StockRead, StockUpdate


router = APIRouter(prefix="/stocks", tags=["stocks"])


@router.get("", response_model=list[StockRead])
def list_stocks() -> list[StockRead]:
    return repository.list()


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
