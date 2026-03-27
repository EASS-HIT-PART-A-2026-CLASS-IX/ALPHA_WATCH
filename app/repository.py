from app.schemas import StockCreate, StockRead, StockUpdate


class StockRepository:
    def __init__(self) -> None:
        self._stocks: dict[int, StockRead] = {}
        self._next_id = 1

    def list(self) -> list[StockRead]:
        return list(self._stocks.values())

    def get(self, stock_id: int) -> StockRead | None:
        return self._stocks.get(stock_id)

    def create(self, stock_data: StockCreate) -> StockRead:
        stock = StockRead(id=self._next_id, **stock_data.model_dump())
        self._stocks[self._next_id] = stock
        self._next_id += 1
        return stock

    def update(self, stock_id: int, stock_data: StockUpdate) -> StockRead | None:
        if stock_id not in self._stocks:
            return None

        updated_stock = StockRead(id=stock_id, **stock_data.model_dump())
        self._stocks[stock_id] = updated_stock
        return updated_stock

    def delete(self, stock_id: int) -> bool:
        if stock_id not in self._stocks:
            return False

        del self._stocks[stock_id]
        return True

    def reset(self) -> None:
        self._stocks.clear()
        self._next_id = 1


repository = StockRepository()
