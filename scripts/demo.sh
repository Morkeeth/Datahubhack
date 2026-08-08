#!/usr/bin/env bash
# Full Nullspace beat: 3 consumers → ghost demand=3 → builder PR → solid.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

export DATAHUB_GMS_URL="${DATAHUB_GMS_URL:-http://localhost:8080}"
export NULLSPACE_STORE="${NULLSPACE_STORE:-/tmp/nullspace-ghosts.json}"
export NULLSPACE_DBT_REPO="${NULLSPACE_DBT_REPO:-$ROOT/dbt_project}"

rm -f "$NULLSPACE_STORE"

if [[ -f .venv/bin/activate ]]; then
  # shellcheck disable=SC1091
  source .venv/bin/activate
fi

python -m nullspace.cli demo
echo ""
echo "Open the board: http://localhost:8787"
echo "(start it with ./scripts/up.sh in another terminal if it is not running)"
