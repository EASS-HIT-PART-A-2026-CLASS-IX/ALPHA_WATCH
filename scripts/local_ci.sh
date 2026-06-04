#!/usr/bin/env bash
set -euo pipefail

API_BASE_URL="${API_BASE_URL:-http://127.0.0.1:8000}"

echo "== Python syntax check =="
python -m compileall ai_service app scripts tests ui

echo
echo "== Pytest =="
pytest

echo
echo "== Compose config validation =="
docker compose config >/dev/null
echo "compose.yaml is valid"

echo
echo "== Schemathesis =="
if python - <<PY
import urllib.request
try:
    urllib.request.urlopen("${API_BASE_URL%/}/openapi.json", timeout=3).read()
except Exception:
    raise SystemExit(1)
PY
then
  scripts/schemathesis.sh
else
  echo "API is not running at ${API_BASE_URL}; skipping Schemathesis."
  echo "Start the API with docker compose or uvicorn, then run: scripts/schemathesis.sh"
fi

echo
echo "Local CI checks completed."
