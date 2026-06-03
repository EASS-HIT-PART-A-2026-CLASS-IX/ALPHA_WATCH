# AlphaWatch 📈

A personal stock watchlist application built with FastAPI, SQLite, JWT authentication, and a Streamlit dashboard.

---

## What is implemented

| Feature | Status |
|---|---|
| SQLite persistence via SQLModel | ✅ |
| User registration + login | ✅ |
| Password hashing with bcrypt | ✅ |
| JWT Bearer token auth | ✅ |
| Per-user stock isolation | ✅ |
| Role field (`user` / `admin`) | ✅ |
| Admin-only route | ✅ |
| Full stock CRUD | ✅ |
| Company auto-fill via Alpha Vantage | ✅ |
| Real market profile / quote / history / news | ✅ |
| Built-in mock fallback when no API key | ✅ |
| Stock Details page in Streamlit | ✅ |

---

## Quick Start

### 1. Install dependencies

```bash
pip install -e ".[dev]"
# or with uv:
uv pip install -e ".[dev]"
```

### 2. Run the FastAPI backend

```bash
uvicorn app.main:app --reload
```

- API: `http://127.0.0.1:8000`
- Docs: `http://127.0.0.1:8000/docs`

### 3. Run the Streamlit frontend

```bash
streamlit run ui/streamlit_app.py
```

Opens at `http://localhost:8501`. Register an account on first visit.

---

## Live data vs demo data

AlphaWatch works fully out of the box — **no API key required**.

| Mode | When | How to tell |
|---|---|---|
| **Live** | `ALPHAVANTAGE_API_KEY` is set and the call succeeds | `source_mode: "live"` in API response |
| **Demo (mock)** | Key is missing or external call fails | `source_mode: "mock"` in API response; small info banner in the UI |

To enable live market data, get a free key at https://www.alphavantage.co/support/#api-key and run:

```bash
export ALPHAVANTAGE_API_KEY=your_key_here
export SECRET_KEY=a-long-random-string-here   # change in production
uvicorn app.main:app --reload
```

### What mock data looks like

When no API key is set, the backend returns realistic built-in data:

- **Profile**: full company description, sector, industry, market cap for AAPL, MSFT, NVDA, TSLA, AMZN, META, GOOGL — and generic data for any other symbol
- **Quote**: a deterministic price based on the symbol (same each day, looks stable)
- **History**: 30 days of a realistic random-walk price chart seeded by symbol
- **News**: 5 plausible recent headlines with the symbol in the title

The Stock Details page renders all sections normally and shows a small info banner:
> ℹ️ Showing demo market data. Set `ALPHAVANTAGE_API_KEY` to see live prices.

---

## Authentication flow

```
POST /auth/register   { "email": "...", "password": "..." }
POST /auth/login      form-data: username=... password=...
GET  /auth/me         Authorization: Bearer <jwt>
GET  /auth/admin/users   (admin role required)
```

---

## Stock CRUD

| Method | Path | Description |
|---|---|---|
| `GET` | `/stocks` | List your watchlist |
| `POST` | `/stocks` | Add a stock |
| `GET` | `/stocks/{id}` | Get a single stock |
| `PUT` | `/stocks/{id}` | Update a stock |
| `DELETE` | `/stocks/{id}` | Delete a stock |
| `GET` | `/stocks/lookup/{symbol}` | Auto-fill company info |

---

## Market data endpoints

All endpoints require a Bearer token. They always return data (live or mock).

| Path | Returns |
|---|---|
| `GET /market/profile/{symbol}` | symbol, company_name, sector, industry, description, market_cap, **source_mode** |
| `GET /market/quote/{symbol}` | price, change, change_percent, previous_close, **source_mode** |
| `GET /market/history/{symbol}` | 30-day daily close series (ascending), **source_mode** |
| `GET /market/news/{symbol}` | up to 10 news items, **source_mode** |

---

## Running tests

```bash
pytest
```

No API key or network access needed — all external calls are mocked.

### What is tested

- Auth: registration, login, protected routes, expired tokens, role checks
- Stock CRUD: create, read, update, delete, user isolation
- Market (live path): correct data returned when API responds
- Market (fallback path): mock data returned when key missing or API fails
- Mock data: symbol appears in headlines, prices are positive, series is ascending

---

## Project structure

```
ALPHA_WATCH/
├── app/
│   ├── auth.py              # bcrypt, JWT, dependency helpers
│   ├── auth_routes.py       # /auth/* endpoints
│   ├── company_lookup.py    # Alpha Vantage OVERVIEW wrapper
│   ├── database.py          # SQLite engine + session
│   ├── main.py              # FastAPI app + lifespan
│   ├── market_routes.py     # /market/* — live with mock fallback
│   ├── mock_data.py         # built-in demo data (no API key needed)
│   ├── models.py            # SQLModel: User, Stock
│   ├── routes.py            # /stocks CRUD
│   └── schemas.py           # Pydantic schemas (stock, auth, market)
├── tests/
│   ├── conftest.py
│   ├── test_auth.py
│   ├── test_stocks.py
│   └── test_market.py       # covers both live and mock fallback paths
├── ui/
│   └── streamlit_app.py
├── .gitignore
├── pyproject.toml
└── README.md
```

---

## AI Assistance

Claude (Anthropic) and GitHub Copilot were used during development for:

- Designing the live/mock fallback pattern and `source_mode` field
- Generating symbol-aware mock data for common tickers
- Writing pytest fixtures that cover both the live and fallback code paths

All generated code was reviewed, understood, and adapted before committing.
