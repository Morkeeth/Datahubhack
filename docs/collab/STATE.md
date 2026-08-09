# STATE — mission control (read this first)

> Every witness row names the **host** it was witnessed on and the command that
> printed it. Night-run receipts from another host are not reused as truth here.

- **Last updated:** 2026-08-09 ~14:30 UTC by Cursor Lane A
- **Host:** `cursor`
- **Phase:** Build day — witness parity + soft-merge ingest; video tomorrow
- **Worker branch:** `cursor/datahub-hack-setup-4c9d`

## Today (video tomorrow)

| Slice | Status | Witness |
|---|---|---|
| Structured props + Queries + Owners from miss | ✅ | earlier |
| Demand ingestion + webhook + plans/receipts/Assertions | ✅ | earlier |
| `solid_witness` assertion + queries | ✅ | want `witness-parity-*`: assertion DATA_SCHEMA fields present |
| Finalize refreshes catalog receipt | ✅ | `solidify_after_merge` → `_write_review_receipt` |
| Webhook uses CLI store policy | ✅ | `NULLSPACE_STORE=memory` hydrate-only |
| Demand ingest soft-merge claimed/solid | ✅ | `merge_demand_custom` unit + live prior solid |
| README cold `export NULLSPACE_STORE` + `--review-want` | ✅ | docs |

## Still open (not video)

1. Host webhook + GitHub App write to `nullspace-dbt` (Oscar)
2. File OSS PR to `datahub-project/datahub` from the sketch (Oscar / Lane B)
3. Lane B: kill MCP “recorded locally” warning; submission package (+ video tomorrow)

## Handback — Lane B

`mcp_server.py` ~163–168 stale local-record warning — still yours.
