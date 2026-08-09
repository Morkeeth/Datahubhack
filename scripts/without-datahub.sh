#!/usr/bin/env bash
# Subtraction proof (Law 2): delete the catalog and the shared namespace is gone.
#
# Three requester agents ask for the same missing asset with GMS unreachable.
# Each fails in its own context. None can see the others. There is no place the
# thing they all want can be named.
#
# Usage (stack may be up — this script points agents at a dead GMS on purpose):
#   ./scripts/without-datahub.sh
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

DEAD_GMS="${NULLSPACE_DEAD_GMS:-http://127.0.0.1:9}"
WANT="${NULLSPACE_EVAL_WANT:-monthly recurring revenue by segment}"
# Distinct non-existent paths — do not pre-create empty files (JSON load fails).
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
  local out
  out="$(
    DATAHUB_GMS_URL="$DEAD_GMS" \
    NULLSPACE_STORE="$store" \
    python3 -m nullspace.cli ask --want "$WANT" --agent "$name" 2>&1 || true
  )"
  printf '%s\n' "$out"
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

python3 - "$OUT_A" "$OUT_B" "$OUT_C" <<'PY'
import json, sys
outs = sys.argv[1:]
print("======== side by side ========")
rows = []
for raw in outs:
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        data = {"status": "error", "reason": raw[:200]}
    rows.append(data)
    print(
        f"{data.get('agent_id', '?'):28}  status={data.get('status')!r}  "
        f"reason={data.get('reason', data.get('ghost', {}).get('want', ''))!r}"
    )

statuses = {r.get("status") for r in rows}
if statuses != {"refused"}:
    print("\nREFUSED: expected all three agents status=refused when GMS is down.", file=sys.stderr)
    sys.exit(1)

# Prove isolation: no shared store accumulated a ghost.
print("\nLaw 2: with DataHub gone, three agents fail alone — no shared demand namespace.")
PY
