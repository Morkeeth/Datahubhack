#!/usr/bin/env bash
# Start local DataHub (Docker quickstart) and load showcase sample data.
# Judges cannot reach a private cloud instance — demos must work from this path.
set -euo pipefail

export PATH="${HOME}/.local/bin:${PATH}"

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker is required. Install Docker Desktop / Engine, then retry." >&2
  exit 1
fi

if ! docker info >/dev/null 2>&1; then
  echo "Docker daemon is not running. Start it, then retry." >&2
  if command -v sudo >/dev/null 2>&1; then
    echo "Trying: sudo service docker start"
    sudo service docker start || true
    sleep 2
  fi
  docker info >/dev/null 2>&1 || exit 1
fi

if ! command -v datahub >/dev/null 2>&1; then
  echo "Installing DataHub CLI..."
  python3 -m pip install --user --upgrade acryl-datahub
  export PATH="${HOME}/.local/bin:${PATH}"
fi

echo "==> Starting DataHub quickstart (this can take several minutes on first pull)"
datahub docker quickstart

echo "==> Configuring CLI for local instance"
datahub init --username datahub --password datahub || true

echo "==> Loading showcase-ecommerce sample datapack"
datahub datapack load showcase-ecommerce || {
  echo "Datapack load failed or unavailable — UI still works at http://localhost:9002"
  echo "Default login: datahub / datahub"
}

cat <<'EOF'

DataHub is ready for local demos:
  UI:  http://localhost:9002  (datahub / datahub)
  GMS: http://localhost:8080

Next:
  - Create a personal access token in the UI (Settings → Access Tokens)
  - export DATAHUB_GMS_URL=http://localhost:8080
  - export DATAHUB_GMS_TOKEN=<your-token>
  - npx -y @acryldata/mcp-server-datahub

Stop:   datahub docker quickstart --stop
Reset:  datahub docker nuke
EOF
