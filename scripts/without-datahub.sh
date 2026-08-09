#!/usr/bin/env bash
# Acceptance test (Law 2): without DataHub there is no Nullspace namespace.
#
# Asserts — and exits non-zero if any assertion silently succeeds:
#   1. three isolated agents each return status=refused
#   2. zero ghosts written to their local stores
#   3. the board reports the catalog unreachable (or this check FAILS loudly)
#
# Usage:
#   ./scripts/without-datahub.sh
# Fail-path probe (must exit 1):
#   NULLSPACE_WITHOUT_DH_EXPECT_FAIL=1 ./scripts/without-datahub.sh
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

DEAD_GMS="${NULLSPACE_DEAD_GMS:-http://127.0.0.1:9}"
WANT="${NULLSPACE_EVAL_WANT:-monthly recurring revenue by segment}"
BOARD_URL="${NULLSPACE_BOARD_URL:-http://localhost:8787/api/board}"
RUN_ID="$$"
STORE_A="/tmp/nullspace-isolated-a-${RUN_ID}.json"
STORE_B="/tmp/nullspace-isolated-b-${RUN_ID}.json"
STORE_C="/tmp/nullspace-isolated-c-${RUN_ID}.json"
trap 'rm -f "$STORE_A" "$STORE_B" "$STORE_C"' EXIT

echo "HOST: $(hostname)"
echo "GMS:  $DEAD_GMS  (intentionally unreachable)"
echo "WANT: $WANT"
echo ""

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
    if status in {"refused", "unreachable", "error"} or "unreachable" in err or "catalog" in err:
        board_ok = True
    if catalog is False or board.get("datahub_reachable") is False:
        board_ok = True
    # GraphQL board (Lane B): empty ghosts alone is NOT enough — must say why.
    if board.get("catalog_unreachable") is True:
        board_ok = True

if board_ok:
    print("PASS: board reports catalog unreachable")
else:
    print(f"FAIL: {board_reason} body={board_raw[:240]!r}", file=sys.stderr)
    failed = True

expect_fail = os.getenv("NULLSPACE_WITHOUT_DH_EXPECT_FAIL") == "1"
if expect_fail:
    if failed:
        print("\nEXPECT_FAIL: assertions failed as requested (exit 0 for probe).")
        sys.exit(0)
    print("\nEXPECT_FAIL: assertions unexpectedly passed.", file=sys.stderr)
    sys.exit(1)

if failed:
    print("\nwithout-datahub.sh FAILED — Law 2 not held on this host.", file=sys.stderr)
    sys.exit(1)

print("\nLaw 2: with DataHub gone, three agents refuse, zero ghosts, board unreachable.")
PY
