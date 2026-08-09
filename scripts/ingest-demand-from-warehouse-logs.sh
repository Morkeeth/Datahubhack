#!/usr/bin/env bash
# Dump warehouse stderr (relation-does-not-exist errors) and ingest as demand.
#
#   ./scripts/ingest-demand-from-warehouse-logs.sh
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

LOG="${NULLSPACE_WAREHOUSE_LOG:-/tmp/nullspace-warehouse.log}"
RECIPE="${NULLSPACE_DEMAND_RECIPE:-/tmp/nullspace-demand-from-logs.yml}"

echo "HOST: $(hostname)"
echo "Dumping warehouse container logs → $LOG"
docker logs nullspace-warehouse-1 2>"$LOG" >/dev/null || docker compose logs warehouse 2>"$LOG" >/dev/null

cat >"$RECIPE" <<YAML
source:
  type: nullspace.ingestion.demand.NullspaceDemandSource
  config:
    postgres_log: $LOG
sink:
  type: datahub-rest
  config:
    server: ${DATAHUB_GMS_URL:-http://localhost:8080}
YAML

echo "Ingesting with $RECIPE"
datahub ingest -c "$RECIPE"
echo "Done. Board: http://localhost:8787"
