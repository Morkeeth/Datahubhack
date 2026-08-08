# Nullspace

**Demand-side metadata: a catalog entry for data that does not exist yet.**

Requester agents search DataHub and miss in separate contexts. Nullspace turns
those misses into demand on one shared ghost. At the threshold, a real builder
agent reads the board over MCP, chooses what to build, explains why, discovers a
warehouse source through DataHub, writes executable dbt SQL from the registered
queries, and claims the ghost. When it goes solid, DataHub shows its schema,
upstream lineage, resolution history, and the requester agents as native Owners.

Built for [Build with DataHub: The Agent Hackathon](https://datahub.devpost.com/)
· deadline Mon 10 Aug 2026, 5pm EDT · Apache-2.0.

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

Install the Python tooling:

```bash
bash scripts/install-deps.sh
```

## Cold reveal (&lt; 3 minutes)

From a clean clone:

```bash
# Prerequisites: Docker Desktop, Docker Compose v2, Python 3.11+
bash scripts/install-deps.sh
./scripts/up.sh
NULLSPACE_STORE=/tmp/nullspace-eval-fresh.json \
NULLSPACE_EVAL_WANT="fresh-nullspace-$(date +%s)" \
python3 scripts/eval_nullspace.py --cold
open http://localhost:8787
```

The warehouse rows and requester-agent identities are disclosed demo data. The
proof is not staged: the eval reads schema, lineage, ownership, demand, tags, and
resolution history back from DataHub.

## Watch the builder decide

After requester agents have registered queries against open ghosts:

```bash
python3 -m nullspace.builder
```

The builder connects as an MCP client, calls `open_demand`, chooses the highest
independent demand (oldest demand breaks ties), states its reason, reads the
registered queries, discovers a real warehouse source from DataHub, and prints
the executable dbt SQL it generated. With demand below threshold it visibly
declines and names the exact shortfall.

Review the last successful decision against DataHub again:

```bash
python3 -m nullspace.builder --review /tmp/nullspace-builder-receipt.json
```

The receipt includes the decision, generated SQL, warehouse `EXPLAIN` proof,
source URN, and DataHub's current schema, lineage, ownership, tags, and demand.

## What is visible in DataHub

- schema fields requested before the asset existed
- upstream lineage to the warehouse table read by the generated model
- requester agents in the native Owners panel
- demand, claim, and resolution history in dataset properties

## Honest boundary

`dbt_project/` has no GitHub remote. `pr_url` is therefore a `file://` local
change reference, **not a pull request**. Nullspace does not claim a PR until an
open GitHub PR exists.

## License

Apache-2.0 — see [LICENSE](LICENSE).
