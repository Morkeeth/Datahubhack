# STATE — mission control (read this first)

> Every witness row names the **host** it was witnessed on and the command that
> printed it. Night-run receipts from another host are not reused as truth here.

- **Last updated:** 2026-08-09 ~19:25 UTC by Cursor Lane A
- **Host:** `cursor`
- **Phase:** SP 422 unblocked + walk-the-book; stranger report next
- **Worker branch:** `cursor/datahub-hack-setup-4c9d`

## This turn

| Slice | Status | Witness |
|---|---|---|
| SP defs sync before values (no same-batch 422) | ✅ | wiped defs → same-batch failed; sync+fallback creates ghost |
| customProperties fallback when defs unavailable | ✅ | want `fresh-want-after-sp-fix-*` demand=3 state=ghost |
| CLI startup registers SP defs | ✅ | `cli._ns` |
| Builder walks the book / `--want` steer | ✅ | unit: rank + skip/claim lines; shortfall fields |

## Still open

1. Stranger cold-clone timing report (this turn, part 2 of final prompt)
2. Oscar: App → nullspace-dbt / hosted webhook
3. Lane B: MCP local-record warning; video

## Handback — Lane B

`mcp_server.py` ~163–168 stale warning — still yours.
