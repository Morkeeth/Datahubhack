#!/usr/bin/env bash
# Full Nullspace beat: 3 requester agents → demand=3 → claim → solid.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

export DATAHUB_GMS_URL="${DATAHUB_GMS_URL:-http://localhost:8080}"
export NULLSPACE_STORE="${NULLSPACE_STORE:-/tmp/nullspace-ghosts.json}"
export NULLSPACE_DBT_REPO="${NULLSPACE_DBT_REPO:-$ROOT/dbt_project}"

rm -f "$NULLSPACE_STORE"

python3 -m nullspace.cli demo
echo ""
echo "Open the board: http://localhost:8787"
echo "(start it with ./scripts/up.sh in another terminal if it is not running)"
echo "NOTE: file:// means a local dbt change reference, not a pull request."
