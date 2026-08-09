# PROMPT — Cursor, Lane A: the builder has to actually think

Paste into Cursor on `cursor/datahub-hack-setup-4c9d`. This replaces the remaining scope
in `cursor-lane-a-close-the-gap.md` — checks 1–4 there are passed, check 5 rolls in here.

---

## The thing nobody has said out loud yet

We call it a **builder agent**. Here is every line of SQL it has ever written, pulled
from the pull request it opened an hour ago:

```sql
select
    "segment",
    "mrr",
    "month",
    "churned_mrr"
from {{ source('warehouse_source', 'revenue_events') }}
```

The want was **"monthly recurring revenue by segment."** That is a `GROUP BY`. There is no
`GROUP BY`. There is no `SUM`. There is no join. It selected four columns out of one table
and called it fulfilment — and the table already had those four columns, so the model
produces *nothing that did not already exist*.

A judge who opens our PR — and we are pointing them straight at it — reads eleven lines of
passthrough `SELECT` and correctly concludes the agent is a **string template with a
decision log stapled to the front**. Everything else we built is real: the MCP clients,
the demand convergence, the schema derived from contracts, the lineage, the SQL-execution
gate. All of it is undermined by those eleven lines, because they are the only artefact
the judge can read without running anything.

**Fix the one artefact the judge can read.**

---

**Objective**

A judge opens `Morkeeth/nullspace-dbt` and reads a dbt model they cannot distinguish from
one a competent analytics engineer wrote — the right grain, a real aggregation, a join
when the demanded fields live in more than one table — and a PR body that explains *why*
that grain, citing the three agents' own queries. And when the agent could not do it well,
it says so out loud instead of shipping a passthrough with a confident commit message.

**Context**

- Branch `cursor/datahub-hack-setup-4c9d`. Lane A files only — read `docs/collab/LANES.md`.
- **Read `handoffs/006-to-cursor-retraction-and-two-bugs.md` first.** Your lineage code is
  correct; my earlier accusation was wrong and is retracted there. Do not rewrite `emit.py`.
- The loop is live end to end on Oscar's laptop and the PR is real:
  `https://github.com/Morkeeth/nullspace-dbt/pull/1`, state OPEN.
- The warehouse now has all seven tables from `infra/warehouse/init.sql`
  (`customers`, `products`, `orders`, `order_items`, `trials`, `revenue_events`,
  `pipeline_performance`) plus the `customer_order_summary` view. **More than one table
  means a real builder can be asked for something that needs a join** — for example
  trial-to-paid conversion by cohort genuinely spans `trials` and `revenue_events`.
- `psycopg` is installed and the SQL-execution gate works: `EXPLAIN` plus a sampled read.
  That gate is your safety net — it means you can let the builder attempt something
  ambitious, because the warehouse refuses anything that does not run.
- Deadline Mon 10 Aug 23:00 Paris. **Freeze 18:00.**

**Constraints**

- **The builder may fail. It may not fake.** If it cannot produce a model that both runs
  and satisfies the demanded grain, it declines and says exactly what defeated it. A
  declined ghost on the board is a stronger artefact than a passthrough that pretends.
- **Disclose the reasoning engine at the point of the claim.** If an LLM wrote the SQL,
  the PR body, the resolution history and the board all say which model. If the
  deterministic path wrote it, they say that instead. Never let the two be
  indistinguishable — that is the `dryRun=true` mistake wearing a new hat.
- No API key is set in the environment. `claude` is on PATH. Design for **three tiers**:
  `ANTHROPIC_API_KEY` if present → the `claude` CLI if present → deterministic SQL
  generation. A cold-cloning judge with neither still gets a working demo, and the board
  tells them which tier ran. Never crash because a key is missing.
- Never `git add -A` (`dbt_project/` carries a nested `.git`).
- **Every witness row names the host it was witnessed on.** Your night-run receipts were
  true in your sandbox and false on the laptop that records the video. That is the single
  most expensive thing that happened in this project.

**Done when — five checks, each one a command**

1. **The model has a grain.** Ask for *monthly recurring revenue by segment*; the
   generated model contains a real aggregation over `revenue_events` (`GROUP BY` on the
   demanded dimensions, `SUM` on the measures) and `dbt build` succeeds against the live
   warehouse. Paste the model and the dbt output.
2. **The builder can join.** Ask for *trial-to-paid conversion by cohort* — fields that do
   not live in one table. The builder discovers both sources through DataHub, writes the
   join, and the resulting solid asset carries **two upstreams**, verified by
   `lineage(UPSTREAM).total == 2`. If it cannot, it declines with the exact reason and
   the ghost stays hollow. Either outcome passes this check. **A passthrough does not.**
3. **The PR body argues.** The pull request explains the grain it chose and quotes the
   three requesters' own SQL as the evidence for it. Paste the PR URL.
4. **BUG-1 fixed** (`builder.py:389`) — a refusal prints its reason instead of raising
   `KeyError: 'urn'`. Prove it by forcing a refusal and showing the clean output.
5. **`nullspace reset` exists** and refuses to touch any URN that is not
   `urn:li:dataPlatform:nullspace`. Prove the guard by pointing it at a warehouse URN and
   watching it decline. (I deleted a real warehouse entity doing this by hand this
   morning; the guard is not theoretical.)

**Stretch, only if 1–5 are done and it is before 14:00 Paris Monday — the subtraction proof**

`scripts/without-datahub.sh`: run the same three agents with GMS unreachable. Each fails
in its own context, none of them can see the other two, and there is no namespace in which
the thing they all want can be named. Print the three isolated failures side by side. This
is the last beat of the video and it is the only moment that *proves* Law 2 rather than
asserting it — deleting DataHub does not degrade Nullspace, it deletes it.

**Start by**

Run the current builder against *trial-to-paid conversion by cohort* — a want that needs a
join — and paste what it generates, before writing any code. If it emits a passthrough, or
declines because it only knows how to look at one table, say so plainly. That output is the
brief.
