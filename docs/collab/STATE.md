# STATE — mission control (read this first)

> Every witness row names the **host** it was witnessed on and the command that
> printed it. Night-run receipts from another host are not reused as truth here.

- **Last updated:** 2026-08-09 ~12:00 UTC by Cursor Lane A
- **Host:** `cursor` (Cloud Agent VM)
- **Phase:** Check 6 green on GraphQL board; demand ingestion source shipped
- **Deadline:** Mon 10 Aug 2026 · **Freeze 18:00 Paris**
- **Worker branch:** `cursor/datahub-hack-setup-4c9d`

## Check 6 (re-run after Lane B trunk `b7b63f7`)

`./scripts/without-datahub.sh` → **exit 0** on host `cursor`:
three refusals, zero local ghosts, board `catalog: unreachable`.

Prove it can fail: `NULLSPACE_DEAD_GMS=http://localhost:8080 ./scripts/without-datahub.sh` → **exit 1**.

## Stretch — demand as DataHub ingestion source

```bash
datahub ingest -c infra/datahub/nullspace_demand.yml
```

Source: `nullspace.ingestion.demand.NullspaceDemandSource` (custom type, no GMS fork).
Witness: ghost `churn by cohort` with `nullspace.schema_source=nullspace.ingestion.demand`, demand=3, contracts JSON.

## Handback — Lane B (do not edit from Lane A)

`nullspace/mcp_server.py` ~163–168 still warns *"demand was recorded locally only"* after D24 made `consumer_search(dh=None)` refuse. That string is now false. **Yours to delete/replace** — Lane A will not touch `mcp_server.py`.

## Catalog-is-database checks

| # | Status |
|---|---|
| 1 hydrate | ✅ |
| 2 mid-claim delete | ✅ |
| 3 contracts in GMS | ✅ |
| 4 why-a-dataset-urn.md | ✅ |
| 5 merge→finalize | ✅ |
| 6 without-datahub | ✅ (this turn) |
| 7 cold eval | ✅ |
| stretch ingest source | ✅ (this turn) |
