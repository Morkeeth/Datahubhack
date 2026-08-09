#!/usr/bin/env bash
# Bring up everything a human or a judge needs, and print the two links.
#
#   bash scripts/serve.sh            # local only: board + MCP on localhost
#   bash scripts/serve.sh --public   # also open Cloudflare tunnels and print public URLs
#
# Run this in a terminal you keep open. It runs in the foreground on purpose:
# the tunnels and the servers die when you Ctrl-C, and it is better that you can
# see that happen than that a link quietly stops working during a demo.
#
# What it starts:
#   :8787  the demand board and the order book, reading DataHub over GraphQL
#   :8788  the Nullspace MCP server, so any agent can create demand
#
# The public MCP endpoint runs with NULLSPACE_PUBLIC=1, which refuses
# claim_and_build — building writes a dbt model, pushes a branch and opens a pull
# request with this machine's GitHub credentials, and that is not a thing to hand
# a stranger. Demand is open to everyone; spending someone else's write access is
# not.
#
# LANE B (Claude).
set -uo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

PUBLIC=0
[[ "${1:-}" == "--public" ]] && PUBLIC=1

PY="${NULLSPACE_PYTHON:-$ROOT/.venv/bin/python}"
[[ -x "$PY" ]] || PY="$(command -v python3)"

export DATAHUB_GMS_URL="${DATAHUB_GMS_URL:-http://localhost:8080}"
export NULLSPACE_STORE="${NULLSPACE_STORE:-/tmp/nullspace-ghosts.json}"
export NULLSPACE_DBT_REPO="${NULLSPACE_DBT_REPO:-$ROOT/dbt_project}"
BOARD_PORT="${NULLSPACE_BOARD_PORT:-8787}"
MCP_PORT="${NULLSPACE_MCP_PORT:-8788}"

PIDS=()
cleanup() {
  echo ""
  echo "stopping…"
  for p in "${PIDS[@]:-}"; do [[ -n "$p" ]] && kill "$p" 2>/dev/null; done
  wait 2>/dev/null
  echo "stopped. the links above are dead now — that is the point, they were"
  echo "pointing at this machine."
}
trap cleanup EXIT INT TERM

# ---------------------------------------------------------------- preflight
if ! curl -sf -m 5 "$DATAHUB_GMS_URL/health" >/dev/null 2>&1; then
  echo "DataHub GMS is not answering at $DATAHUB_GMS_URL."
  echo "Start the stack first:  docker compose up -d   (then wait for"
  echo "metadata-ingestion to report 'Pipeline finished successfully')"
  echo ""
  echo "Refusing to start: the board reads DataHub and has no copy of its own,"
  echo "so without GMS it would come up saying the catalog is gone."
  exit 1
fi
echo "DataHub GMS  ok   $DATAHUB_GMS_URL"

# ---------------------------------------------------------------- the board
"$PY" -m uvicorn nullspace.board:app --host 127.0.0.1 --port "$BOARD_PORT" \
  >/tmp/nullspace-board.log 2>&1 &
PIDS+=($!)

# ---------------------------------------------------------------- tunnels
BOARD_URL="http://127.0.0.1:$BOARD_PORT"
MCP_URL="http://127.0.0.1:$MCP_PORT/mcp"
ALLOWED=""

if [[ $PUBLIC -eq 1 ]]; then
  command -v cloudflared >/dev/null || {
    echo "cloudflared not found. brew install cloudflared — or drop --public."; exit 1; }

  : >/tmp/nullspace-tunnel-board.log
  : >/tmp/nullspace-tunnel-mcp.log
  cloudflared tunnel --url "http://127.0.0.1:$BOARD_PORT" --no-autoupdate \
    >/tmp/nullspace-tunnel-board.log 2>&1 &
  PIDS+=($!)
  cloudflared tunnel --url "http://127.0.0.1:$MCP_PORT" --no-autoupdate \
    >/tmp/nullspace-tunnel-mcp.log 2>&1 &
  PIDS+=($!)

  echo -n "opening tunnels"
  for _ in $(seq 1 40); do
    B=$(grep -oE "https://[a-z0-9-]+\.trycloudflare\.com" /tmp/nullspace-tunnel-board.log | head -1)
    M=$(grep -oE "https://[a-z0-9-]+\.trycloudflare\.com" /tmp/nullspace-tunnel-mcp.log | head -1)
    [[ -n "$B" && -n "$M" ]] && break
    echo -n "."; sleep 1
  done
  echo ""
  if [[ -z "${B:-}" || -z "${M:-}" ]]; then
    echo "tunnels did not come up; continuing local-only."
    PUBLIC=0
  else
    BOARD_URL="$B"; MCP_URL="$M/mcp"
    # The MCP SDK refuses a Host header it does not recognise — DNS-rebinding
    # protection, and it is right to. Name the tunnel host rather than disable
    # the check. A quick tunnel mints a NEW hostname every run, which is why
    # this has to be read at start-up and cannot be baked into a config file.
    ALLOWED="${M#https://}"
  fi
fi

# ---------------------------------------------------------------- the MCP server
export NULLSPACE_MCP_TRANSPORT=streamable-http
export NULLSPACE_MCP_HOST=127.0.0.1
export NULLSPACE_MCP_PORT="$MCP_PORT"
[[ -n "$ALLOWED" ]] && export NULLSPACE_ALLOWED_HOSTS="$ALLOWED"
[[ $PUBLIC -eq 1 ]] && export NULLSPACE_PUBLIC=1

"$PY" -m nullspace.mcp_server >/tmp/nullspace-mcp.log 2>&1 &
PIDS+=($!)
sleep 4

# ---------------------------------------------------------------- report
ok() { curl -sf -m 8 -o /dev/null "$1" && echo "ok" || echo "NOT ANSWERING"; }
echo ""
echo "board        $(ok "$BOARD_URL/api/board")   $BOARD_URL"
echo "order book   $(ok "$BOARD_URL/api/order-book")   $BOARD_URL/order-book"
echo "mcp          $MCP_URL"
if [[ $PUBLIC -eq 1 ]]; then
  echo "             public instance — building is refused, demand is open"
fi
echo ""
echo "Point your own agent at it:"
echo ""
echo "  python scripts/remote_agent.py --url $MCP_URL \\"
echo "      --want \"customer health score by account\" \\"
echo "      --agent your-agent-name \\"
echo "      --query \"SELECT account_id, health_score FROM {}\""
echo ""
echo "Ctrl-C to stop everything."
wait
