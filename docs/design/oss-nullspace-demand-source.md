# Upstream sketch — Nullspace Demand Source

This is the body of a contribution to `datahub-project/datahub`, not a docs
typo. Filing the PR is Oscar / Lane B; the implementation already runs here.

## What it is

A custom metadata-ingestion source that turns unmet demand into Dataset entities
on platform `nullspace`:

```yaml
source:
  type: nullspace.ingestion.demand.NullspaceDemandSource
  config:
    postgres_log: /var/log/postgresql/postgresql.log
    # or:
    # events: [{ want, agent_id, sql, needs_fields }]
sink:
  type: datahub-rest
  config:
    server: http://localhost:8080
```

## What a maintainer gets

| Aspect | Purpose |
|---|---|
| `structuredProperties` `nullspace.demand/state/want` | Typed lifecycle, not a JSON bag |
| `ownership` + `ownershipType:nullspace_requester` | Agents that asked, from the first miss |
| `query` + `querySubjects` | Registered SQL aimed at the ghost URN |
| `globalTags` `ghost` | Discoverable demand |
| `datasetProperties.customProperties` | Dual-write for search/UI until an RFC aspect lands |

## Why Dataset URNs

See `docs/design/why-a-dataset-urn.md`. Demand that cannot search, own, or grow
lineage is a second product. We refuse that.

## Local proof (host-named receipts go in STATE)

```bash
datahub ingest -c infra/datahub/nullspace_demand.yml
./scripts/ingest-demand-from-warehouse-logs.sh
```

## Packaging for upstream

1. Move `nullspace/ingestion/demand.py` under `metadata-ingestion/src/datahub/ingestion/source/nullspace/`.
2. Register entry point `nullspace-demand = ...:NullspaceDemandSource`.
3. Add recipe + docs under `metadata-ingestion/docs/sources/nullspace/`.
4. Open one PR: connector + design note. No drive-by docs.

Until that PR is open, this file is the honest standing of the contribution.
