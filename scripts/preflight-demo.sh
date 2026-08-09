#!/usr/bin/env bash
# Preflight before recording / X clip / stranger demo.
# Exit non-zero on any hard fail so you do not film a dirty host.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

GMS="${DATAHUB_GMS_URL:-http://localhost:8080}"
BOARD="${NULLSPACE_BOARD_URL:-http://localhost:8787}"
FAIL=0

say() { printf '%s\n' "$*"; }
ok() { say "OK  $*"; }
bad() { say "FAIL $*"; FAIL=1; }
warn() { say "WARN $*"; }

say "==> Nullspace preflight"

if curl -sf "$GMS/health" >/dev/null; then
  ok "GMS healthy at $GMS"
else
  bad "GMS not healthy at $GMS — run ./scripts/up.sh"
fi

if curl -sf "$BOARD/api/board" >/dev/null; then
  ok "board reachable at $BOARD"
  python3 - <<'PY' || true
import json, os, urllib.request
board = os.environ.get("NULLSPACE_BOARD_URL", "http://localhost:8787")
data = json.load(urllib.request.urlopen(board + "/api/board", timeout=5))
c = data.get("counts") or {}
n = sum(c.get(k, 0) for k in ("ghost", "claimed", "solid"))
cat = data.get("catalog")
print(f"    catalog={cat} ghosts={c.get('ghost')} claimed={c.get('claimed')} solid={c.get('solid')} total={n}")
if cat not in (None, "live") and cat != "live":
    print("    WARN board catalog is not live")
if n > 20:
    print("    WARN board is dirty (total>20) — run: python3 -m nullspace.cli reset")
PY
else
  bad "board not reachable at $BOARD"
fi

if command -v dbt >/dev/null 2>&1; then
  VER="$(dbt --version 2>&1 | head -5 || true)"
  if echo "$VER" | grep -qiE 'fusion|2\.0\.0-alpha|2\.0\.0a'; then
    bad "dbt is Fusion/alpha — pin dbt-core<2 (bash scripts/install-deps.sh)"
    say "$VER" | sed 's/^/    /'
  else
    ok "dbt looks classic: $(echo "$VER" | head -1)"
  fi
else
  warn "dbt not on PATH — solid may be CTAS only"
fi

if gh api repos/Morkeeth/nullspace-dbt --jq '.permissions.push' 2>/dev/null | grep -q true; then
  ok "gh can push Morkeeth/nullspace-dbt (real https:// PRs possible)"
else
  warn "gh cannot push nullspace-dbt — do not say 'pull request' over file://"
fi

RFC_TITLE="$(gh pr view 19022 --repo datahub-project/datahub --json title -q .title 2>/dev/null || true)"
if [[ "$RFC_TITLE" == docs\(rfc\):* ]]; then
  ok "RFC #19022 title is conventional-commit clean"
else
  warn "RFC #19022 title still needs APPLY.md retitle (now: ${RFC_TITLE:-unreachable})"
fi

say "==> Suggested X citation PR"
say "    https://github.com/Morkeeth/nullspace-dbt/pull/5"

if [[ "$FAIL" -ne 0 ]]; then
  say "==> PREFLIGHT FAILED — fix above before recording"
  exit 1
fi
say "==> PREFLIGHT OK"
exit 0
