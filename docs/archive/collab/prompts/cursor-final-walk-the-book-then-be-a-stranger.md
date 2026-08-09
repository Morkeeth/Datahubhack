# PROMPT — Cursor, final run: walk the book, then be a stranger

Paste into Cursor on `cursor/datahub-hack-setup-4c9d`. Last substantive run before freeze
(**Mon 18:00 Paris**). Two things, in order. Do not start the second before the first is
green.

---

## 1. Walk the book — the money shot

Full brief: `docs/collab/handoffs/007-steer-the-builder.md`.

`run_builder_agent()` always claims the highest independent demand and takes no argument.
The book now holds 40 wants harvested from 1,205 real Postgres errors, and its top items —
`churn by cohort` at 19, `net revenue retention by cohort` at 17 — **cannot be built from
this warehouse at all**; no `cohort`, `churn_rate`, `nrr` or `retained_accounts` column
exists in any table. The builder refuses them, correctly, and then picks the same one again
next cycle, forever. `pipeline coverage by rep` at 13 *is* buildable —
`ecommerce.pipeline_performance` has exactly `rep_id`, `pipeline_value`, `quota`,
`coverage_ratio` — and is unreachable behind two permanent refusals.

Make the builder **walk the book in demand order and claim the first want it can actually
satisfy**, printing one refusal line per want it steps over:

```
skipped  'churn by cohort'                 demand 19  no warehouse column for cohort, churn_rate, retained_accounts
skipped  'net revenue retention by cohort' demand 17  no warehouse column for nrr, expansion_mrr
claiming 'pipeline coverage by rep'        demand 13  all 4 fields resolve to ecommerce.pipeline_performance
```

**That output is the most persuasive thing this project can show a judge** — an agent
working a ranked backlog, refusing what it cannot do and saying why, then building what it
can. It is worth more than another feature.

Also add `want: str | None = None` so a caller can steer it, and leave the no-argument
behaviour identical when the top of the book *is* satisfiable.

**Done when:** the watcher (`python -m nullspace.agents.watcher --max-builds 1`) reaches a
real build without being restarted, the ghost goes solid with an `https://` PR, and
`python scripts/agents_return.py --want "pipeline coverage by rep"` shows the blocked
queries returning rows.

## 2. Then be a stranger — on your host, which is the point

You are the only clean machine we have. Everything on Oscar's laptop has been repaired
in place for two days: a stale Postgres volume, a venv missing `psycopg`, `dbt` installed
by hand this afternoon, a `~/.dbt/profiles.yml` written by hand. **None of that is in the
repo, and every one of them silently broke something before it was found.**

So: `git clone` the public repo into a fresh directory on your host, with nothing carried
over, and follow `README.md` **literally** — no charitable substitutions, no "obviously
they meant". Stop at the first thing that does not work and report the exact command and
the exact error. Then keep going and **time it**: minutes from clone to the moment a ghost
goes solid. Anything over five minutes is a defect.

Specifically confirm, because these are the ones I know are shaky:

- Does anything install `dbt`? The README's happy path ends with a ghost going solid, and
  until this afternoon "solid" meant a tag in DataHub with **no physical table anywhere** —
  `information_schema.tables` returned zero rows for it. If `scripts/install-deps.sh` does
  not install `dbt-postgres` and write a profile, a stranger's `solid` is a fiction.
- Does `./scripts/up.sh` produce a warehouse with all seven tables from
  `infra/warehouse/init.sql`? On the laptop it did not, because Postgres only runs its
  init script on an empty volume, and the file had grown since.
- Does `bash scripts/serve.sh` work with no `.venv`?
- Do the two README links resolve for someone not logged in as Oscar?

**Report failures as a list with commands and errors. Do not fix them in the same run** —
tell us first, so we can rule on what is worth changing this close to freeze.

## What not to do

No new features. No refactors. `RULING.md`'s kill list is still dead, and after **12:00
Monday** nothing gets written that is not fixing something a stranger actually hit.

One last thing that is thirty seconds: `AGENTS.md:75` documents a `daemon.json`;
`git ls-files -- daemon.json` returns nothing and no such file is on disk. That is a false
claim in a judged artifact and it breaks our own first rule.
