# AlphaWatch 📈

A personal stock research terminal built with FastAPI, SQLite, JWT auth, and Streamlit.
Uses **Yahoo Finance** (via the `yfinance` library) for real-time market data — **no API key required**.

---

## Features

| | Feature |
|---|---|
| ✅ | SQLite persistence via SQLModel |
| ✅ | User registration, login, JWT auth |
| ✅ | Per-user stock isolation |
| ✅ | Admin role + admin-only route |
| ✅ | Full stock CRUD |
| ✅ | Company symbol auto-fill via yfinance |
| ✅ | Live quote, profile, history (30 days), news |
| ✅ | Automatic mock fallback if yfinance is unreachable |
| ✅ | Dashboard with metrics, charts, watchlist overview |
| ✅ | Stock Details page with full quote stats, price chart, news |

---

## Quick Start

### 1. Install

```bash
pip install -e ".[dev]"
```

### 2. Run the backend

```bash
uvicorn app.main:app --reload
```

API: `http://127.0.0.1:8000` · Docs: `http://127.0.0.1:8000/docs`

### 3. Run the frontend

```bash
streamlit run ui/streamlit_app.py
```

Opens at `http://localhost:8501`. Register an account on first visit.

**That's it — no API keys, no environment variables, no secrets.**

---

## Data source: Yahoo Finance

AlphaWatch uses the [`yfinance`](https://github.com/ranaroussi/yfinance) Python package, which is a free, unofficial Yahoo Finance API.

| | Value |
|---|---|
| Cost | Free |
| API key | Not required |
| Rate limit | Effectively unlimited for normal use |
| Real-time quotes | Yes (delayed ~15 min for most exchanges) |
| Historical data | Yes (years of daily data) |
| Company news | Yes |

If Yahoo Finance is temporarily unreachable, the app automatically falls back to realistic built-in mock data for AAPL, MSFT, NVDA, TSLA, AMZN, META, GOOGL, AMD, PLTR — and generic data for any other symbol.

---

## Pages

### Dashboard
- Total stocks, favorites, average score
- Top gainer / top loser from your watchlist (live)
- Sector allocation chart + score ranking chart
- Watchlist overview table with live prices

### Watchlist
- Each stock shows: price, daily change %, target price, personal score
- Expanded view: prev close, open, high, low, volume, thesis
- Edit and delete inline

### Add Stock
- Symbol lookup auto-fills company name and sector
- Duplicate symbol check
- Validation errors and success messages

### Stock Details
- Large price display with green/red movement
- Full quote stats grid (open, high, low, volume, prev close)
- Company profile with market cap, industry, country, website, description
- 30-day price chart
- Latest news cards with summaries
- Your personal notes: target price, score, thesis, favorite

---

## API endpoints

### Auth
```
POST /auth/register   { "email": "...", "password": "..." }
POST /auth/login      form-data: username=... password=...
GET  /auth/me
GET  /auth/admin/users   (admin only)
```

### Stocks (JWT required)
```
GET    /stocks
POST   /stocks
GET    /stocks/{id}
PUT    /stocks/{id}
DELETE /stocks/{id}
GET    /stocks/lookup/{symbol}
```

### Market (JWT required, always returns data)
```
GET /market/profile/{symbol}   → symbol, company_name, sector, industry, website, description, market_cap, country, source_mode
GET /market/quote/{symbol}     → price, change, change_percent, open, day_high, day_low, volume, previous_close, source_mode
GET /market/history/{symbol}   → interval, range, series[{timestamp, close}], source_mode
GET /market/news/{symbol}      → items[{title, source, published_at, url, summary}], source_mode
```

`source_mode` is `"live"` (Yahoo Finance) or `"mock"` (offline fallback).

---

## Tests

```bash
pytest
```

No network needed — all `yfinance` calls are mocked.

### Coverage
- Auth: register, login, protected routes, expired token, role enforcement
- Stock CRUD: all operations + user isolation
- Market profile: live shape, uppercase normalisation, fallback on yfinance failure, unknown symbol
- Market quote: live shape (all fields), fallback
- Market history: ascending series, 30-point mock, fallback on empty history
- Market news: live items, empty feed, fallback, symbol in titles

---

## Project structure

```
ALPHA_WATCH/
├── app/
│   ├── auth.py              # bcrypt, JWT, dependencies
│   ├── auth_routes.py       # /auth/*
│   ├── company_lookup.py    # yfinance-based lookup
│   ├── database.py          # SQLite engine + session
│   ├── main.py              # FastAPI app + lifespan
│   ├── market_routes.py     # /market/* — yfinance with auto-fallback
│   ├── mock_data.py         # symbol-aware demo data
│   ├── models.py            # SQLModel: User, Stock
│   ├── routes.py            # /stocks CRUD
│   └── schemas.py           # Pydantic schemas
├── tests/
│   ├── conftest.py
│   ├── test_auth.py
│   ├── test_market.py
│   └── test_stocks.py
├── ui/
│   └── streamlit_app.py     # Dashboard, Watchlist, Add Stock, Stock Details
├── .gitignore
├── pyproject.toml
└── README.md
```

---

## AI Assistance

Claude (Anthropic) was used for:
- Switching the data provider from Alpha Vantage → Finnhub → yfinance
- Designing the live/mock fallback architecture and `source_mode` field
- Streamlit dashboard layout, CSS theming, and card components
- Writing pytest coverage for both live and fallback code paths

All generated code was reviewed, understood, and adapted before committing.
