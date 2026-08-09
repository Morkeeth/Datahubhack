# Where to look

Nullspace makes DataHub record the tables your agents asked for and could not get.

## Start here

| | |
|---|---|
| What it is, and the argument for it | [`submission/pitch.md`](submission/pitch.md) |
| Every link, every number, and how each one was checked | [`submission/SUBMISSION.md`](submission/SUBMISSION.md) |
| Why a ghost is a Dataset URN, and the case against it | [`design/why-a-dataset-urn.md`](design/why-a-dataset-urn.md) |
| The upstream RFC this project argues for | [datahub#19022](https://github.com/datahub-project/datahub/pull/19022) |

## Use of DataHub

Ghosts are real DataHub datasets, not a sidecar. Each one carries structured
properties, Query entities for the requesters' registered SQL, ownership,
`schemaMetadata`, `upstreamLineage`, and its full resolution history. Demand also
ships as a stock ingestion source, so `datahub ingest -c infra/datahub/nullspace_demand.yml`
loads it the way any other source loads.

Delete DataHub and the product does not degrade, it disappears. That is a test,
not a claim: `scripts/without-datahub.sh` asserts three agents refuse, zero
ghosts are written, and the board reports the catalog unreachable. It exits non
zero if any of that silently succeeds.

## Technical execution

`pytest nullspace/tests` is the unit surface. `scripts/eval_nullspace.py --cold`
is the acceptance surface and reads every claim back out of the catalog rather
than out of a log line.

The one number that is not a read back is the queries that could not run and now
do. That is a live `READ ONLY` execution, because no amount of metadata settles
whether an agent is still blocked. It is labelled as the exception everywhere it
appears.

## Artifacts a judge can read without running anything

- Pull requests an agent opened by itself: [Morkeeth/nullspace-dbt](https://github.com/Morkeeth/nullspace-dbt/pulls?q=is%3Apr)
- Generated dbt models: [`examples/`](../examples) and the merged models on that repo's `main`
- The demand board and the order book, frozen with real numbers: <https://nullspace-five.vercel.app>

## Honest boundaries

Stated here rather than left to be found. Requester identities and warehouse rows
are disclosed demo traffic; the misses behind them are genuine Postgres errors.
Demand counts independent requesters, so a dashboard refreshing every ten minutes
is one agent and not a hundred and forty four. Nobody should merge agent written
SQL unreviewed and this does not ask you to.

## Not part of the submission

[`archive/`](archive) holds the working notes: concept sets written before the
idea was chosen, agent to agent handoffs, and the adversarial reviews we ran on
ourselves. Kept because they are honest, moved because they are process rather
than product.
