#!/usr/bin/env bash
# Detached wrapper for the one-command Compose substrate.
# The canonical stranger path remains: docker compose up
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker is required. Install Docker Desktop / Engine, then retry." >&2
  exit 1
fi

if ! docker info >/dev/null 2>&1; then
  echo "Docker daemon is not running. Start it, then retry." >&2
  if command -v sudo >/dev/null 2>&1; then
    echo "Trying: sudo service docker start"
    sudo service docker start || true
    sleep 2
  fi
  docker info >/dev/null 2>&1 || exit 1
fi

echo "==> Starting DataHub, warehouse, and metadata ingestion"
docker compose up --detach

echo "==> Waiting for the metadata ingestion job"
ingestion_id="$(docker compose ps --quiet metadata-ingestion)"
while [[ -n "$ingestion_id" ]] && [[ "$(docker inspect --format '{{.State.Running}}' "$ingestion_id")" == "true" ]]; do
  sleep 2
done

ingestion_exit="$(docker inspect --format '{{.State.ExitCode}}' "$ingestion_id")"
if [[ "$ingestion_exit" != "0" ]]; then
  docker compose logs metadata-ingestion
  echo "Metadata ingestion failed with exit code ${ingestion_exit}" >&2
  exit "$ingestion_exit"
fi

cat <<'EOF'

DataHub is ready for local demos:
  UI:  http://localhost:9002  (datahub / datahub)
  GMS: http://localhost:8080
  DB:  postgresql://agent:agent@localhost:5432/warehouse

Verify:
  bash scripts/check-datahub.sh
  bash scripts/query-seeded-entity.sh

Stop:   docker compose down
Reset:  docker compose down --volumes
EOF
