# Nullspace

**Demand-side metadata for agents.** A catalog entry for data that does not exist yet.

Consumer agents search DataHub for an asset that isn't there. Instead of failing silently, each miss materializes or increments a **ghost** — a real DataHub dataset URN tagged `ghost`, with a demand counter and edges back to every requesting agent. When demand crosses threshold, a **builder agent** claims the ghost, opens a real dbt PR, and on merge the ghost **goes solid**: schema, lineage, and provenance pointing at the agents that asked for it.

> Built for [Build with DataHub: The Agent Hackathon](https://datahub.devpost.com/) · deadline **Mon 10 Aug 2026, 5pm EDT** · Apache-2.0

**Ruling:** see [`RULING.md`](./RULING.md). Fallback (tripwire only): Scar Tissue.

## Stranger demo (&lt; 3 minutes)

```bash
# Prerequisites: Docker Desktop running, Python 3.11+, uv or pip
./scripts/up.sh          # DataHub quickstart + Nullspace API + board
./scripts/demo.sh        # three consumers → ghost demand=3 → builder PR → solid
open http://localhost:8787
```

Judges: the **live board** at the deployed URL is a read-only view of a real public DataHub instance running the same compose stack. Primary proof is still local `docker compose` — not a fake endpoint.

## What it uses from DataHub

| Surface | Role |
|---|---|
| Search / GraphQL | Consumers look for the asset (miss → ghost) |
| Dataset entity + tags + properties | Ghost URN, `ghost` tag, demand counter |
| Lineage + aspects | Solidify writeback + requester provenance |
| MCP Server (optional) | Agents can talk to the same graph |

## Repo map

```
nullspace/          # Python package — ghost ops, agents, board API
dbt_project/        # Target repo the builder opens PRs against
scripts/            # up / demo / solidify
forge/              # Concept forge artifacts (archived; not the product)
RULING.md           # Final build law — do not re-litigate
```

## License

Apache-2.0
