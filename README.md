# AlphaWatch 📈

A personal stock watchlist application with a FastAPI backend, SQLite persistence, JWT authentication, and a Streamlit dashboard.

---

## What's in this phase (EX3)

- SQLite database via SQLModel (replaces in-memory storage)
- User registration and login
- Password hashing with bcrypt
- JWT-based authentication (Bearer token)
- Every stock belongs to a specific user — full data isolation
- Role field on users (`user` / `admin`) with a protected admin route
- Four market-data stub endpoints ready for future integration
- Full pytest suite: auth flows, CRUD, user isolation, role checks

---

## Quick Start

### 1. Install dependencies

```bash
# with uv (recommended)
uv pip install -e ".[dev]"

# or with pip
pip install -e ".[dev]"
```

### 2. Run the FastAPI backend

```bash
uvicorn app.main:app --reload
```

- API: `http://127.0.0.1:8000`
- Interactive docs: `http://127.0.0.1:8000/docs`

The SQLite database file (`alphawatch.db`) is created automatically on first run.

### 3. Run the Streamlit frontend

Open a second terminal:

```bash
streamlit run ui/streamlit_app.py
```

The app opens at `http://localhost:8501`. Register an account on first visit.

### 4. (Optional) Configure secrets and features

```bash
# Required for the company auto-fill feature
export ALPHAVANTAGE_API_KEY=your_key_here

# Override the JWT secret in production
export SECRET_KEY=a-long-random-string-here
```

---

## Project Structure

```
ALPHA_WATCH/
├── app/
│   ├── main.py            # FastAPI app entry point (lifespan → init_db)
│   ├── database.py        # SQLite engine, session dependency, init_db
│   ├── models.py          # SQLModel table models: User, Stock
│   ├── auth.py            # bcrypt hashing, JWT creation/validation, dependencies
│   ├── schemas.py         # Pydantic request/response schemas
│   ├── auth_routes.py     # /auth/register, /auth/login, /auth/me, /auth/admin/users
│   ├── routes.py          # /stocks CRUD (protected, per-user)
│   ├── market_routes.py   # /market stubs (profile, quote, history, news)
│   └── company_lookup.py  # Alpha Vantage integration (unchanged)
├── ui/
│   └── streamlit_app.py   # Streamlit multi-page frontend with auth gate
├── tests/
│   ├── conftest.py        # In-memory SQLite fixture, TestClient setup
│   ├── test_auth.py       # Registration, login, token, role tests
│   └── test_stocks.py     # CRUD + user isolation tests
├── pyproject.toml
└── README.md
```

---

## API Endpoints

### Auth

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `POST` | `/auth/register` | — | Create a new account |
| `POST` | `/auth/login` | — | Get a JWT token (form: username + password) |
| `GET` | `/auth/me` | ✓ | Current user info |
| `GET` | `/auth/admin/users` | admin | List all users |

### Stocks

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/stocks` | ✓ | List your stocks |
| `POST` | `/stocks` | ✓ | Add a stock |
| `GET` | `/stocks/{id}` | ✓ | Get one stock |
| `PUT` | `/stocks/{id}` | ✓ | Update a stock |
| `DELETE` | `/stocks/{id}` | ✓ | Delete a stock |
| `GET` | `/stocks/lookup/{symbol}` | ✓ | Auto-fill via Alpha Vantage |

### Market (stubs for next phase)

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/market/profile/{symbol}` | Company profile |
| `GET` | `/market/quote/{symbol}` | Live quote |
| `GET` | `/market/history/{symbol}` | Price history |
| `GET` | `/market/news/{symbol}` | News feed |

---

## Auth Flow

1. `POST /auth/register` with `{"email": "...", "password": "..."}` → creates account
2. `POST /auth/login` with form fields `username` + `password` → returns `access_token`
3. Pass the token as `Authorization: Bearer <token>` on every protected request
4. Token expires after 60 minutes (configurable via `ACCESS_TOKEN_EXPIRE_MINUTES`)

---

## Dashboard Pages

| Page | Description |
|------|-------------|
| **Login / Register** | Auth gate shown before access |
| **Dashboard** | Metrics, sector distribution chart, personal score chart |
| **Add Stock** | Form with optional Alpha Vantage auto-fill |
| **Watchlist** | Table with filter by sector/favorites, sort, delete |
| **Stock Details** | Detail view, charts, edit form |

---

## Running Tests

```bash
pytest tests/
```

Tests use an in-memory SQLite database — no file created, no cleanup needed.

---

## AI Assistance

This project was developed with assistance from Claude (Anthropic). AI was used for architecture decisions, code generation, and documentation. All generated outputs were reviewed, tested locally, and adapted for the project's requirements.
