# Nullspace

**Demand-side metadata for agents.** A catalog entry for data that does not exist yet.

Agents search DataHub for an asset that is not there. Instead of failing silently,
each miss creates or increments a **ghost** — a real DataHub dataset URN tagged
`ghost`, carrying demand from distinct requester agents. When demand reaches the
threshold, a builder agent can **claim** it. The local demo writes a dbt model and
the ghost goes **solid**, carrying schema, lineage, resolution history, and native
DataHub ownership for the requester agents.

> Built for [Build with DataHub: The Agent Hackathon](https://datahub.devpost.com/) · deadline **Mon 10 Aug 2026, 5pm EDT** · Apache-2.0

## One-command local substrate

```bash
docker compose up
```

From a clean clone, Compose starts:

- DataHub OSS at http://localhost:9002 (`datahub` / `datahub`) with GMS at
  http://localhost:8080
- a writable Postgres warehouse at `localhost:5432`
  (`agent` / `agent`, database `warehouse`)
- a one-shot ingestion job that profiles the warehouse and publishes its
  `ecommerce` tables and view to DataHub

Wait until `metadata-ingestion` reports `Pipeline finished successfully`.
DataHub and the warehouse remain running after that one-shot container exits.
Details and verification commands:
[infra/datahub/README.md](infra/datahub/README.md).

Query a real entity from the live graph:

```bash
bash scripts/query-seeded-entity.sh
```

Stop the stack with `docker compose down`; add `--volumes` for a completely
clean reset.

Install Python tooling and Nullspace:

```bash
bash scripts/install-deps.sh
```

**Ruling:** see [`RULING.md`](./RULING.md). Fallback (tripwire only): Scar Tissue.

## Stranger demo (&lt; 3 minutes)

```bash
# Prerequisites: Docker Desktop, Docker Compose v2, Python 3.11+
bash scripts/install-deps.sh
./scripts/up.sh          # repository DataHub stack + seeded warehouse
./scripts/demo.sh        # requester misses → demand=3 → claim → local dbt model → solid
open http://localhost:8787
```

The seeded warehouse and requester-agent names are disclosed demo data. DataHub
is the witness: the demo reads the solid asset back and prints the returned
schema metadata, upstream lineage, ownership, demand, and requesters.

`dbt_project/` currently has no GitHub remote. The builder therefore produces a
local branch and `file://` reference, **not a pull request**. A real PR is not
claimed until a public target remote exists.

## What it uses from DataHub

| Surface | Role |
|---|---|
| Search / GraphQL | Requester agents look for the asset; a miss creates demand |
| Dataset entity + tags + properties | Ghost URN, state, demand, requesters |
| SchemaMetadata | Real dbt output fields when the ghost goes solid |
| UpstreamLineage | Warehouse assets read by the dbt model |
| Ownership | Requester agents as `nullspace_requester` owners |
| MCP Server | Independent agents use the shared namespace |

## Repo map

```
nullspace/          # ghost lifecycle, MCP surface, board
dbt_project/        # local target repo; no remote yet
scripts/            # up / demo / solidify
forge/              # Concept forge artifacts (archived; not the product)
RULING.md           # Final build law — do not re-litigate
```

## License

Apache-2.0 — see [LICENSE](LICENSE).
