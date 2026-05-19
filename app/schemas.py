from typing import Annotated

from pydantic import BaseModel, ConfigDict, EmailStr, Field, StringConstraints

StockSymbol = Annotated[str, StringConstraints(strip_whitespace=True, to_upper=True, min_length=1, max_length=5)]
NonEmptyText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


# ── Stock schemas (unchanged from EX2) ──────────────────────────────────────

class StockCreate(BaseModel):
    symbol: StockSymbol
    company_name: NonEmptyText
    sector: NonEmptyText
    target_price: float = Field(gt=0)
    personal_score: int = Field(ge=1, le=10)
    thesis: NonEmptyText
    is_favorite: bool


class StockUpdate(BaseModel):
    symbol: StockSymbol
    company_name: NonEmptyText
    sector: NonEmptyText
    target_price: float = Field(gt=0)
    personal_score: int = Field(ge=1, le=10)
    thesis: NonEmptyText
    is_favorite: bool


class StockRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    symbol: str
    company_name: str
    sector: str
    target_price: float
    personal_score: int
    thesis: str
    is_favorite: bool


class CompanyLookupRead(BaseModel):
    symbol: str
    company_name: str
    sector: str


# ── Auth schemas ─────────────────────────────────────────────────────────────

class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    role: str


class Token(BaseModel):
    access_token: str
    token_type: str
