#!/usr/bin/env bash
# Build the download package a judge or a reader gets handed.
#
# Everything in it is either copied from the repo or read live from the running
# stack at the moment you run this. Nothing is transcribed by hand, because a
# number typed twice is a number that drifts — and this project's whole argument
# is that claims should be read back rather than remembered.
#
#   bash scripts/package.sh
#
# Writes dist/nullspace-submission/ and a zip beside it.
set -uo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
OUT="dist/nullspace-submission"
rm -rf "$OUT"; mkdir -p "$OUT/screenshots"

PY="${NULLSPACE_PYTHON:-$ROOT/.venv/bin/python}"
[[ -x "$PY" ]] || PY="$(command -v python3)"
GMS="${DATAHUB_GMS_URL:-http://localhost:8080}"
BOARD="${NULLSPACE_BOARD:-http://127.0.0.1:8790}"

cp docs/submission/SUBMISSION.md "$OUT/"
cp docs/submission/pitch.md      "$OUT/" 2>/dev/null || true
cp README.md LICENSE             "$OUT/" 2>/dev/null || true

echo "==> receipts (read live, not transcribed)"
if curl -sf -m 10 "$BOARD/api/order-book" -o "$OUT/order-book.json"; then
  "$PY" - "$OUT" <<'PY'
import json, subprocess, sys, datetime
out = sys.argv[1]
d = json.load(open(f"{out}/order-book.json"))
t = d.get("totals", {})
def sh(cmd):
    try: return subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=60).stdout.strip()
    except Exception as e: return f"(unavailable: {e})"
receipts = {
  "generated_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
  "figures": {
    "unfilled_wants":  {"value": t.get("open_orders"),        "source": "GET /api/order-book -> totals.open_orders"},
    "agents_blocked":  {"value": t.get("blocked_agents"),     "source": "GET /api/order-book -> totals.blocked_agents"},
    "built":           {"value": t.get("filled"),             "source": "GET /api/order-book -> totals.filled"},
    "requests_unblocked": {"value": t.get("requests_unblocked"), "source": "GET /api/order-book -> totals.requests_unblocked"},
  },
  "tests": sh("cd '%s' && python -m pytest nullspace/tests -q 2>&1 | tail -1" % out.rsplit('/dist',1)[0]),
  "note": "Requester identities and warehouse rows are disclosed demo traffic. "
          "The misses behind them are genuine Postgres 'relation does not exist' errors.",
}
json.dump(receipts, open(f"{out}/receipts.json","w"), indent=2)
print("   receipts.json written")
PY
else
  echo "   board not answering at $BOARD — receipts skipped."
  echo "   Start it first: python -m uvicorn nullspace.board:app --port 8790"
fi

echo "==> screenshots"
if command -v python3 >/dev/null && python3 -c "import playwright" 2>/dev/null; then
  python3 - "$OUT" "$BOARD" <<'PY'
import sys
from playwright.sync_api import sync_playwright
out, board = sys.argv[1], sys.argv[2]
shots = [("board", "/", 1440), ("order-book", "/order-book", 1440),
         ("board-mobile", "/", 390), ("order-book-mobile", "/order-book", 390)]
with sync_playwright() as p:
    b = p.chromium.launch()
    for name, path, w in shots:
        pg = b.new_page(viewport={"width": w, "height": 1000}, device_scale_factor=2)
        pg.goto(board + path, wait_until="domcontentloaded"); pg.wait_for_timeout(4000)
        pg.screenshot(path=f"{out}/screenshots/{name}.png", full_page=True)
        print("  ", name)
    b.close()
PY
else
  echo "   playwright not installed — screenshots skipped (pip install playwright)"
fi

( cd dist && zip -qr nullspace-submission.zip nullspace-submission ) 2>/dev/null \
  && echo "==> dist/nullspace-submission.zip"
echo "==> done: $OUT"
