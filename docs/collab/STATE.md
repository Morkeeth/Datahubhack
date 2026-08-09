# STATE — mission control (read this first)

> Every witness row names the **host** it was witnessed on and the command that
> printed it. Night-run receipts from another host are not reused as truth here.

- **Last updated:** 2026-08-09 ~13:00 UTC by Cursor Lane A
- **Host:** `cursor`
- **Phase:** Build day — receipts + schema Assertions on the URN; video tomorrow
- **Worker branch:** `cursor/datahub-hack-setup-4c9d`

## Today (video tomorrow)

| Slice | Status | Witness |
|---|---|---|
| Structured props + Queries + Owners from miss | ✅ | `ambitious first-class lifecycle` |
| Demand ingestion source parity | ✅ | `datahub ingest` + warehouse-log script |
| Merge webhook | ✅ | `nullspace.webhook` |
| Builder plan on ghost URN | ✅ | want `catalog-plan-survives-delete` |
| `NULLSPACE_STORE=memory` | ✅ | hydrate-only CLI mode |
| OSS connector sketch | ✅ | `docs/design/oss-nullspace-demand-source.md` |
| Builder receipt on ghost URN | ✅ | want `catalog-receipt-assert-*`: solidify → wipe receipt file → `load_review_receipt` from GMS |
| DATA_SCHEMA Assertion on solidify | ✅ | same want: `nullspace.assertion_urn` + AssertionInfo EXACT_MATCH; `--review-want` matches |
| `demo.sh` video path | ✅ | prints board / review-want / webhook cues |

## Still open (not video)

1. Host webhook + GitHub App write to `nullspace-dbt` (Oscar)
2. File OSS PR to `datahub-project/datahub` from the sketch (Oscar / Lane B)
3. Lane B: kill MCP “recorded locally” warning; submission package (+ video tomorrow)

## Handback — Lane B

`mcp_server.py` ~163–168 stale local-record warning — still yours.
