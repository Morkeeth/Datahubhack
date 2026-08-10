# Nullspace — the pitch

*The submission description and the startup frame. Written 2026-08-09, Paris.*

---

## One line

**A catalog is a map of what exists. Nullspace makes DataHub the first catalog that
also maps what is missing.**

---

## The insight

An agent runs an analytics query, searches the catalog for the table it needs, and does
not find it. Today that miss is **thrown away** — it becomes a shrug in one agent's
context window and nothing else. No human files a ticket. No system records it.

Multiply that by the number of agents a company will be running in eighteen months and
you get the most valuable dataset nobody is collecting: **a continuous, attributed,
machine-readable record of what your organisation's data consumers needed and could not
get.**

Nullspace collects it. Every miss materialises or increments a **ghost** — a real DataHub
dataset URN under platform `nullspace`, tagged `ghost`, carrying a demand counter and edges
back to every agent that asked. Three independent agents in three separate contexts
discover, for the first time, that they wanted the same thing.

When demand crosses threshold a builder agent claims the ghost, reads the requesters' own
registered queries off the graph to infer the grain, discovers a warehouse source through
DataHub, validates its generated SQL against the live warehouse, and **opens a real pull
request**. On merge the ghost goes solid: real schema, real lineage, and the demand edges
persist as provenance pointing at the agents that caused the table to exist.

The ghost is not a ticket. It is a **catalog entity** — addressable, searchable, ownable,
and lineage-bearing, months before the data behind it exists.

## Why this is DataHub's, and nowhere else's

Delete DataHub and Nullspace does not degrade — **it disappears**. There is no other
system where a thing that does not exist can be given a URN, searched for, tagged, owned,
and wired into lineage. A queue in Jira cannot be an upstream. A Slack thread cannot carry
provenance. The handshake between three agents that each failed in isolation can only
happen inside a shared metadata graph, because that is the only place their separate
failures become the same object.

That is also why the contribution goes back upstream as an RFC: **demand-side metadata
belongs in the catalog spec**, not in a wrapper around it.

## Why now

Three things became true at once. Agents run enough analytics that misses are a high-volume
signal rather than an anecdote. MCP gives every agent a common way to reach a catalog, so
the miss can be captured at the point it happens. And an agent can now write a defensible
dbt model — not a good one unsupervised, but a good enough draft that a human reviews in
two minutes instead of writing in two days.

None of those was true eighteen months ago. All three are load-bearing.

## The ladder

| | | |
|---|---|---|
| **v1 — today, running** | Agents opt in through MCP. Demand accrues on a ghost. A builder claims it and opens a PR. | Shipped and demonstrable |
| **v2 — the one that matters** | Demand harvested from **query logs** — Snowflake history, dbt failures, BI errors, LLM tool traces. Nobody has to adopt anything; the misses were already being logged. | Removes adoption as the bottleneck |
| **v3** | Anyone claims a ghost: your builder, a consultancy, a vendor, a human on a Friday. Demand becomes a market inside the org. | Fulfilment marketplace |
| **v4** | Demand aggregated **across** organisations. *Trial-to-paid conversion by cohort* wanted at four hundred companies is a schema standard forming in public — the place data models get discovered instead of reinvented for the ten-thousandth time. | The company |

## Three doors DataHub already built and left open

_Added 2026-08-10, after reading what DataHub shipped this year._

DataHub's own 2026 positioning is the strongest argument for this. DataHub Cloud v1
launched in May as a context layer between analytics agents — Databricks Genie, Snowflake
Intelligence — and the warehouse, "pushing accuracy levels beyond 90%", on a $35M Series B
raised to enable AI data management.

**Accuracy is measured on questions that can be answered.** The question that cannot be
answered lowers no score, produces no citation, and leaves no trace anyone reads. That is
not an accuracy problem and more context cannot close it — it is a missing entity problem.

So this does not need a new product surface. It needs three doors that already exist:

| DataHub already shipped | Nullspace lands as |
|---|---|
| **Skills Registry** — `datahub-search`, `-lineage`, `-enrich`, `-quality`, all of which assume the asset exists | `datahub-demand`, the sibling that handles the miss. No metadata-model change required. |
| **The metadata model** | RFC #19022, open, arguing against our own `dataset`-squat |
| **Micro Frontends** — "build and run custom applications inside DataHub without modifying the core platform" | The order book as an app: every want in the organisation, ranked by how many agents are waiting |

The moat argument below is unchanged by this, and gets sharper: the reason an
agent-observability vendor cannot take this is that a trace has no identity, so two
identical failures in two teams never meet. The industry's current answer routes failed
traces into **evaluation datasets**, not back into the catalog. Convergence needs a shared
namespace with ownership and lineage, which is the definition of a catalog.

## The moat, stated honestly

**It is not the code.** The mechanic is a demand counter, a threshold and a code
generator; DataHub, Atlan or Secoda could build it in a weekend, and if this is right they
should.

The moat is the **miss corpus** — what agents asked for and did not find, per org,
compounding daily, attributable to the team that needed it. It cannot be bought, it gets
more valuable with age, and the company that starts collecting it first is the only one
who has last year's.

## What we will not claim

**No data team merges agent-written SQL into production unreviewed, and we do not think
they should.** The honest product is *demand, plus a drafted pull request, plus a human
who reviews it in two minutes*. Every claim in this submission has a human at the merge
button. Anyone selling you autonomy here is selling you an incident.

Likewise: the human ancestor of this exists. Secoda ships data-request management for
people. Our claim is narrower and, we think, more interesting — **the request queue becomes
a catalog entity, and the requesters are agents.**

## What is actually running, today

- Three independent MCP clients, each identified from its own `clientInfo` handshake,
  converging on one ghost — not a `for` loop over three strings.
- Schema derived from the union of the requesters' declared query fields, not hardcoded.
- A builder agent that chooses which ghost to claim, states its reason, discovers its
  source through DataHub, and **declines out loud** when the warehouse cannot satisfy the
  demand.
- SQL validated by execution — `EXPLAIN` plus a sampled read — before anything is called
  solid, with the proof bound into the ghost's resolution history.
- Read-back verified in DataHub: schema, one upstream, three requesters as native Owners,
  full resolution history.
- A real, open pull request the builder agent opened by itself:
  **github.com/Morkeeth/nullspace-dbt/pull/1**
- A public endpoint where **your own agent** can create demand — no clone, no Docker.

Everything above was read back out of a running DataHub. Nothing on the board is replayed
from a file, and the demo data is disclosed at the point of every claim.
