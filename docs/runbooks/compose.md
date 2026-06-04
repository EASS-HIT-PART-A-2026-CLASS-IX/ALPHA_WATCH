# Compose Runbook

This runbook verifies the local EX3 stack: FastAPI API, Redis, worker, SQLite persistence, tests, Schemathesis, and the Streamlit dashboard.

## What Compose Covers

`docker compose up` starts:

- FastAPI API at `http://127.0.0.1:8000`
- Redis at `localhost:6379`
- one-shot seed service that initializes the demo account and sample watchlist
- background worker using the same SQLite volume as the API
- Streamlit UI at `http://localhost:8501`

## Fresh Clone Setup

Install dependencies:

```bash
uv sync --extra dev
```

Validate the local source tree:

```bash
uv run scripts/local_ci.sh
```

The local CI script runs Python syntax checks, pytest, compose config validation, and Schemathesis when an API is already running. If the API is not running, it skips Schemathesis and prints the exact command to run later.

## Launch The Stack

Start API, Redis, seed, worker, and UI:

```bash
docker compose up --build
```

The `seed` service runs automatically after the API is healthy. It exits successfully after creating the demo account and sample stocks. It is idempotent, so repeated compose starts do not duplicate data.

Open the app:

- Streamlit UI: `http://localhost:8501`
- API docs: `http://127.0.0.1:8000/docs`

Demo login:

```text
demo@alphawatch.local / password123
```

Stop the stack:

```bash
docker compose down
```

Remove the local compose database volume:

```bash
docker compose down -v
```

## Verify API Health

Check OpenAPI:

```bash
curl -fsS http://127.0.0.1:8000/openapi.json >/dev/null
```

Check docs in a browser:

```text
http://127.0.0.1:8000/docs
```

Show response headers:

```bash
curl -i http://127.0.0.1:8000/openapi.json | sed -n '1,20p'
```

AlphaWatch does not currently implement request rate limiting, so no `X-RateLimit-*` headers are expected. If rate limiting is added later, this header check is where those headers should be verified.

## Verify Redis

```bash
docker compose exec redis redis-cli ping
```

Expected output:

```text
PONG
```

## Verify Worker Behavior

Watch logs:

```bash
docker compose logs -f worker
```

You should see a cycle summary like:

```text
refresh cycle complete: symbols=3 refreshed=3 skipped=0 errors=0
```

If no stocks exist yet, run:

```bash
docker compose run --rm seed
```

You can also run one manual refresh and then watch the worker continue on its interval:

```bash
uv run python scripts/refresh.py AAPL MSFT --concurrency 2 --retries 2
```

## Verify Streamlit UI

Open:

```text
http://localhost:8501
```

Use the demo login after seeding:

```text
demo@alphawatch.local / password123
```

## Run Pytest

```bash
uv run pytest
```

The tests mock Yahoo Finance and fake Redis where needed. They do not require real market network calls.

## Run Schemathesis

Schemathesis is included in the `dev` dependencies. It checks the live OpenAPI schema against the running API.

Start the compose stack first:

```bash
docker compose up --build
```

Then run:

```bash
uv run scripts/schemathesis.sh
```

The script runs a small GET-focused Schemathesis smoke test against `http://127.0.0.1:8000/openapi.json` with an intentionally invalid bearer token. This keeps the check local and stable: protected routes should reject the request before Yahoo-backed endpoint logic runs, and Schemathesis verifies that those requests do not produce server errors.

## Local CI Equivalent

For a local CI-style check:

```bash
uv run scripts/local_ci.sh
```

Recommended full verification flow:

```bash
uv sync --extra dev
docker compose up --build
uv run scripts/local_ci.sh
```

In hosted CI, the equivalent steps would be:

```bash
uv sync --extra dev
uv run python -m compileall app scripts tests
uv run pytest
docker compose config
docker compose up -d --build
uv run scripts/schemathesis.sh
docker compose down
```

## Run Manual Refresh

Refresh all saved stocks:

```bash
uv run python scripts/refresh.py
```

Refresh selected symbols:

```bash
uv run python scripts/refresh.py AAPL MSFT --concurrency 2 --retries 2
```

When running against compose Redis from the host, the default `REDIS_URL=redis://localhost:6379/0` works.

## View The Weekly Report

Log in:

```bash
curl -X POST \
  -d "username=demo@alphawatch.local&password=password123" \
  http://127.0.0.1:8000/auth/login
```

Use the returned token:

```bash
curl -H "Authorization: Bearer TOKEN_HERE" \
  http://127.0.0.1:8000/reports/weekly
```
