#!/usr/bin/env bash
# Bring up DataHub quickstart (if needed) + Nullspace board.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

export DATAHUB_GMS_URL="${DATAHUB_GMS_URL:-http://localhost:8080}"
export NULLSPACE_STORE="${NULLSPACE_STORE:-/tmp/nullspace-ghosts.json}"

if [[ ! -d .venv ]]; then
  echo "Creating .venv with uv (Python 3.12)…"
  uv venv --python 3.12 .venv
  uv pip install -e ".[dev]"
fi
# shellcheck disable=SC1091
source .venv/bin/activate

if ! curl -sf "$DATAHUB_GMS_URL/health" >/dev/null 2>&1; then
  echo "Starting DataHub quickstart (first boot can take several minutes)…"
  datahub docker quickstart
else
  echo "DataHub already healthy at $DATAHUB_GMS_URL"
fi

echo "Starting Nullspace board on :8787 …"
exec uvicorn nullspace.board:app --host 0.0.0.0 --port 8787
