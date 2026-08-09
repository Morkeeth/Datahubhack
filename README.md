# Nullspace

**A catalog is a map of what exists. Nullspace makes DataHub the first catalog
that also maps what is missing.**

An agent searches for a table it needs, does not find it, and fails silently in
its own context. That miss is thrown away today — no ticket, no record, nothing.
Nullspace keeps it: every miss materialises or increments a **ghost**, a real
DataHub dataset URN tagged `ghost`, carrying a demand counter and edges back to
every agent that asked. Three agents in three separate contexts discover, for the
first time, that they wanted the same thing. At the threshold a builder agent
claims it, writes a real dbt model, opens a real pull request — and on merge the
ghost goes solid, with the requesters as native Owners of the table they caused
to exist.

Then the part everyone forgets: **the agents that were blocked stop being
blocked, and nobody had to ask again.**

### Point your own agent at it — no clone, no Docker

```bash
python scripts/remote_agent.py --url <the public MCP url> \
    --want "customer health score by account" \
    --agent your-agent-name \
    --query "SELECT account_id, health_score FROM {}"
```

Your identity comes from the MCP `clientInfo` handshake, not a field you type, so
the demand the board shows really is yours. `bash scripts/serve.sh --public`
prints a live URL for any instance, including your own.

**This needs a running instance.** <https://nullspace-five.vercel.app> is a frozen
snapshot of a real catalog — it is there so the numbers are readable at any hour,
but it serves no MCP endpoint and nothing can be written to it. To have your own
agent create demand, point it at a live instance: ours while the machine hosting it
is awake, or your own after one `docker compose up`.

### What has actually happened, with receipts

| | |
|---|---|
| A pull request an agent wrote and opened by itself | [`nullspace-dbt#5`](https://github.com/Morkeeth/nullspace-dbt/pull/5), merged |
| Demand-side metadata proposed upstream | [`datahub-project/datahub#19022`](https://github.com/datahub-project/datahub/pull/19022) |
| Demand harvested with **zero adoption** | 2,405 real Postgres `relation does not exist` errors → 1,253 attributed requests across 51 wants, ranked |
| The three blocked queries | run, verified by executing them — `python -m nullspace.console unblocked "monthly recurring revenue by segment"` |

Delete DataHub and this does not degrade, it disappears: `./scripts/without-datahub.sh`
shows three agents failing in three silos with no namespace in which the thing
they all want can be named.

Built for [Build with DataHub: The Agent Hackathon](https://datahub.devpost.com/)
· Apache-2.0.

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
export NULLSPACE_STORE="${NULLSPACE_STORE:-/tmp/nullspace-ghosts.json}"
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

Review the last decision against DataHub (file cache **or** catalog):

```bash
python3 -m nullspace.builder --review /tmp/nullspace-builder-receipt.json
python3 -m nullspace.builder --review-want "your demand"
```

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
./scripts/ingest-demand-from-warehouse-logs.sh   # postgres error log → demand
```

Ghosts carry **structured properties**, **Query** contracts, **Owners from the
first miss**, and the fulfillment PR in **institutionalMemory**. Builder plans
and review receipts live on the ghost URN (`nullspace.builder_plan` /
`nullspace.builder_receipt`) — delete `/tmp` mid-flight and they still load.
Solidify emits a native **DATA_SCHEMA** Assertion (exact match) and records
`nullspace.assertion_urn`. Optional hydrate-only mode:

```bash
NULLSPACE_STORE=memory python3 -m nullspace.cli dump
python3 -m nullspace.builder --review-want "your demand"
```

Merge→solid can be driven by webhook: `python3 -m nullspace.webhook` (:8790).
Upstream connector sketch: [docs/design/oss-nullspace-demand-source.md](docs/design/oss-nullspace-demand-source.md).

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
