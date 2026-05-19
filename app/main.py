from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.auth_routes import router as auth_router
from app.database import init_db
from app.market_routes import router as market_router
from app.routes import router as stocks_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="AlphaWatch", lifespan=lifespan)

app.include_router(auth_router)
app.include_router(stocks_router)
app.include_router(market_router)
