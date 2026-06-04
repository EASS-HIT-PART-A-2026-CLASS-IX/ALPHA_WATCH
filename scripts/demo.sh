#!/usr/bin/env bash
set -euo pipefail

cat <<'TEXT'
AlphaWatch EX3 local demo
=========================

1. Install dependencies:
   uv sync --extra dev

2. Start the EX3 infrastructure stack:
   docker compose up --build

3. In another terminal, seed the compose database:
   docker compose exec api python scripts/seed.py

4. Open the Streamlit dashboard:
   uv run streamlit run ui/streamlit_app.py

5. Log in with:
   demo@alphawatch.local / password123

6. Demo flow:
   - Open Dashboard and confirm the sample watchlist appears.
   - Open Watchlist and add or edit a stock.
   - Open Stock Details for AAPL, MSFT, or NVDA.
   - Confirm quote, profile, history, and news sections load.
   - Check the worker logs in the docker compose terminal.

7. Manual refresh and report:
   uv run python scripts/refresh.py AAPL MSFT --concurrency 2 --retries 2
   curl -X POST -d "username=demo@alphawatch.local&password=password123" http://127.0.0.1:8000/auth/login
   Use the returned token:
   curl -H "Authorization: Bearer TOKEN_HERE" http://127.0.0.1:8000/reports/weekly

8. Verify health:
   curl -fsS http://127.0.0.1:8000/openapi.json >/dev/null
   curl http://127.0.0.1:8000/docs
   docker compose exec redis redis-cli ping

9. Run verification:
   uv run pytest
   uv run scripts/schemathesis.sh
   uv run scripts/local_ci.sh

Stop the stack with:
   docker compose down
TEXT
