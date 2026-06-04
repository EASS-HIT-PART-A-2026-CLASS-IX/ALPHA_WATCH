#!/usr/bin/env bash
set -euo pipefail

cat <<'TEXT'
AlphaWatch EX3 local demo
=========================

1. Install dependencies:
   uv sync --extra dev

2. Start the full EX3 app stack:
   docker compose up --build

   This starts:
   - FastAPI API on http://127.0.0.1:8000
   - Redis on localhost:6379
   - one-shot seed service for demo data
   - AI sidecar on http://127.0.0.1:8010
   - background worker
   - Streamlit UI on http://localhost:8501

3. Open the Streamlit dashboard:
   http://localhost:8501

4. Log in with:
   demo@alphawatch.local / password123

5. Demo flow:
   - Open Dashboard and confirm the sample watchlist appears.
   - Open Watchlist and add or edit a stock.
   - Open Stock Details for AAPL, MSFT, or NVDA.
   - Switch the price chart between 1D, 5D, 1M, YTD, and 1Y.
   - Review the AI Brief sentiment, takeaways, and risks.
   - Confirm quote, profile, history, and news sections load.
   - Check the worker logs in the docker compose terminal.

6. Manual refresh and report:
   uv run python scripts/refresh.py AAPL MSFT --concurrency 2 --retries 2
   curl -X POST -d "username=demo@alphawatch.local&password=password123" http://127.0.0.1:8000/auth/login
   Use the returned token:
   curl -H "Authorization: Bearer TOKEN_HERE" http://127.0.0.1:8000/reports/weekly

7. Verify health:
   curl -fsS http://127.0.0.1:8000/openapi.json >/dev/null
   curl -fsS http://127.0.0.1:8010/health
   curl http://127.0.0.1:8000/docs
   docker compose exec redis redis-cli ping

8. Run verification:
   uv run pytest
   uv run scripts/schemathesis.sh
   uv run scripts/local_ci.sh

Stop the stack with:
   docker compose down
TEXT
