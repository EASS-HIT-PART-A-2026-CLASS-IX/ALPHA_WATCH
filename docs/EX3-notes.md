# AlphaWatch EX3 Notes

## Architecture Overview

AlphaWatch remains the same stock dashboard product:

- FastAPI serves auth, watchlist CRUD, market data, and reports.
- SQLite stores users, stocks, and refresh snapshots.
- Streamlit remains the local dashboard UI.
- Yahoo Finance through `yfinance` is still the live data provider.
- Built-in mock data still keeps market endpoints usable when Yahoo Finance is slow or unreachable.

EX3 adds a small infrastructure layer around the existing product:

- `compose.yaml` starts API, Redis, seed, worker, and Streamlit UI.
- Redis coordinates refresh idempotency.
- `app.worker` refreshes saved stock data in the background.
- `scripts/refresh.py` lets a student or grader run the same refresh flow manually.
- `scripts/seed.py` initializes a fresh local database with a demo account and sample stocks, and Compose runs it automatically through the `seed` service.
- `scripts/local_ci.sh` gives a local CI-equivalent verification path.
- `scripts/schemathesis.sh` runs a small OpenAPI contract check against the live API.
- `/reports/weekly` is the documented EX3 enhancement.

## Services

### API

The `api` service runs:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

It initializes SQLite tables on startup and exposes the existing product endpoints plus the weekly report endpoint.

Health is verified through:

```bash
curl -fsS http://127.0.0.1:8000/openapi.json >/dev/null
```

### Seed

The `seed` service runs:

```bash
python scripts/seed.py
```

It waits until the API is healthy, shares the same SQLite volume, creates the demo account if needed, adds sample stocks only when missing, and exits successfully. This makes the grader flow one command:

```bash
docker compose up --build
```

### Redis

The `redis` service uses `redis:7-alpine`. AlphaWatch stores short-lived idempotency keys such as:

```text
alphawatch:refresh:AAPL
```

The key prevents the worker and manual script from refreshing the same symbol at the same time.

### Worker

The `worker` service runs:

```bash
python -m app.worker
```

Every `WORKER_REFRESH_INTERVAL_SECONDS` seconds, it loads distinct saved stock symbols from SQLite and refreshes:

- profile
- quote
- 30-day history
- news

Each successful refresh writes a `MarketSnapshot` row. Failed refreshes write an error snapshot so the failure is visible during local debugging.

### UI

The `ui` service runs:

```bash
streamlit run ui/streamlit_app.py --server.address=0.0.0.0 --server.port=8501 --server.headless=true
```

Inside Compose, Streamlit uses `API_BASE_URL=http://api:8000`. Outside Compose, it still defaults to `http://127.0.0.1:8000`.

## Auth And Security

AlphaWatch keeps its existing security model:

- users register with email and password
- passwords are hashed with bcrypt
- `/auth/login` issues a JWT
- protected routes require `Authorization: Bearer <token>`
- admin routes require role `admin`
- stocks remain isolated by `user_id`
- local secrets are read from environment variables
- SQLite database files and `.env` files are ignored by git

Local compose reads `SECRET_KEY` from the shell when provided and otherwise uses a local-only fallback:

```text
SECRET_KEY=${SECRET_KEY:-local-compose-secret-change-me-32-bytes}
```

This is intentionally simple for class/demo use. For a real local handoff, set a different value in a local `.env` file or shell environment and keep it out of git.

AlphaWatch does not currently expose rate-limit headers because no rate-limit middleware is installed. The runbook includes a header inspection command so this can be verified explicitly. If rate limiting is added later, expected `X-RateLimit-*` headers should be documented there.

## JWT Secret Rotation

For local rotation:

1. Stop the app:

   ```bash
   docker compose down
   ```

2. Change `SECRET_KEY` in `compose.yaml` or export it in your local shell.

3. Start again:

   ```bash
   docker compose up --build
   ```

4. Existing tokens become invalid. Users should log in again.

No password reset is required because password hashes are stored separately from JWT signing.

## Credentials Handling

- Do not commit `.env` files.
- Do not commit SQLite database files.
- Keep local secrets in shell variables or a local `.env` file ignored by git.
- For this project, Yahoo Finance needs no API key.

## Worker And Refresh Notes

The refresh implementation lives in `app/refresh.py` and is reused by:

- `python -m app.worker`
- `python scripts/refresh.py`
- tests

Refresh behavior:

- symbols are normalized to uppercase
- duplicate symbols are removed
- concurrency is bounded with `asyncio.Semaphore`
- blocking market calls run in worker threads
- each market section has retry support
- Redis idempotency prevents duplicate work
- results are stored in SQLite snapshots

The worker is intentionally local and small. It does not use a cloud queue, cron service, or hosted database.

## Redis Idempotency

Before refreshing a symbol, AlphaWatch attempts:

```text
SET alphawatch:refresh:AAPL running NX EX 300
```

If Redis returns false, another refresh owns the symbol and the job is skipped. When refresh completes, the key is deleted. If the process crashes, Redis automatically expires the key after the TTL.

## Example Trace

Example worker log excerpt:

```text
INFO:app.worker:AlphaWatch worker started; interval=300s
INFO:app.refresh:refreshed AAPL quote=live profile=live history=live news=mock
INFO:app.refresh:refreshed MSFT quote=mock profile=mock history=mock news=mock
INFO:app.worker:refresh cycle complete: symbols=2 refreshed=2 skipped=0 errors=0
```

## EX3 Enhancement

The enhancement is a weekly markdown stock summary report:

```text
GET /reports/weekly
```

It combines the authenticated user's saved watchlist with the latest background refresh snapshot and returns markdown suitable for local review or export.

Automated coverage lives in `tests/test_reports.py`.

## Verification

Core automated checks:

```bash
uv run pytest
```

Local CI-equivalent check:

```bash
uv run scripts/local_ci.sh
```

Schemathesis contract smoke check against a running API:

```bash
docker compose up --build
uv run scripts/schemathesis.sh
```

The Schemathesis helper intentionally uses an invalid bearer token for GET requests. That keeps the check deterministic and local by verifying protected routes reject unauthenticated traffic without reaching Yahoo Finance calls.
