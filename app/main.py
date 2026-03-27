from fastapi import FastAPI

from app.routes import router as stocks_router


app = FastAPI(title="AlphaWatch")
app.include_router(stocks_router)
