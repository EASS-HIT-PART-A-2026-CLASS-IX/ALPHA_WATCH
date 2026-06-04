# Compose Runbook

## What Compose Covers

`docker compose up` starts the EX3 infrastructure services:

- FastAPI API at `http://127.0.0.1:8000`
- Redis at `localhost:6379`
- background worker using the same SQLite data volume as the API

The Streamlit dashboard stays local by default:

```bash
uv run streamlit run ui/streamlit_app.py
```

## Launch The Stack

Install dependencies locally:

```bash
uv sync --extra dev
```

Start API, Redis, and worker:

```bash
docker compose up --build
```

Seed the compose SQLite volume from a second terminal:

```bash
docker compose exec api python scripts/seed.py
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

Open:

```text
http://127.0.0.1:8000/docs
```

Or run:

```bash
curl http://127.0.0.1:8000/docs
```

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

If no stocks exist yet, run `docker compose exec api python scripts/seed.py` or register through the dashboard and add stocks.

## Run The Streamlit Dashboard

In a second terminal:

```bash
uv run streamlit run ui/streamlit_app.py
```

Open:

```text
http://localhost:8501
```

Use the demo login if you ran `scripts/seed.py`:

```text
demo@alphawatch.local / password123
```

## Run Tests

```bash
uv run pytest
```

The tests mock Yahoo Finance and fake Redis where needed. They do not require real network calls.

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
