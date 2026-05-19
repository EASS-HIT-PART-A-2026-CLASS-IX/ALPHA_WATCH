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
