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
| Real market profile endpoint | ✅ |
| Real live quote endpoint | ✅ |
| Real price history endpoint | ✅ |
| Real news endpoint | ✅ |
| Stock Details page in Streamlit | ✅ |

---

## Quick Start

### 1. Install dependencies

```bash
pip install -e ".[dev]"
# or with uv:
uv pip install -e ".[dev]"
```

### 2. Configure API keys

Market data is powered by [Alpha Vantage](https://www.alphavantage.co/support/#api-key) (free tier, no credit card).

```bash
export ALPHAVANTAGE_API_KEY=your_key_here
export SECRET_KEY=a-long-random-string-here   # JWT secret — change in production
```

> Without `ALPHAVANTAGE_API_KEY`, stock CRUD and auth still work fully.
> Market data endpoints return a clear 503 with an explanatory message.

### 3. Run the FastAPI backend

```bash
uvicorn app.main:app --reload
```

- API: `http://127.0.0.1:8000`
- Interactive docs: `http://127.0.0.1:8000/docs`

The SQLite database (`alphawatch.db`) is created automatically on first run.

### 4. Run the Streamlit frontend

```bash
streamlit run ui/streamlit_app.py
```

Opens at `http://localhost:8501`. Register an account on first visit.

---

## Authentication flow

```
POST /auth/register   { "email": "...", "password": "..." }
  → 201 { "id": 1, "email": "...", "role": "user" }

POST /auth/login      form-data: username=... password=...
  → 200 { "access_token": "<jwt>", "token_type": "bearer" }

GET  /auth/me         Authorization: Bearer <jwt>
GET  /auth/admin/users   (admin role required → 403 otherwise)
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

All endpoints require a valid Bearer token and `ALPHAVANTAGE_API_KEY`.

| Path | Returns |
|---|---|
| `GET /market/profile/{symbol}` | symbol, company_name, sector, industry, description, market_cap |
| `GET /market/quote/{symbol}` | price, change, change_percent, previous_close |
| `GET /market/history/{symbol}` | 30-day daily close price series (ascending, ready to chart) |
| `GET /market/news/{symbol}` | up to 10 recent news items (title, source, published_at, url, summary) |

### Error responses

| Situation | HTTP status |
|---|---|
| `ALPHAVANTAGE_API_KEY` not set | 503 Service Unavailable |
| Symbol not found / no data | 404 Not Found |
| Alpha Vantage request failed | 502 Bad Gateway |

---

## Stock Details page

Click **🔍 Details** on any watchlist entry. The page shows:

- Your personal notes: target price, score, thesis, favorite status
- Live quote with price and daily change/percent
- Company profile: description, market cap, industry
- 30-day price chart (line chart, pandas + Streamlit)
- Latest news feed with clickable headlines

---

## Provider limitations (Alpha Vantage free tier)

| Limit | Value |
|---|---|
| Requests per day | 25 |
| Requests per minute | 5 |
| Quote freshness | ~15–20 min delayed |
| News | Recent articles only, no full-text |

Opening the Stock Details page makes up to 4 API calls (profile, quote, history, news).
With a free key and 25 calls/day, opening ~6 stock detail pages will exhaust the daily limit.
Upgrade to a paid Alpha Vantage key for production use.

---

## Running tests

```bash
pytest
```

All external API calls are mocked — no API key or network access required.

### What is tested

- Auth: registration, login, protected routes, expired tokens, role checks
- Stock CRUD: create, read, update, delete, isolation between users
- Market profile: success, 404 for unknown symbol, 503 for missing key, 401 without token
- Market quote: success, 404 for unknown symbol, 503 for missing key, 401 without token
- Market history: success, correct ascending order, 404, 503, 401
- Market news: success, empty feed, 503, 401

---

## Project structure

```
ALPHA_WATCH/
├── app/
│   ├── auth.py              # bcrypt hashing, JWT encode/decode, dependency helpers
│   ├── auth_routes.py       # /auth/register, /auth/login, /auth/me, /auth/admin/users
│   ├── company_lookup.py    # Alpha Vantage OVERVIEW — used by both /stocks/lookup and /market/profile
│   ├── database.py          # SQLite engine, get_session, init_db
│   ├── main.py              # FastAPI app + lifespan startup hook
│   ├── market_routes.py     # /market/profile, /quote, /history, /news — real integrations
│   ├── models.py            # SQLModel tables: User, Stock
│   ├── routes.py            # /stocks CRUD (per-user isolation)
│   └── schemas.py           # Pydantic v2 schemas: stock, auth, market
├── tests/
│   ├── conftest.py          # in-memory DB fixture + TestClient override
│   ├── test_auth.py
│   ├── test_stocks.py
│   └── test_market.py       # mocked tests for all 4 market endpoints
├── ui/
│   └── streamlit_app.py     # login/register + watchlist + stock details dashboard
├── .gitignore
├── pyproject.toml
└── README.md
```

---

## AI Assistance

Claude (Anthropic) and GitHub Copilot were used during development for:

- Drafting Alpha Vantage response parsing logic for quote, history, and news
- Structuring Pydantic response schemas for market data
- Generating mocked pytest fixtures for external API tests
- Streamlit layout and error handling for the Stock Details page

All generated code was reviewed, understood, and adapted before committing.
