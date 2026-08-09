#!/usr/bin/env bash
# Full Nullspace beat via real MCP requester sessions (not the offline for-loop).
# Tomorrow's video: run this cold, then open the board — ghost≥3 → PR → solid.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

export DATAHUB_GMS_URL="${DATAHUB_GMS_URL:-http://localhost:8080}"
export NULLSPACE_STORE="${NULLSPACE_STORE:-/tmp/nullspace-ghosts.json}"
export NULLSPACE_DBT_REPO="${NULLSPACE_DBT_REPO:-$ROOT/dbt_project}"
export NULLSPACE_EVAL_WANT="${NULLSPACE_EVAL_WANT:-fresh-nullspace-$(date +%s)}"

echo "== Nullspace demo =="
echo "GMS:   $DATAHUB_GMS_URL"
echo "want:  $NULLSPACE_EVAL_WANT"
echo "store: $NULLSPACE_STORE (cache only; catalog is SoT)"
echo ""

# Wipe only the shared store the board also reads; GMS reset clears ghosts.
rm -f "$NULLSPACE_STORE"
python3 -m nullspace.cli reset 2>/dev/null || true

python3 scripts/eval_nullspace.py --cold
echo ""
echo "== After the beat =="
echo "Board:  http://localhost:8787"
echo "        (./scripts/up.sh if it is not running)"
echo "Review: python3 -m nullspace.builder --review-want \"$NULLSPACE_EVAL_WANT\""
echo "Merge→solid: python3 -m nullspace.webhook   # :8790, or cli finalize"
echo "Done when: board shows ghost demand≥3, then claimed/solid after builder."
echo "Honest boundary: file:// is a local change reference, not a GitHub PR."
