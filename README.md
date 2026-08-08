# Join Treaty — DataHub Agent Hackathon

Parallel multi-model ideation for **Build with DataHub: The Agent Hackathon** (deadline Mon 10 Aug 2026, 5pm EDT).

Public repo · Apache-2.0 · local DataHub Docker for judge demos.

## Purpose

The concept forge is complete. **Join Treaty** is the locked winner:

> Mine the equality joins teams repeat in DataHub's query history, verify each
> one against schema and column profiles, and write it back as a native ER model
> relationship — the join graph that lineage never captures.

Read the [final ranking](docs/final-ranking.md) and locked
[build brief](docs/build-brief.md).

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

Python tooling and the Join Treaty app are installed by:

```bash
bash scripts/install-deps.sh
```

## Join Treaty demo (< 3 minutes)

With the substrate running (`docker compose up`) and deps installed, the whole
mine → validate → native write → proof loop is four commands:

```bash
# Prerequisites: Docker Desktop, Docker Compose v2, Python 3.11+
bash scripts/install-deps.sh
./scripts/up.sh          # repository DataHub stack + seeded warehouse
python3 scripts/moonshot_demo.py
# three real MCP requester agents → demanded schema → claim → dbt model → solid
open http://localhost:8787
```

The seeded warehouse and requester-agent names are disclosed demo data. DataHub
is the witness: the demo reads the solid asset back and prints the returned
schema metadata, upstream lineage, ownership, demand, and requesters.
The schema is the union of fields the requester agents declared for their queued
queries; after solidification, each query is checked against DataHub's returned
schema and reports `RUNS` or the exact missing fields.

- Offline artifact: [examples/join-treaty-receipt.json](examples/join-treaty-receipt.json)
- Deterministic tests: `pytest app/tests`
- Design + morning checklist: [docs/night-build-plan.md](docs/night-build-plan.md)
- DataHub OSS V2 does not yet render ER relationships in its UI; the native
  proof is the read-after-write plus the receipt in each dataset's Properties
  tab (an honest platform gap, not a faked screenshot).

## Concept forge

| Folder | Owner |
| --- | --- |
| [concepts/grok](concepts/grok) | Grok concepts |
| [concepts/gpt](concepts/gpt) | GPT concepts |
| [concepts/third](concepts/third) | Competitive-whitespace pass |

Rules and scoring: [docs/playbook.md](docs/playbook.md). Final ruling:
[docs/final-ranking.md](docs/final-ranking.md). Agent instructions:
[AGENTS.md](AGENTS.md).

## Constraints (hard)

- ~2 build days after concept lock; agents write the code
- Stranger demos from README in &lt;3 minutes
- Live URL + &lt;3-min video + Apache-2.0 public repo
- DataHub local Docker — judges cannot reach a private instance

## Cloud agents

`.cursor/environment.json` builds a Docker-capable image and installs DataHub tooling on each Build. Docker starts with the environment; run `scripts/setup-datahub.sh` when a live catalog is needed.

## Status

**Ideation closed. Join Treaty MVP built on the substrate: deterministic
mining, native `ERModelRelationship` write-back, dataset receipts, web view,
and tests.**

## License

Apache-2.0 — see [LICENSE](LICENSE).
