# STATE — mission control (read this first)

> Every witness row names the **host** it was witnessed on and the command that
> printed it. Night-run receipts from another host are not reused as truth here.

- **Last updated:** 2026-08-09 08:05 UTC by Cursor Lane A (`bc-9950b172`)
- **Host:** `cursor` (Cloud Agent VM)
- **Phase:** **Builder thinks (grain + join); BUG-1/BUG-2 fixed. Lineage emit not rewritten (HANDOFF 006 retraction).**
- **Deadline:** Mon 10 Aug 2026 · **Freeze 18:00 Paris**
- **Worker branch:** `cursor/datahub-hack-setup-4c9d`
- **Briefs:** HANDOFF 006 + `prompts/cursor-lane-a-the-builder-must-think.md`

## You are here

HANDOFF 006 retracted the “lineage never written” accusation. **Do not rewrite
`emit.py`.** On host `cursor`, lineage read-back still works for solids created here.

The builder no longer emits passthrough `SELECT` lists. The deterministic tier
writes real `GROUP BY` / `SUM` / `COUNT` grains and multi-table joins when a join
key exists; otherwise it **declines** with the exact shortfall (never a cartesian
product). Generation tier is disclosed: `ANTHROPIC_API_KEY` → `claude` CLI →
`deterministic` (this host: **deterministic**; no API key, no `claude` on PATH).

## Baseline before the fix (host `cursor`, required by the prompt)

Command: call current `generate_model_sql` for trial-to-paid fields →

```sql
select
    "cohort_id",
    "trials",
    "conversions",
    "trial_to_paid_rate"
from {{ source('warehouse_source', 'trials') }}
```

That is a passthrough of columns that are not even physical on `trials`. Said
plainly: the agent was a string template.

## HANDOFF 006 / “builder must think” checks

| # | Check | Status | Host | Command / proof |
|---|---|---|---|---|
| 1 | MRR model has grain (`GROUP BY` + `SUM`) | ✅ | `cursor` | Planner + `validate_model_sql` → `explain_node=Aggregate`, SQL has `sum("mrr")` / `group by segment, month` |
| 2 | Join → `lineage(UPSTREAM).total ≥ 2` **or** honest decline | ✅ | `cursor` | Join want solidified: GraphQL `lineage.total=3` (customers, orders, order_items). Spanning `cohort_id`+`mrr` without a key → declined with “shortfall is 1 join key”. |
| 3 | PR body argues grain + quotes requester SQL | 🟡 | code ✅ / remote 🔴 | `SqlPlan.pr_body` generated. Push to `nullspace-dbt` still 403 for `cursor[bot]` (App install = only `Morkeeth/nullspace`). Existing OPEN PR: https://github.com/Morkeeth/nullspace-dbt/pull/1 (opened on Oscar’s laptop; still carries pre-think passthrough SQL until a push lands). |
| 4 | BUG-1 refusal prints reason (no `KeyError: urn`) | ✅ | `cursor` | `_write_review_receipt` on `{"status":"declined"}` → receipt with `"refusal"`; no traceback |
| 5 | `nullspace reset` refuses non-nullspace URNs | ✅ | `cursor` | `DataHubClient.hard_delete_urn(<postgres trials urn>)` → `ValueError: reset refused: … non-nullspace` |
| 5b | Merge → solid | 🔴 | — | Blocked on write to `nullspace-dbt` from this host. Path ready: `python3 -m nullspace.cli finalize --want "…"`. Oscar laptop already has OPEN PR #1 for check 4 of the prior prompt. |

## Live witness (host `cursor`, 2026-08-09)

**Asset:** `ghost_orders_by_customer_country_1786262567_b26872c5`

| Claim | Command | Returned |
|---|---|---|
| generation tier | planner print | `deterministic` |
| SQL grain | model text | `group by c.country_code` + `count`/`sum` over customers⨝orders⨝order_items |
| GraphQL lineage | `dataset.lineage(UPSTREAM).total` | **3** |
| schema | GraphQL `schemaMetadata.fields` | `country_code`, `order_count`, `lifetime_value` |
| MRR grain SQL | planner for “monthly recurring revenue by segment” | `sum("mrr")… group by segment, month`; warehouse `EXPLAIN` → `Aggregate` |
| trial-to-paid SQL | planner | `count(*)… group by cohort_id` (not passthrough) |
| reset guard | `hard_delete_urn(postgres trials)` | refused |

## Next actions

- **Oscar:** add `Morkeeth/nullspace-dbt` to the Cursor GitHub App install (or run builder on the laptop where `gh` is `Morkeeth`) so a **new** PR carries the grain SQL + arguing body; then merge for check 5b.
- **Claude Lane B:** GraphQL board + `register_query` on judged path (multimodel 3/3 / 2/3).
- **Cursor:** stop rewriting lineage; keep disclosing generation tier.

## Canonical docs

- HANDOFF 006: `docs/collab/handoffs/006-to-cursor-retraction-and-two-bugs.md`
- Prompt: `docs/collab/prompts/cursor-lane-a-the-builder-must-think.md`
- Multimodel: `docs/collab/reviews/multimodel-2026-08-09.md`
