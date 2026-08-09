# SUBMISSION PACKAGE — Nullspace

Everything a human needs to record, upload and post. Nothing here is a claim the
running system does not produce; every figure was read back on **2026-08-09** from
the live stack and is marked with how it was checked.

---

## 1 · THE LINKS

| | |
|---|---|
| Repo (public, Apache-2.0) | https://github.com/Morkeeth/nullspace |
| The pull request an agent opened and merged | https://github.com/Morkeeth/nullspace-dbt/pull/5 |
| The fulfilment repo it writes into | https://github.com/Morkeeth/nullspace-dbt |
| Upstream contribution (RFC, open) | https://github.com/datahub-project/datahub/pull/19022 |
| Live board | printed by `bash scripts/serve.sh --public` |
| Video | *paste after upload* |

**Track:** the agent-infrastructure / MCP track — Nullspace is agent-to-agent
infrastructure, the requesters are MCP clients, and the builder is an MCP client too.

---

## 2 · THE NUMBERS, AND HOW EACH ONE WAS CHECKED

| Figure | Value | How |
|---|---|---|
| Real Postgres errors harvested | 2,405 log lines | `docker logs` piped to `nullspace.agents.harvest` |
| Requester-want pairs recorded | 1,253 | harvest output, deduped to one per (want, requester) |
| Distinct wants in the catalog | 41 | GraphQL search on platform `nullspace` |
| Unfilled right now | 40 | `/api/order-book` |
| Agents blocked | 1,209 | sum of demand on unfilled wants |
| Built because demand was visible | 1 | the solid asset, read back from DataHub |
| Queries unblocked | 3 of 3 | executed in a READ ONLY transaction |
| Tests | 24 passed | `pytest nullspace/tests` |
| Time from first ask to solid | seconds, printed on the board | `nullspace.resolution` timestamps |

**Disclosed:** requester identities and warehouse rows are demo traffic. The misses
behind them are genuine `relation ... does not exist` errors raised by Postgres.

---

## 3 · THE RECORDING RUN-SHEET

Two terminals and a browser. Nothing here needs typing mid-take except the marked lines.

**Before you start**
```bash
cd ~/Datahubhack-jt
export PATH="$HOME/Datahubhack/.venv/bin:$PATH" \
  DATAHUB_GMS_URL=http://localhost:8080 \
  NULLSPACE_STORE=/tmp/ns-demo.json \
  NULLSPACE_DBT_REPO=$HOME/Datahubhack/dbt_project \
  DBT_PROFILES_DIR=$HOME/.dbt \
  NULLSPACE_DBT_SCHEMA=ecommerce
python -m uvicorn nullspace.board:app --host 127.0.0.1 --port 8790   # terminal 1
```
Board: `http://localhost:8790` · Order book: `http://localhost:8790/order-book`
**Not 8787 — Cursor holds that port.**

| # | Shot | What you do |
|---|---|---|
| 1 | **DataHub's own UI**, `localhost:9002`, `datahub`/`datahub`. Search *monthly recurring revenue by segment*. **No results.** | their catalog, showing an absence |
| 2 | Terminal: `python scripts/moonshot_demo.py` | three separate MCP clients miss, demand 1 → 2 → 3 |
| 3 | Order book in the browser | the strip, the twin combs, **WANTED AND BUILT — NONE** |
| 4 | Back to **DataHub UI**, search again | the ghost is there, tagged `ghost`, requesters as Owners |
| 5 | Terminal: `python -m nullspace.builder` | **the money shot** — it walks 40 wants, prints a refusal line for each one the warehouse cannot satisfy, then claims the one it can |
| 6 | The PR on screen, then merge it | `python -m nullspace.cli finalize --want "monthly recurring revenue by segment"` |
| 7 | Order book again | the built row, schema, upstream, the PR link |
| 8 | **The ending** — `python -m nullspace.console unblocked "monthly recurring revenue by segment"` | three queries that could not run, now run, with real rows |

**Do not record `scripts/demo.sh`** — it calls the build tool directly and skips the
walk-the-book output, which is the best thing the project does.

**Never say "opens a pull request" over a `file://` URL.** If the PR line shows
`file://`, the push failed; say what is on screen.

---

## 4 · SUBMISSION DESCRIPTION — paste as-is

**Nullspace — a catalog is a map of what exists. This makes DataHub the first catalog that also maps what is missing.**

An agent searches the catalog for a table it needs, does not find it, and fails
silently in its own context. That miss is thrown away today — no ticket, no record,
nothing. Nullspace keeps it.

Every miss materialises or increments a **ghost**: a real DataHub dataset URN tagged
`ghost`, carrying a demand counter and edges back to every agent that asked. Three
agents in three separate contexts discover, for the first time, that they wanted the
same thing. When demand crosses a threshold a builder agent walks the book, refuses
out loud what the warehouse cannot satisfy, claims what it can, writes a real dbt
model, and opens a real pull request. On merge the ghost goes solid — real schema,
real lineage, and the requesters become native Owners of the table they caused to
exist. Then the part everyone forgets: **the agents that were blocked stop being
blocked, and none of them had to ask again.**

Demand does not require adoption. Postgres has logged every miss for twenty years —
`ERROR: relation "x" does not exist`, with the statement beside it. We read that log.
2,405 real error lines from this warehouse became 1,253 attributed requests across 41
tables that do not exist, ranked by how many independent agents are waiting.

**Delete DataHub and this does not degrade, it disappears.** A Jira ticket cannot be an
upstream. A Slack thread cannot carry provenance. Three agents' separate failures only
become the same object inside a shared metadata graph — which is why the contribution
goes back upstream as an RFC proposing demand-side metadata as a first-class concept.

Honest boundaries, stated on the page and in the repo: nobody should merge
agent-written SQL unreviewed, and this does not ask you to — the agent's job is to turn
three silent failures into a reviewable two-minute diff. Requester identities and
warehouse rows are disclosed demo traffic; the misses are real.

---

## 5 · THE TWEET

> A catalog tells you what data you have.
>
> Nobody records what your agents asked for and couldn't get — the query fails, the
> agent shrugs, and the signal is gone.
>
> So I made the miss the record. It's a real DataHub entity: a table that doesn't exist
> yet, with a demand counter and every agent that asked.
>
> Three agents want the same missing table → a builder agent walks the backlog, refuses
> what the warehouse can't answer, writes the dbt model for what it can, opens a PR.
> Merge it and the ghost goes solid — schema, lineage, and the three agents as owners of
> the table they caused to exist.
>
> Then the bit I hadn't seen anyone do: the agents that were blocked just… aren't. None
> of them asked again.
>
> No adoption needed either. Postgres has been logging `relation does not exist` for
> twenty years. 2,405 real errors → 41 tables nobody built, ranked by how many agents
> are waiting.
>
> Built for the DataHub agent hackathon. Open source, and the RFC is upstream.
>
> 🔗 github.com/Morkeeth/nullspace

*Alt short version:*

> Your agents are failing at queries you'll never hear about.
>
> Nullspace makes DataHub record the tables that don't exist yet — who asked, how many,
> what they were trying to run. Enough demand and an agent builds it, opens a PR, and the
> blocked queries start working.
>
> 2,405 real Postgres errors → 41 tables nobody built.

---

## 6 · THE DOWNLOAD PACKAGE

```bash
bash scripts/package.sh
```
Writes `dist/nullspace-submission/` with the screenshots, the run-sheet, the
description, the tweet, and a `receipts.json` of every figure above with the command
that produced it.

---

## 7 · KNOWN GAPS — say these before a judge finds them

- The public MCP endpoint **refuses `claim_and_build`** by design: building spends this
  machine's GitHub credentials. Demand is open to everyone; write access is not.
- Cloudflare quick tunnels mint a **new hostname every restart**, so a live URL is only
  live while the terminal is open.
- The harvest corpus is reproducible but **not committed**, so a stranger sees the
  mechanism, not our 41 wants, until they run the seeder themselves.
- `dbt` must be installed for `solid` to mean a real table. `scripts/install-deps.sh`
  installs it; if it fails, the run says solid cannot be trusted.
