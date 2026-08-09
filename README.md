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
./scripts/up.sh
```

That starts Compose (DataHub + warehouse + ingestion) **and** the Nullspace
board on http://localhost:8787. Compose alone (`docker compose up`) brings up
the substrate without the board.

From a clean clone you get:

- DataHub OSS at http://localhost:9002 (`datahub` / `datahub`) with GMS at
  http://localhost:8080
- a writable Postgres warehouse at `localhost:5432`
  (`agent` / `agent`, database `warehouse`)
- a one-shot ingestion job that profiles the warehouse and publishes its
  `ecommerce` tables and view to DataHub
- the Nullspace board at http://localhost:8787

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
# Same NULLSPACE_STORE as up.sh/board (default /tmp/nullspace-ghosts.json)
NULLSPACE_EVAL_WANT="fresh-nullspace-$(date +%s)" \
python3 scripts/eval_nullspace.py --cold
open http://localhost:8787
```

The warehouse rows and requester-agent identities are disclosed demo data. The
proof is not staged: the eval reads schema, lineage, ownership, demand, and tags
back from DataHub. Resolution history is written into dataset properties on the
solid asset; open the dataset in DataHub to read it.

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

The builder targets the public fulfillment repo
[`Morkeeth/nullspace-dbt`](https://github.com/Morkeeth/nullspace-dbt) (D9).
`main` is hollow — no `ghost_*` models — so every model must arrive through a
pull request the builder opens against **`main`**.

When the authenticated `gh` CLI (or `NULLSPACE_DBT_TOKEN`) can push, `pr_url` is
an `https://github.com/...` URL, the ghost stays **claimed** until that PR
merges, and `python3 -m nullspace.cli finalize --want "..."` solidifies on
merge. If push is unavailable, `pr_url` stays a `file://` local change
reference — **not a pull request** — and solidify still runs locally so the
DataHub witness path works. Nullspace never claims a PR that does not exist.

Reset a dirty demo graph before a stranger run:

```bash
python3 -m nullspace.cli reset
```

After reset, DataHub search for platform `nullspace` returns **0** assets.

## The catalog is the database

Local JSON under `/tmp` is a cache. Demand, requesters, contracts, resolution
history, and the state machine live on DataHub. Delete the files mid-demo and
rehydrate:

```bash
rm -f /tmp/nullspace-*.json
python3 -m nullspace.cli hydrate
python3 -m nullspace.cli dump
```

Register requester SQL against the ghost URN (read back with the sidecar gone):

```bash
python3 -m nullspace.cli register-query --want "…" --agent "…" --sql "…" --fields "a,b"
rm -f /tmp/nullspace-contracts.json
python3 -m nullspace.cli contract-status --want "…"
```

Why ghosts are Dataset URNs: [docs/design/why-a-dataset-urn.md](docs/design/why-a-dataset-urn.md).

Demand as a stock ingestion source (the RFC with a connector behind it):

```bash
datahub ingest -c infra/datahub/nullspace_demand.yml
```

## Subtraction proof (Law 2)

With GMS unreachable, three isolated agents each refuse — there is no shared
namespace in which their demand can be named. The script is an acceptance test
(non-zero if any assertion silently succeeds):

```bash
./scripts/without-datahub.sh
# Prove it can fail:
NULLSPACE_DEAD_GMS=http://localhost:8080 ./scripts/without-datahub.sh; echo $?
```

Deleting DataHub does not degrade Nullspace into a local JSON loop; it deletes
the product.

## License

Apache-2.0 — see [LICENSE](LICENSE).
