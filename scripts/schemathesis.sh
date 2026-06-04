#!/usr/bin/env bash
set -euo pipefail

API_BASE_URL="${API_BASE_URL:-http://127.0.0.1:8000}"
MAX_EXAMPLES="${SCHEMATHESIS_MAX_EXAMPLES:-1}"

if ! command -v schemathesis >/dev/null 2>&1; then
  echo "schemathesis is not installed. Run: uv sync --extra dev"
  exit 1
fi

python - <<PY
import urllib.request

base_url = "${API_BASE_URL}".rstrip("/")
try:
    urllib.request.urlopen(f"{base_url}/openapi.json", timeout=5).read()
except Exception as exc:
    raise SystemExit(f"API is not reachable at {base_url}: {exc}")
PY

schemathesis run "${API_BASE_URL%/}/openapi.json" \
  --header "Authorization: Bearer invalid-local-contract-token" \
  --include-method GET \
  --checks not_a_server_error \
  --phases fuzzing \
  --max-examples "${MAX_EXAMPLES}" \
  --request-timeout 5 \
  --generation-database :memory:
