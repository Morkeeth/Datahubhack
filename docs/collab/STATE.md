# STATE — mission control (read this first)

> Every witness row names the **host** it was witnessed on and the command that
> printed it. Night-run receipts from another host are not reused as truth here.

- **Last updated:** 2026-08-09 ~09:00 UTC by Cursor Lane A
- **Host:** `cursor` (Cloud Agent VM)
- **Phase:** **Catalog is the database** — checks 1–5 + 7 green on host `cursor`; check 6 board assertion waits on Lane B GraphQL board rebase onto trunk
- **Deadline:** Mon 10 Aug 2026 · **Freeze 18:00 Paris**
- **Worker branch:** `cursor/datahub-hack-setup-4c9d`
- **Brief:** `docs/collab/prompts/cursor-long-run-the-catalog-is-the-database.md`

## Check 1 deletion map (before code — host `cursor`)

```text
rm -f /tmp/nullspace-*.json
python3 -m nullspace.cli dump          → []
curl localhost:8787/api/board          → counts all 0
# GMS still held catalog-is-db-baseline-want demand=4 + requesters + resolution
```

That was the map: **dump/board read the cache; the graph still had the truth.**

## Done-when (host `cursor`)

| # | Check | Status | Witness |
|---|---|---|---|
| 1 | Rehydrate from graph | ✅ | `rm -f /tmp/nullspace-*.json` → `cli hydrate` → `cli dump` restored ghosts with demand/requesters/resolution |
| 2 | Survive deletion mid-claim | ✅ | claim → `rm` → hydrate → `cli build` → GMS `state=solid`, resolution retained |
| 3 | Contracts in catalog | ✅ | `register-query` → `rm` contracts+store → `contract-status` from GMS (`nullspace.contracts` JSON). Closest stock home: `datasetProperties.customProperties` (no Demand aspect on v1.7.0 without GMS rebuild) |
| 4 | Stop squatting / defend | ✅ | `docs/design/why-a-dataset-urn.md` (241 words) — RFC spine |
| 5 | Merge closes loop | ✅ | `nullspace-dbt#1` MERGED (`2026-08-09T08:45:31Z`); `finalize --observe-only` → solid; GraphQL: schema 4 fields, `lineage.total=1`, 3 native Owners, tag `solid` |
| 6 | `without-datahub.sh` acceptance | 🟡 | Three refusals + zero ghosts **PASS**; board unreachable **FAIL** on trunk (file board still serves `{"ghosts":[]}`). Test **can fail**: `NULLSPACE_DEAD_GMS=http://localhost:8080 ./scripts/without-datahub.sh` → exit 1. Needs Claude rebase of GraphQL board onto this trunk. |
| 7 | Cold-safe eval | ✅ | Exact-want match; `--cold` runs `cli reset`. Two warm-stack cold runs: **16/0/1** each; Ctrl-C then `--cold` same want: **16/0/1** |

## Next

1. **Lane B:** rebase GraphQL board onto `cursor/datahub-hack-setup-4c9d` so check 6 goes green; point MCP `register_query` at `Nullspace.register_contract` (sidecar cache only).
2. **Stretch (after 6 green):** demand as a DataHub ingestion source.
3. Do not rewrite `emit.py` lineage path; contracts preserved across `_mirror`.

## Canonical

- Prompt: `docs/collab/prompts/cursor-long-run-the-catalog-is-the-database.md`
- Design: `docs/design/why-a-dataset-urn.md`
- Redteam: `docs/collab/reviews/redteam-2026-08-09.md`
