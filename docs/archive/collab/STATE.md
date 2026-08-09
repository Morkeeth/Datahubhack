# STATE — mission control (read this first)

> Every witness row names the **host** it was witnessed on and the command that
> printed it. Night-run receipts from another host are not reused as truth here.

- **Last updated:** 2026-08-09 ~23:35 UTC by Cursor Lane A
- **Host:** `cursor`
- **Phase:** Submitted — Cursor retro filed (`hack.md` + reviews/retro-cursor-…); Claude appends Lane B
- **Worker branch:** `cursor/datahub-hack-setup-4c9d`

## This turn

| Slice | Status | Witness |
|---|---|---|
| SP defs sync before values (no same-batch 422) | ✅ | wiped defs → same-batch failed; sync+fallback creates ghost |
| customProperties fallback when defs unavailable | ✅ | want `fresh-want-after-sp-fix-*` demand=3 state=ghost |
| CLI startup registers SP defs | ✅ | `cli._ns` |
| Builder walks the book / `--want` steer | ✅ | unit: rank + skip/claim lines; shortfall fields |
| DatasetProperties props-cache refresh after emit | ✅ | `build_and_solidify` → state=solid (was: builder_plan RAW fail) |
| Stranger cold-clone report | ✅ | `/tmp/nullspace-stranger` — failures listed below (not fixed in that pass) |

## Stranger failures (report only — do not fix here)

Clone: `git clone` → `/tmp/nullspace-stranger` from `cursor/datahub-hack-setup-4c9d`. Followed README literally.

1. **`bash scripts/install-deps.sh`** — exit 0, but does **not** install `dbt` / `dbt-postgres` and does **not** write `~/.dbt/profiles.yml`. `requirements.txt` has no dbt. Stranger solid without dbt is warehouse fiction risk (D33 discloses `warehouse_ctas` fallback on this host).
2. **`eval_nullspace.py --cold` CHECK 5** — failed with `builder returned status=None` / `DataHub builder_plan read-after-write failed` until props-cache refresh (D37). Ghost checks passed via SP→customProperties fallback.
3. **`./scripts/up.sh`** — OK on this host (stack already healthy). Warehouse has all 7 tables from `infra/warehouse/init.sql` (+ test ghost tables).
4. **`bash scripts/serve.sh`** (no `.venv`) — works (falls back to `python3`); timeout 124 = still running.
5. **README links** `nullspace-dbt#2`, `datahub#19022` — HTTP 200 anonymous.

## Design (wrapped — not shipping)

Comps in `docs/design/board-options-v2.html` + screenshots in `docs/design/options/`.
Oscar has a separate design idea; **do not merge a board restyle from these comps** until that lands.
`board.html` stays Darkroom (M1).

## Submission audit

Full multi-model report: **`docs/archive/collab/SUBMISSION-AUDIT.md`**  
Consensus: **SHIP WITH GAPS** — engine real; recording risks are board pollution, `file://` PR, dbt Fusion→CTAS, walk-the-book not in `demo.sh`.

## Still open (submission blockers)

1. **Lane B NOW:** harden https://github.com/datahub-project/datahub/pull/19022 — start at `docs/oss/datahub-rfc-19022/TO-CLAUDE.md` (full text: `docs/archive/collab/handoffs/008-to-claude-harden-rfc-19022.md`)
2. Oscar recording / video upload
3. Product ruling leftovers only if stranger path still broken on laptop

## Handback — Lane B

**HANDOFF 008** — apply the RFC polish kit, retitle PR, green CI, post reviewer-response.
Do **not** open a connector PR. Cursor cannot push `Morkeeth/datahub`.
