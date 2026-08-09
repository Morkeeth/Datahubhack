# HANDOFF 007 → Cursor — the builder cannot be told what to build

- **From:** Claude (Opus 5), terminal · 2026-08-09 ~15:5x Paris
- **To:** Lane A, `cursor/datahub-hack-setup-4c9d`
- **Found by:** building the watcher (`nullspace/agents/watcher.py`, Lane B, pushed)

---

## The defect

`run_builder_agent()` takes no arguments and always claims **the highest independent
demand**. That is the right default and the wrong only-option.

The order book now holds 40 open wants harvested from 1,205 real Postgres errors. The
top of that book — `churn by cohort` at demand 19, `net revenue retention by cohort` at
17 — **cannot be built from this warehouse at all.** There is no `cohort`, no
`churn_rate`, no `retained_accounts` column in any table. The builder is right to refuse.

But it refuses, and then next cycle it picks the same want again, and refuses again,
forever. A watcher cannot advance past it, because there is no way to say *"not that one,
try the next"*. Meanwhile `pipeline coverage by rep` at demand 13 **is** buildable —
`ecommerce.pipeline_performance` has exactly `rep_id`, `pipeline_value`, `quota`,
`coverage_ratio` — and is unreachable behind two permanently-refusing wants.

**This is not a watcher bug. It is the shape of the builder**, and it will bite in the
demo the moment anyone leaves it running.

## What I did in the meantime

The watcher detects the repeated refusal of the same want and **stops**, saying why and
pointing here. It does not spin. A watcher that spins on one refusal is indistinguishable
from one that is working, and I would rather it stop and name the gap.

## The fix — small, and yours

```python
async def run_builder_agent(want: str | None = None) -> dict[str, Any]:
```

- `want=None` keeps today's behaviour exactly: pick the highest independent demand.
- `want="…"` claims that specific ghost, and refuses with a stated reason if it is not at
  threshold, already solid, or unknown.

Then, the part that actually matters:

**`open_demand` should be skippable.** Either the builder accepts `skip: list[str]`, or —
better, and more honest as a product — the builder **walks the book in demand order and
claims the first one it can actually satisfy**, printing a one-line refusal for each one
it steps over. That turns a stuck loop into the most persuasive output this project has:

```
skipped 'churn by cohort'                 demand 19  no warehouse column for cohort, churn_rate, retained_accounts
skipped 'net revenue retention by cohort' demand 17  no warehouse column for nrr, expansion_mrr
claiming 'pipeline coverage by rep'       demand 13  all 4 fields resolve to ecommerce.pipeline_performance
```

A judge reading that sees an agent with judgement, working a ranked backlog, refusing what
it cannot do and saying why. That is a much stronger frame than one lucky build.

## Done when

1. `run_builder_agent(want=...)` claims that want, or refuses with a stated reason.
2. Run with no argument against the current book: it steps over the unsatisfiable top and
   claims `pipeline coverage by rep`, printing one refusal line per skip.
3. The ghost goes solid with a real PR, and `scripts/agents_return.py --want "pipeline
   coverage by rep"` shows the blocked queries running.
4. No behaviour change when the top of the book *is* satisfiable.

## Two smaller things, both yours

- **Write throughput.** Harvesting 629 requester-want pairs took over ten minutes and my
  scale run was cut off at 395 — roughly a second per DataHub write. At a real warehouse's
  volume this path is unusable. Batch the emits. **Done when 629 pairs land in under 60s.**
- **`AGENTS.md:75`** documents a `daemon.json`; `git ls-files -- daemon.json` returns
  nothing and there is no such file on disk. That is a false claim in a judged artifact and
  it breaks our own non-negotiable #1.

## Not yours, so you do not have to worry about it

`dbt` had never been run — the model merged this morning existed only as metadata, with no
physical relation in Postgres (`information_schema.tables` returned zero rows for it).
Installed `dbt-postgres`, wrote the profile, built it; the requesters' queries now return
real rows. Worth knowing because it means **`solid` in DataHub did not imply the table
exists**, and if you want a guard in `builder.py` that refuses to tag `solid` until a row
comes back, that would make today's failure impossible to repeat.
