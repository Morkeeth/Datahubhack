#!/usr/bin/env bash
# Bring up the repository DataHub stack + Nullspace board.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

export DATAHUB_GMS_URL="${DATAHUB_GMS_URL:-http://localhost:8080}"
export NULLSPACE_STORE="${NULLSPACE_STORE:-/tmp/nullspace-ghosts.json}"
BOARD_PORT="${NULLSPACE_BOARD_PORT:-8787}"
BOARD_URL="http://localhost:${BOARD_PORT}"

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

# README promises warehouse at localhost:5432 — do not declare the stack ready
# when only GMS answers (redteam WEAPON 2: half-up warehouse).
if ! docker compose ps --status running --services 2>/dev/null | grep -qx warehouse; then
  echo "Warehouse not running; starting Compose services…"
  docker compose up -d
fi
echo "Waiting for warehouse on localhost:5432…"
warehouse_ok=0
for _ in $(seq 1 60); do
  if docker compose exec -T warehouse pg_isready -U agent -d warehouse >/dev/null 2>&1; then
    warehouse_ok=1
    break
  fi
  sleep 2
done
if [[ "$warehouse_ok" -ne 1 ]]; then
  echo "REFUSED: warehouse did not become ready on localhost:5432; inspect 'docker compose ps'."
  exit 1
fi
echo "Warehouse ready."

ingestion_id="$(docker compose ps -aq metadata-ingestion)"
if [[ -n "$ingestion_id" ]]; then
  echo "Waiting for disclosed warehouse metadata ingestion…"
  for _ in $(seq 1 90); do
    ingestion_status="$(docker inspect -f '{{.State.Status}} {{.State.ExitCode}}' "$ingestion_id")"
    [[ "$ingestion_status" == "exited 0" ]] && break
    if [[ "$ingestion_status" == exited* ]]; then
      echo "REFUSED: metadata ingestion returned $ingestion_status."
      exit 1
    fi
    sleep 2
  done
  ingestion_status="$(docker inspect -f '{{.State.Status}} {{.State.ExitCode}}' "$ingestion_id")"
  if [[ "$ingestion_status" != "exited 0" ]]; then
    echo "REFUSED: metadata ingestion did not finish after 180s."
    exit 1
  fi
  echo "Metadata ingestion finished successfully."
fi

if curl -sf "${BOARD_URL}/api/board" >/dev/null 2>&1; then
  echo "Nullspace board already healthy at ${BOARD_URL}"
else
  echo "Starting Nullspace board on :${BOARD_PORT} …"
  nohup python3 -m uvicorn nullspace.board:app \
    --host 0.0.0.0 --port "$BOARD_PORT" \
    >/tmp/nullspace-board.log 2>&1 &
  for _ in $(seq 1 20); do
    curl -sf "${BOARD_URL}/api/board" >/dev/null 2>&1 && break
    sleep 0.5
  done
  if ! curl -sf "${BOARD_URL}/api/board" >/dev/null 2>&1; then
    echo "REFUSED: board did not start; inspect /tmp/nullspace-board.log."
    exit 1
  fi
  echo "Nullspace board healthy at ${BOARD_URL}"
fi
