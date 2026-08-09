# STATE — mission control (read this first)

> Every witness row names the **host** it was witnessed on and the command that
> printed it. Night-run receipts from another host are not reused as truth here.

- **Last updated:** 2026-08-09 ~19:45 UTC by Cursor Lane A
- **Host:** `cursor`
- **Phase:** SP 422 unblocked; walk-the-book shipped; stranger report filed (no fixes in that pass)
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

## Still open

1. Oscar: App → nullspace-dbt / hosted webhook (real `https://` PR)
2. Live watcher money shot: skip churn/NRR → claim `pipeline coverage by rep` → solid + `agents_return`
3. Lane B: MCP local-record warning; video
4. Product ruling: whether `install-deps` must install `dbt-postgres` + write profile before freeze

## Handback — Lane B

`mcp_server.py` ~163–168 stale warning — still yours.
