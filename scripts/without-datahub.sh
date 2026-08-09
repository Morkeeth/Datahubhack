#!/usr/bin/env bash
# Acceptance test (Law 2): without DataHub there is no Nullspace namespace.
#
# Asserts — and exits non-zero if any assertion silently succeeds:
#   1. three isolated agents each return status=refused
#   2. zero ghosts written to their local stores
#   3. the board reports catalog unreachable (GraphQL board against dead GMS)
#
# Usage:
#   ./scripts/without-datahub.sh
# Prove it can fail:
#   NULLSPACE_DEAD_GMS=http://localhost:8080 ./scripts/without-datahub.sh; echo $?
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

DEAD_GMS="${NULLSPACE_DEAD_GMS:-http://127.0.0.1:9}"
WANT="${NULLSPACE_EVAL_WANT:-monthly recurring revenue by segment}"
BOARD_PORT="${NULLSPACE_WITHOUT_DH_BOARD_PORT:-8799}"
BOARD_URL="${NULLSPACE_BOARD_URL:-http://127.0.0.1:${BOARD_PORT}/api/board}"
RUN_ID="$$"
STORE_A="/tmp/nullspace-isolated-a-${RUN_ID}.json"
STORE_B="/tmp/nullspace-isolated-b-${RUN_ID}.json"
STORE_C="/tmp/nullspace-isolated-c-${RUN_ID}.json"
BOARD_LOG="/tmp/nullspace-without-dh-board-${RUN_ID}.log"
BOARD_PID=""

cleanup() {
  if [[ -n "$BOARD_PID" ]] && kill -0 "$BOARD_PID" 2>/dev/null; then
    kill "$BOARD_PID" 2>/dev/null || true
    wait "$BOARD_PID" 2>/dev/null || true
  fi
  rm -f "$STORE_A" "$STORE_B" "$STORE_C"
}
trap cleanup EXIT

echo "HOST: $(hostname)"
echo "GMS:  $DEAD_GMS  (intentionally unreachable for agents + board)"
echo "WANT: $WANT"
echo "BOARD:$BOARD_URL"
echo ""

# Ephemeral board pointed at the same dead GMS — proves Law 2 on the judged URL shape.
DATAHUB_GMS_URL="$DEAD_GMS" \
  python3 -m uvicorn nullspace.board:app --host 127.0.0.1 --port "$BOARD_PORT" \
  >"$BOARD_LOG" 2>&1 &
BOARD_PID=$!
for _ in $(seq 1 30); do
  if curl -sf --max-time 1 "$BOARD_URL" >/dev/null 2>&1; then
    break
  fi
  sleep 0.2
done

run_agent() {
  local name="$1"
  local store="$2"
  DATAHUB_GMS_URL="$DEAD_GMS" \
  NULLSPACE_STORE="$store" \
  python3 -m nullspace.cli ask --want "$WANT" --agent "$name" 2>&1 || true
}

echo "======== agent A (isolated store) ========"
OUT_A="$(run_agent "revenue-copilot-1.0.0" "$STORE_A")"
echo "$OUT_A"
echo ""
echo "======== agent B (isolated store) ========"
OUT_B="$(run_agent "finance-agent-2.3.1" "$STORE_B")"
echo "$OUT_B"
echo ""
echo "======== agent C (isolated store) ========"
OUT_C="$(run_agent "board-deck-writer-0.9.0" "$STORE_C")"
echo "$OUT_C"
echo ""

BOARD_BODY="$(curl -sS --max-time 3 "$BOARD_URL" 2>&1 || true)"
echo "======== board ($BOARD_URL) ========"
echo "$BOARD_BODY"
echo ""

python3 - "$OUT_A" "$OUT_B" "$OUT_C" "$STORE_A" "$STORE_B" "$STORE_C" "$BOARD_BODY" <<'PY'
import json, os, sys

outs = sys.argv[1:4]
stores = sys.argv[4:7]
board_raw = sys.argv[7]
failed = False

print("======== assertions ========")
rows = []
for raw in outs:
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        data = {"status": "error", "reason": raw[:200]}
    rows.append(data)
    print(
        f"  agent {data.get('agent_id', '?'):28} status={data.get('status')!r}"
    )

statuses = {r.get("status") for r in rows}
if statuses != {"refused"}:
    print("FAIL: expected all three agents status=refused", file=sys.stderr)
    failed = True
else:
    print("PASS: three refusals")

for path in stores:
    if not os.path.exists(path):
        print(f"PASS: no store file written at {path}")
        continue
    try:
        payload = json.loads(open(path, encoding="utf-8").read() or "{}")
    except json.JSONDecodeError:
        print(f"FAIL: unreadable store {path}", file=sys.stderr)
        failed = True
        continue
    ghosts = payload.get("ghosts") or []
    if ghosts:
        print(f"FAIL: {len(ghosts)} ghost(s) written to {path}", file=sys.stderr)
        failed = True
    else:
        print(f"PASS: zero ghosts in {path}")

board_ok = False
board_reason = "board did not report catalog unreachable"
try:
    board = json.loads(board_raw)
except json.JSONDecodeError:
    board = None
    board_reason = f"board non-JSON: {board_raw[:160]!r}"

if isinstance(board, dict):
    status = str(board.get("status") or "").lower()
    err = str(board.get("error") or board.get("reason") or "").lower()
    catalog = board.get("catalog")
    if catalog in {"unreachable", "error"}:
        board_ok = True
    if status in {"refused", "unreachable", "error"} or "unreachable" in err:
        board_ok = True
    if catalog is False or board.get("datahub_reachable") is False:
        board_ok = True
    if board.get("catalog_unreachable") is True:
        board_ok = True
    # Empty ghosts alone is NOT enough — must name the catalog failure.
    if board_ok and catalog == "live":
        board_ok = False
        board_reason = "board catalog is live while agents aimed at dead GMS"

if board_ok:
    print("PASS: board reports catalog unreachable")
else:
    print(f"FAIL: {board_reason} body={board_raw[:240]!r}", file=sys.stderr)
    failed = True

if failed:
    print("\nwithout-datahub.sh FAILED — Law 2 not held on this host.", file=sys.stderr)
    sys.exit(1)

print("\nLaw 2: with DataHub gone, three agents refuse, zero ghosts, board unreachable.")
PY
