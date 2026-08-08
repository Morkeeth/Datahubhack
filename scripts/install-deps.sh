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

echo "==> Install complete"
