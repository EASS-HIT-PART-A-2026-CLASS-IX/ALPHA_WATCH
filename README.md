# AlphaWatch 📈

A personal stock watchlist application built with FastAPI, SQLite, JWT authentication, and a Streamlit dashboard.

---

## What is implemented (EX3 Foundation)

| Feature | Status |
|---|---|
| SQLite persistence via SQLModel | ✅ |
| User registration + login | ✅ |
| Password hashing with bcrypt | ✅ |
| JWT Bearer token auth | ✅ |
| Per-user stock isolation | ✅ |
| Role field (`user` / `admin`) | ✅ |
| Admin-only route (`GET /auth/admin/users`) | ✅ |
| Full stock CRUD (create, read, update, delete) | ✅ |
| Company auto-fill via Alpha Vantage | ✅ (requires API key) |
| Market data stub endpoints | ✅ (stubs, not yet integrated) |
| Streamlit dashboard with login/register | ✅ |
| pytest suite (auth, CRUD, isolation, roles) | ✅ |

---

## Quick Start

### 1. Install dependencies

```bash
# recommended: uv
uv pip install -e ".[dev]"

# or plain pip
pip install -e ".[dev]"
```

> `email-validator` is included in the dependencies and is required for the
> registration endpoint to validate email addresses correctly.

### 2. Run the FastAPI backend

```bash
uvicorn app.main:app --reload
```

- API root: `http://127.0.0.1:8000`
- Interactive docs: `http://127.0.0.1:8000/docs`

The SQLite database file (`alphawatch.db`) is created automatically on first
run and is excluded from version control via `.gitignore`.

### 3. Run the Streamlit frontend

Open a second terminal:

```bash
streamlit run ui/streamlit_app.py
```

The UI opens at `http://localhost:8501`. Register a new account on first visit,
then log in to access your personal watchlist.

### 4. (Optional) Set environment variables

```bash
# Required for the company symbol auto-fill feature
export ALPHAVANTAGE_API_KEY=your_key_here

# Override the JWT signing secret in production (strongly recommended)
export SECRET_KEY=a-long-random-string-here
```

---

## Authentication flow

```
POST /auth/register   { "email": "...", "password": "..." }
  → 201 { "id": 1, "email": "...", "role": "user" }

POST /auth/login      form-data: username=... password=...
  → 200 { "access_token": "<jwt>", "token_type": "bearer" }

GET  /auth/me         Authorization: Bearer <jwt>
  → 200 { "id": 1, "email": "...", "role": "user" }

GET  /auth/admin/users   Authorization: Bearer <admin-jwt>
  → 200 [ ... ]   (403 if caller is not an admin)
```

All `/stocks` and `/market` endpoints require a valid Bearer token.

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

Each user can only see and modify their own stocks.

---

## Market data stubs (future phases)

These endpoints are authenticated and wired up — ready for real integrations:

| Path | Future purpose |
|---|---|
| `GET /market/profile/{symbol}` | Company overview |
| `GET /market/quote/{symbol}` | Live price quote |
| `GET /market/history/{symbol}` | Price history |
| `GET /market/news/{symbol}` | News / sentiment feed |

---

## Running tests

```bash
pytest
```

Tests use an isolated in-memory SQLite database — the `alphawatch.db` file is
never touched.

### What is tested

- Registration: success, duplicate email, short password
- Login: success, wrong password, unknown email
- Protected routes: no token, expired token, malformed token
- Admin route: regular user gets 403, admin gets 200
- `/auth/me` returns the current user
- Stock CRUD: create, read, update, delete, 404 cases
- User isolation: users cannot see or modify each other's stocks
- Two users can hold the same symbol without conflict
- Company lookup: mocked API response, missing API key → 503

---

## Project structure

```
ALPHA_WATCH/
├── app/
│   ├── auth.py           # password hashing, JWT encode/decode, dependency helpers
│   ├── auth_routes.py    # /auth/register, /auth/login, /auth/me, /auth/admin/users
│   ├── company_lookup.py # Alpha Vantage OVERVIEW wrapper
│   ├── database.py       # SQLite engine, get_session, init_db
│   ├── main.py           # FastAPI app + lifespan startup hook
│   ├── market_routes.py  # /market/* stub endpoints for future integration
│   ├── models.py         # SQLModel tables: User, Stock
│   ├── routes.py         # /stocks CRUD (per-user isolation)
│   └── schemas.py        # Pydantic v2 request/response schemas
├── tests/
│   ├── conftest.py       # in-memory DB fixture + TestClient override
│   ├── test_auth.py      # auth flow tests
│   └── test_stocks.py    # CRUD + isolation tests
├── ui/
│   └── streamlit_app.py  # login/register + personal watchlist dashboard
├── .gitignore
├── pyproject.toml
└── README.md
```

---

## AI Assistance

GitHub Copilot and Claude (Anthropic) were used during development for:

- Drafting boilerplate for SQLModel table definitions and Pydantic schemas
- Suggesting the `lifespan` pattern for FastAPI startup hooks
- Generating the pytest fixture structure for in-memory database isolation
- Reviewing bcrypt / JWT integration for common pitfalls

All generated code was reviewed, understood, and adapted before being committed.
