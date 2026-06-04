from datetime import datetime, timezone
from typing import List, Optional

from sqlmodel import Field, Relationship, SQLModel


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True)
    hashed_password: str
    role: str = Field(default="user")  # "user" or "admin"

    stocks: List["Stock"] = Relationship(back_populates="owner")


class Stock(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    symbol: str = Field(index=True)
    company_name: str
    sector: str
    target_price: float
    personal_score: int
    thesis: str
    is_favorite: bool = Field(default=False)
    user_id: int = Field(foreign_key="user.id")

    owner: Optional["User"] = Relationship(back_populates="stocks")


class MarketSnapshot(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    symbol: str = Field(index=True)
    refreshed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), index=True)
    status: str = Field(default="ok")
    quote_source_mode: str = Field(default="mock")
    profile_source_mode: str = Field(default="mock")
    history_source_mode: str = Field(default="mock")
    news_source_mode: str = Field(default="mock")
    quote_json: str = Field(default="")
    profile_json: str = Field(default="")
    history_json: str = Field(default="")
    news_json: str = Field(default="")
    error: Optional[str] = None
