# AlphaWatch

AlphaWatch is a personal stock research dashboard built with FastAPI, SQLite, JWT auth, SQLModel, Streamlit, and Yahoo Finance.

The core product remains simple and local:

- register and log in
- keep a private stock watchlist
- add, edit, favorite, and delete stocks
- view live quote, profile, history, and news data
- continue working when Yahoo Finance is unavailable through mock fallback data

EX3 adds the missing local infrastructure layer without replacing the existing dashboard:

- `compose.yaml` for API, Redis, worker, one-shot seed, and Streamlit UI
- Redis-backed refresh idempotency
- background worker for saved stock market refresh
- manual refresh script
- reproducible database seed script
- local demo script
- EX3 docs and compose runbook
- weekly markdown stock summary report enhancement
- Schemathesis/OpenAPI verification helper
- local CI-equivalent script

## Service Architecture

```text
Streamlit UI
   |       \
   v        v
AI Service  FastAPI API ---- SQLite
             |
             v
        Yahoo Finance with mock fallback

Worker ---- Redis idempotency
   |
   v
refresh snapshots in SQLite
```

## Features

| Status | Feature |
|---|---|
| yes | SQLite persistence via SQLModel |
| yes | User registration, login, JWT auth |
| yes | Per-user stock isolation |
| yes | Admin role and admin-only route |
| yes | Stock CRUD |
| yes | Company symbol lookup |
| yes | Yahoo Finance quote, profile, history, and news |
| yes | Stock Details chart range selector: 1D, 5D, 1M, YTD, 1Y |
| yes | Mock fallback for offline or failed market calls |
| yes | Streamlit dashboard, watchlist, add stock, and stock details |
| yes | AI sidecar microservice with deterministic stock briefs |
| yes | Redis-backed refresh idempotency |
| yes | Async worker with bounded concurrency and retries |
| yes | Manual refresh script |
| yes | Reproducible database seed script |
| yes | Weekly markdown report enhancement |

## Local Quick Start

For the grader/demo path, run one command:

```bash
docker compose up --build
```

Then open:

- Streamlit UI: `http://localhost:8501`
- API docs: `http://127.0.0.1:8000/docs`

The compose stack automatically runs the idempotent seed script on startup. Demo login:

```text
demo@alphawatch.local / password123
```

For local development without Docker, install dependencies:

```bash
uv sync --extra dev
```

Run the backend:

```bash
uv run uvicorn app.main:app --reload
```

Run the dashboard:

```bash
uv run streamlit run ui/streamlit_app.py
```

Open:

- API docs: `http://127.0.0.1:8000/docs`
- Streamlit: `http://localhost:8501`

Initialize local demo data when not using compose:

```bash
uv run python scripts/seed.py
```

## Compose Stack

The EX3 compose stack runs the full local app:

- `api`: FastAPI backend
- `redis`: Redis 7 for refresh idempotency
- `seed`: one-shot idempotent demo database setup
- `ai`: FastAPI AI sidecar at `http://localhost:8010`
- `worker`: background refresh worker
- `ui`: Streamlit frontend at `http://localhost:8501`

Start it:

```bash
docker compose up --build
```

The `seed` service runs `python scripts/seed.py` once after the API is healthy. It is safe to rerun because it does not duplicate the demo user or sample stocks.

Stop it:

```bash
docker compose down
```

See [docs/runbooks/compose.md](docs/runbooks/compose.md) for the full runbook.

## Redis And Worker

The worker runs independently from the API:

```bash
python -m app.worker
```

It refreshes saved stock symbols and stores market snapshots. Each symbol gets a Redis idempotency key such as:

```text
alphawatch:refresh:AAPL
```

That key prevents duplicate refresh work when the worker and manual script run at the same time. Keys expire automatically if a process exits unexpectedly.

## Manual Refresh

Refresh all saved symbols:

```bash
uv run python scripts/refresh.py
```

Refresh selected symbols:

```bash
uv run python scripts/refresh.py AAPL MSFT --concurrency 2 --retries 2
```

The script uses the same bounded concurrency, retry, Redis idempotency, Yahoo Finance, and mock fallback flow as the worker.

## Yahoo Finance And Mock Fallback

AlphaWatch uses `yfinance` for market data and requires no API key.

Every market endpoint returns a `source_mode` value:

- `live`: data came from Yahoo Finance
- `mock`: the fallback data was used

This keeps the product usable in class demos, offline testing, and temporary Yahoo Finance failures.

Stock history supports:

```text
GET /market/history/{symbol}?range=1d
GET /market/history/{symbol}?range=5d
GET /market/history/{symbol}?range=1mo
GET /market/history/{symbol}?range=ytd
GET /market/history/{symbol}?range=1y
```

The Stock Details page exposes these as 1D, 5D, 1M, YTD, and 1Y chart buttons.

## AI Service

AlphaWatch includes a small FastAPI AI sidecar:

```text
POST /ai/stock-brief
```

It receives stock context from the Streamlit server, including quote, profile, recent news, and the user's thesis. It returns:

- summary
- sentiment
- key takeaways
- key risks
- source_mode

The base demo requires no AI secrets. The service returns deterministic `mock` briefs for common symbols like AAPL, MSFT, NVDA, TSLA, AMZN, META, GOOGL, AMD, and PLTR, plus a useful generic brief for unknown symbols.

## EX3 Enhancement

The implemented enhancement is a weekly markdown stock summary report:

```text
GET /reports/weekly
```

It combines the logged-in user's watchlist with the latest background refresh snapshot. The report includes saved stocks, favorites, personal scores, target prices, thesis notes, latest price, daily move, source mode, and refresh time.

## API Endpoints

Auth:

```text
POST /auth/register
POST /auth/login
GET  /auth/me
GET  /auth/admin/users
```

Stocks:

```text
GET    /stocks
POST   /stocks
GET    /stocks/{id}
PUT    /stocks/{id}
DELETE /stocks/{id}
GET    /stocks/lookup/{symbol}
```

Market:

```text
GET /market/profile/{symbol}
GET /market/quote/{symbol}
GET /market/history/{symbol}?range=1mo
GET /market/news/{symbol}
```

AI sidecar:

```text
POST /ai/stock-brief
GET  /health
```

Reports:

```text
GET /reports/weekly
```

## Demo Script

Print the local demo walkthrough:

```bash
./scripts/demo.sh
```

The script guides a grader through setup, login, adding/viewing stocks, opening details, seeing market data, checking worker logs, and running the report.

## Schemathesis And Local CI

Run the local CI-equivalent checks:

```bash
uv run scripts/local_ci.sh
```

With the compose stack or local API running, run Schemathesis against the live OpenAPI schema:

```bash
uv run scripts/schemathesis.sh
```

The Schemathesis helper is a local GET smoke test with an intentionally invalid bearer token. It checks that protected OpenAPI routes do not produce server errors without triggering Yahoo Finance calls.

AlphaWatch does not currently expose rate-limit headers because it does not include rate-limit middleware. The compose runbook includes a response-header check and notes where those headers would be verified if rate limiting is added later.

## Database Setup

AlphaWatch creates tables on startup through SQLModel metadata.

For Docker Compose, the `seed` service runs automatically on startup.

For local development without Compose:

```bash
uv run python scripts/seed.py
```

The repository does not commit SQLite database artifacts. Database files are ignored by git.

## Tests

Run all tests:

```bash
uv run pytest
```

Tests cover:

- auth
- stock CRUD and user isolation
- market live/mock behavior
- Redis idempotency
- refresh retries and snapshot persistence
- weekly markdown report enhancement

Tests do not depend on real Yahoo Finance calls.

## Project Structure

```text
ALPHA_WATCH/
├── ai_service/
│   └── main.py
├── app/
│   ├── auth.py
│   ├── auth_routes.py
│   ├── database.py
│   ├── main.py
│   ├── market_routes.py
│   ├── models.py
│   ├── refresh.py
│   ├── redis_client.py
│   ├── reports.py
│   ├── routes.py
│   └── worker.py
├── docs/
│   ├── EX3-notes.md
│   └── runbooks/compose.md
├── scripts/
│   ├── demo.sh
│   ├── local_ci.sh
│   ├── refresh.py
│   ├── schemathesis.sh
│   └── seed.py
├── tests/
├── ui/
│   └── streamlit_app.py
├── compose.yaml
├── Dockerfile
├── pyproject.toml
└── README.md
```

## AI Assistance

AI assistance was used to implement and document the EX3 infrastructure layer: compose services, Redis idempotency, async refresh worker, manual refresh script, seed/demo scripts, tests, runbooks, and the weekly markdown report enhancement. The existing AlphaWatch product structure was preserved rather than rebuilt.
