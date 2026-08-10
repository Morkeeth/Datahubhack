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

if [[ -f "$ROOT/app/pyproject.toml" ]]; then
  echo "==> Join Treaty app (editable)"
  "$PY" -m pip install --user -e "$ROOT/app"
fi

echo "==> Warm npm cache for DataHub MCP server"
npx --yes @acryldata/mcp-server-datahub --help >/dev/null 2>&1 || true

echo "==> Verify CLI"
export PATH="${HOME}/.local/bin:${PATH}"
datahub version || datahub --version || true
"$PY" -c "import datahub_agent_context; print('datahub-agent-context OK')"

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

echo "==> Install complete"
