#!/usr/bin/env bash
# Idempotent dependency install for DataHub Agent Hackathon cloud builds.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

# Prefer Python 3.11 (DataHub CLI actively tested there)
if command -v python3.11 >/dev/null 2>&1; then
  PY=python3.11
else
  PY=python3
fi

# mcp>=2.0.0 requires Python >=3.10, and stock macOS still ships 3.9. Without this
# check, pip fails with a several-hundred-line resolver dump that never says which
# Python is needed, and the run limps on to print "Install complete".
if ! "$PY" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3,10) else 1)'; then
  echo "REFUSED: $PY is $("$PY" -c 'import sys;print(".".join(map(str,sys.version_info[:3])))'), and this project needs 3.10 or newer."
  echo "         mcp>=2.0.0 has no build for 3.9. Install Python 3.11 and re-run:"
  echo "           brew install python@3.11   # or use pyenv"
  exit 1
fi

echo "==> Python toolchain ($PY)"
"$PY" -m pip install --user --upgrade pip "setuptools<82" wheel

echo "==> DataHub CLI + Agent Context Kit"
"$PY" -m pip install --user --upgrade \
  "acryl-datahub" \
  "datahub-agent-context" \
  "mcp>=2.0.0" \
  "psycopg[binary]" \
  "httpx" \
  "pydantic" \
  "python-dotenv" \
  "rich" \
  "typer"

if [[ -f "$ROOT/requirements.txt" ]]; then
  echo "==> Project requirements.txt"
  "$PY" -m pip install --user -r "$ROOT/requirements.txt"
fi

echo "==> Nullspace itself (editable)"
# Without this, `python3 scripts/eval_nullspace.py` fails with
# "ModuleNotFoundError: No module named 'nullspace'": running a script by path puts
# scripts/ on sys.path, not the repository root. Every documented scripts/*.py
# command depends on this line.
"$PY" -m pip install --user -e "$ROOT"

if [[ -f "$ROOT/app/pyproject.toml" ]]; then
  echo "==> Join Treaty app (editable)"
  "$PY" -m pip install --user -e "$ROOT/app"
fi

echo "==> Warm npm cache for DataHub MCP server"
npx --yes @acryldata/mcp-server-datahub --help >/dev/null 2>&1 || true

echo "==> Verify"
export PATH="${HOME}/.local/bin:${HOME}/Library/Python/3.11/bin:${PATH}"
FAILED=0
datahub version >/dev/null 2>&1 || datahub --version >/dev/null 2>&1 || {
  echo "    FAIL: the datahub CLI is not on PATH after install."
  echo "          Add one of these to your shell profile and re-run:"
  echo "            export PATH=\"\$HOME/.local/bin:\$PATH\""
  echo "            export PATH=\"\$HOME/Library/Python/3.11/bin:\$PATH\""
  FAILED=1
}
"$PY" -c "import datahub_agent_context" 2>/dev/null || { echo "    FAIL: datahub-agent-context did not import."; FAILED=1; }
"$PY" -c "import nullspace" 2>/dev/null || { echo "    FAIL: nullspace did not import — the editable install above did not take."; FAILED=1; }

# A stranger who follows the README gets a ghost that goes "solid" — and until
# this was added, solid meant a tag in DataHub with no physical table anywhere,
# because nothing installed dbt and no profile existed. `information_schema`
# returned zero rows for the model the builder had just "shipped". A solid asset
# nobody can select from is the exact kind of claim this project refuses to make,
# so the tool that makes it true is part of the install, not a footnote.
echo "==> Install dbt (so a solid asset is a real table, not just metadata)"
# Pin dbt-core <2: unpinned `dbt-postgres` resolves Fusion (2.0 alpha) which
# has no Postgres adapter — solid then falls back to CTAS (D33). Strangers
# following the README must get a working `dbt run`, not a silent fallback.
"$PY" -m pip install --user "dbt-core>=1.8,<2" "dbt-postgres>=1.8,<1.10" || \
  echo "    WARNING: dbt-postgres did not install. A ghost can still go solid in" \
       "DataHub, but no physical table will exist. Do not trust 'solid' until" \
       "'dbt run' has succeeded."

if [ ! -f "${HOME}/.dbt/profiles.yml" ]; then
  echo "==> Write ~/.dbt/profiles.yml for the Compose warehouse"
  mkdir -p "${HOME}/.dbt"
  cat > "${HOME}/.dbt/profiles.yml" <<'PROFILE'
nullspace:
  target: dev
  outputs:
    dev:
      type: postgres
      host: localhost
      port: 5432
      user: agent
      password: agent
      dbname: warehouse
      schema: ecommerce
      threads: 4
PROFILE
else
  echo "==> ~/.dbt/profiles.yml already exists — leaving it alone"
fi

if [[ "$FAILED" -ne 0 ]]; then
  echo "==> Install INCOMPLETE — fix the FAIL lines above before following the README."
  exit 1
fi
echo "==> Install complete"
