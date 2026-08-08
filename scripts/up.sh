#!/usr/bin/env bash
# Bring up the repository DataHub stack + Nullspace board.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

export DATAHUB_GMS_URL="${DATAHUB_GMS_URL:-http://localhost:8080}"
export NULLSPACE_STORE="${NULLSPACE_STORE:-/tmp/nullspace-ghosts.json}"

if ! command -v docker >/dev/null 2>&1 || ! docker compose version >/dev/null 2>&1; then
  echo "REFUSED: Docker Compose v2 is unavailable; install/start Docker Desktop, then retry."
  exit 1
fi

if ! curl -sf "$DATAHUB_GMS_URL/health" >/dev/null 2>&1; then
  echo "Starting repository DataHub + disclosed demo warehouse…"
  docker compose up -d
  echo "Waiting for DataHub GMS…"
  for _ in $(seq 1 90); do
    curl -sf "$DATAHUB_GMS_URL/health" >/dev/null 2>&1 && break
    sleep 2
  done
  if ! curl -sf "$DATAHUB_GMS_URL/health" >/dev/null 2>&1; then
    echo "REFUSED: GMS did not become healthy after 180s; inspect 'docker compose ps'."
    exit 1
  fi
else
  echo "DataHub already healthy at $DATAHUB_GMS_URL"
fi

echo "Starting Nullspace board on :8787 …"
exec python3 -m uvicorn nullspace.board:app --host 0.0.0.0 --port 8787
