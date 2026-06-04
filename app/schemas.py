from typing import Annotated, Literal, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, StringConstraints

StockSymbol = Annotated[str, StringConstraints(strip_whitespace=True, to_upper=True, min_length=1, max_length=5)]
NonEmptyText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


# ── Stock schemas ─────────────────────────────────────────────────────────────

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


# ── Auth schemas ──────────────────────────────────────────────────────────────

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


# ── Market schemas ────────────────────────────────────────────────────────────
# source_mode tells the caller whether data came from a live API or mock fallback.

SourceMode = Literal["live", "mock"]


class MarketProfileRead(BaseModel):
    symbol: str
    company_name: str
    sector: str
    industry: str
    website: str = ""
    description: str
    market_cap: Optional[int] = None
    country: str = "United States"
    source_mode: SourceMode = "live"


class MarketQuoteRead(BaseModel):
    symbol: str
    price: float
    change: float
    change_percent: float
    previous_close: Optional[float] = None
    open: Optional[float] = None
    day_high: Optional[float] = None
    day_low: Optional[float] = None
    volume: Optional[int] = None
    source_mode: SourceMode = "live"


class HistoryPoint(BaseModel):
    timestamp: str
    close: float


class MarketHistoryRead(BaseModel):
    symbol: str
    interval: str = "1day"
    range: str = "1mo"
    series: list[HistoryPoint]
    source_mode: SourceMode = "live"


class NewsItem(BaseModel):
    title: str
    source: str
    published_at: str
    url: str
    summary: Optional[str] = None


class MarketNewsRead(BaseModel):
    symbol: str
    items: list[NewsItem]
    source_mode: SourceMode = "live"
