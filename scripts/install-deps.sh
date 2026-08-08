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
"$PY" -m pip install --user --upgrade pip setuptools wheel

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
  echo "==> Join Treaty app (editable — spine reference, not the submission)"
  "$PY" -m pip install --user -e "$ROOT/app"
fi

if [[ -f "$ROOT/pyproject.toml" ]]; then
  echo "==> Nullspace (editable — the submission)"
  "$PY" -m pip install --user -e "$ROOT[dev]"
fi

# Ensure user bin is on PATH for this shell and for strangers who source nothing
export PATH="${HOME}/.local/bin:${PATH}"
USER_BIN="${HOME}/.local/bin"
mkdir -p "$USER_BIN"
# Symlink datahub into a place the README can name if pip --user put it elsewhere
if ! command -v datahub >/dev/null 2>&1; then
  for candidate in \
    "${HOME}/.local/bin/datahub" \
    "${HOME}/Library/Python/3.12/bin/datahub" \
    "${HOME}/Library/Python/3.11/bin/datahub"; do
    if [[ -x "$candidate" ]]; then
      ln -sfn "$candidate" "${USER_BIN}/datahub"
      break
    fi
  done
fi

echo "==> Warm npm cache for DataHub MCP server"
npx --yes @acryldata/mcp-server-datahub --help >/dev/null 2>&1 || true

echo "==> Verify CLI"
datahub version || datahub --version || {
  echo "ERROR: datahub not on PATH after install. Add ${USER_BIN} to PATH and retry."
  exit 1
}
"$PY" -c "import datahub_agent_context; print('datahub-agent-context OK')"
"$PY" -c "import nullspace; print('nullspace', nullspace.__version__)"

echo "==> Install complete"
