#!/usr/bin/env bash
# Print DataHub + MCP connectivity status for demos and agents.
set -euo pipefail

export PATH="${HOME}/.local/bin:${PATH}"

echo "Docker:     $(command -v docker >/dev/null && echo OK || echo MISSING)"
if command -v docker >/dev/null 2>&1; then
  if docker info >/dev/null 2>&1; then
    echo "Daemon:     running"
  else
    echo "Daemon:     not running"
  fi
fi

echo "datahub CLI:$(command -v datahub >/dev/null && datahub version 2>/dev/null | head -1 || echo ' MISSING')"
echo "GMS URL:    ${DATAHUB_GMS_URL:-unset}"
echo "GMS token:  ${DATAHUB_GMS_TOKEN:+set}${DATAHUB_GMS_TOKEN:-unset}"

if [[ -n "${DATAHUB_GMS_URL:-}" ]]; then
  code=$(curl -s -o /dev/null -w "%{http_code}" "${DATAHUB_GMS_URL}/health" || true)
  echo "GMS health: HTTP ${code}"
fi

echo "UI probe:   $(curl -s -o /dev/null -w "%{http_code}" http://localhost:9002/ 2>/dev/null || echo unreachable)"
