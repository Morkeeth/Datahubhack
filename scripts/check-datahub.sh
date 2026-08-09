#!/usr/bin/env bash
# Verify the Compose substrate, warehouse, ingestion, and live endpoints.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

docker info >/dev/null
docker compose config --quiet

gms_code="$(curl --silent --output /dev/null --write-out '%{http_code}' http://localhost:8080/health)"
ui_code="$(curl --silent --output /dev/null --write-out '%{http_code}' http://localhost:9002/)"
ingestion_id="$(docker compose ps --all --quiet metadata-ingestion)"
ingestion_exit="$(docker inspect --format '{{.State.ExitCode}}' "$ingestion_id")"
warehouse_rows="$(
  docker compose exec --no-TTY warehouse \
    psql --tuples-only --no-align -U agent -d warehouse \
    -c 'select count(*) from ecommerce.customers;'
)"

printf 'Docker:             running\n'
printf 'Compose config:      valid\n'
printf 'GMS health:          HTTP %s\n' "$gms_code"
printf 'UI probe:            HTTP %s\n' "$ui_code"
printf 'Warehouse customers: %s rows\n' "$warehouse_rows"
printf 'Metadata ingestion:  exit %s\n' "$ingestion_exit"

[[ "$gms_code" == "200" ]]
[[ "$ui_code" == "200" ]]
[[ "$warehouse_rows" == "3" ]]
[[ "$ingestion_exit" == "0" ]]
