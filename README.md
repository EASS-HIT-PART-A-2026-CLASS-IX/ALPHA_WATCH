# AlphaWatch

AlphaWatch is a personal stock research dashboard built with FastAPI, SQLite, JWT auth, SQLModel, Streamlit, and Yahoo Finance.

The core product remains simple and local:

- register and log in
- keep a private stock watchlist
- add, edit, favorite, and delete stocks
- view live quote, profile, history, and news data
- continue working when Yahoo Finance is unavailable through mock fallback data

EX3 adds the missing local infrastructure layer without replacing the existing dashboard:

- `compose.yaml` for API, Redis, and worker
- Redis-backed refresh idempotency
- background worker for saved stock market refresh
- manual refresh script
- reproducible database seed script
- local demo script
- EX3 docs and compose runbook
- weekly markdown stock summary report enhancement

## Service Architecture

```text
Streamlit UI (local)
        |
        v
FastAPI API ---- SQLite
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
| yes | Mock fallback for offline or failed market calls |
| yes | Streamlit dashboard, watchlist, add stock, and stock details |
| yes | Redis-backed refresh idempotency |
| yes | Async worker with bounded concurrency and retries |
| yes | Manual refresh script |
| yes | Reproducible database seed script |
| yes | Weekly markdown report enhancement |

## Local Quick Start

Install dependencies:

```bash
uv sync --extra dev
```

Initialize a demo database:

```bash
uv run python scripts/seed.py
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

Demo login:

```text
demo@alphawatch.local / password123
```

## Compose Stack

The EX3 compose stack runs the infrastructure services:

- `api`: FastAPI backend
- `redis`: Redis 7 for refresh idempotency
- `worker`: background refresh worker

Start it:

```bash
docker compose up --build
```

Seed the compose database from another terminal:

```bash
docker compose exec api python scripts/seed.py
```

Stop it:

```bash
docker compose down
```

Streamlit is still run locally:

```bash
uv run streamlit run ui/streamlit_app.py
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
GET /market/history/{symbol}
GET /market/news/{symbol}
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

## Database Setup

AlphaWatch creates tables on startup through SQLModel metadata.

For reproducible demo data:

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
│   ├── refresh.py
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
