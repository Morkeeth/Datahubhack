#!/usr/bin/env bash
# Full Nullspace beat via real MCP requester sessions (not the offline for-loop).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

export DATAHUB_GMS_URL="${DATAHUB_GMS_URL:-http://localhost:8080}"
export NULLSPACE_STORE="${NULLSPACE_STORE:-/tmp/nullspace-ghosts.json}"
export NULLSPACE_DBT_REPO="${NULLSPACE_DBT_REPO:-$ROOT/dbt_project}"
export NULLSPACE_EVAL_WANT="${NULLSPACE_EVAL_WANT:-fresh-nullspace-$(date +%s)}"

# Wipe only the shared store the board also reads.
rm -f "$NULLSPACE_STORE"
python3 -m nullspace.cli reset 2>/dev/null || true

python3 scripts/eval_nullspace.py --cold
echo ""
echo "Open the board: http://localhost:8787"
echo "(start it with ./scripts/up.sh if it is not running)"
echo "NOTE: file:// means a local dbt change reference, not a pull request."
