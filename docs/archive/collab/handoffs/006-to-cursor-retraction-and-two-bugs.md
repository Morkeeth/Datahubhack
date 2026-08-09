# HANDOFF 006 → Cursor — one retraction, two real bugs, and the ending is live

- **From:** Claude (Opus 5), terminal · 2026-08-09 ~10:0x Paris
- **To:** Cursor, Lane A, branch `cursor/datahub-hack-setup-4c9d`
- **Read before you act on:** `handoffs/005-final-38-hours.md` §"The review that triggered this file"

---

## 1. RETRACTION — your lineage code is correct. Do not rewrite it.

HANDOFF 005 said the `upstreamLineage` aspect *"was never written"* and told you to go
fix it. **That was wrong about the cause and it would have cost you hours in the wrong
file.** Your emit path works. I have now watched it write, and read it back:

```
GET /aspects/<ghost-urn>?aspect=upstreamLineage&version=0   → 200
  upstreams[0].dataset = urn:li:dataset:(urn:li:dataPlatform:postgres,
    local-warehouse.warehouse.ecommerce.revenue_events,DEV)   type TRANSFORMED
GraphQL lineage(UPSTREAM).total = 1
GraphQL schemaMetadata.fields  = segment, mrr, month, churned_mrr
GraphQL ownership.owners       = 3
```

**What was actually broken was Oscar's laptop, in two places**, and both would have made
your own receipts unreproducible here no matter how good the code was:

1. **The Postgres volume was stale.** `infra/warehouse/init.sql` grew `trials`,
   `revenue_events` and `pipeline_performance` *after* this machine's warehouse first
   booted, and a Postgres entrypoint script only runs on an empty data directory. The
   running warehouse had four tables; `init.sql` declares seven. So the builder could
   never find a source covering the demanded fields and honestly declined every time.
   Repaired by replaying `init.sql` into the live container and re-running
   `metadata-ingestion` (73 events, "Pipeline finished successfully").
2. **`psycopg` was not installed in `~/Datahubhack/.venv`.** Your new SQL-validation gate
   imports it, so validation raised `ModuleNotFoundError`, the build was refused, and the
   whole beat died. `scripts/install-deps.sh:23` already installs `psycopg[binary]` —
   the script is right; that venv predates the line. **The stranger path was never
   broken. Only the returning user was.**

The lesson for both of us, and it is the same rule as before: **your night-run receipts
were true in your cloud sandbox and false on the machine the video gets recorded on.**
A witness row needs to name the host it was witnessed on, not just the command.

## 2. THE ENDING IS LIVE — `pr_url` is no longer `file://`

D9 landed (see 005 §D9). With `Morkeeth/nullspace-dbt` public and the local
`dbt_project` pointed at it, **the builder agent opened a real pull request on its own,
with no code change from either of us**:

**https://github.com/Morkeeth/nullspace-dbt/pull/1** — `gh pr view --json state` → **OPEN**
· title *"feat(nullspace): solidify monthly recurring revenue by segment"* · 2 files,
+17 (`models/ghost_monthly_recurring_revenue_by_segment_0d3a3d17.sql`, `models/sources.yml`).

Your check 4 in the Lane A prompt is **passed**. What remains is check 5: **merge that PR
and prove the ghost flips solid off the merge**, observed, not assumed.

## 3. Two real bugs, both yours, both small

### BUG-1 · `builder.py:389` — a refusal crashes instead of explaining itself
`_write_review_receipt()` does `DataHubClient().solid_witness(str(result["urn"]))`, but on
any refusal `claim_and_build` returns no `urn`, so it raises `KeyError: 'urn'` and buries
the honest reason under a `TaskGroup` traceback. Observed verbatim:

```
File "nullspace/builder.py", line 526, in run_builder_agent
    built["review_receipt"] = _write_review_receipt(...)
File "nullspace/builder.py", line 389, in _write_review_receipt
    witness = DataHubClient().solid_witness(str(result["urn"]))
KeyError: 'urn'
```

The reason it was hiding was good and should have been the whole output:
*"build refused: generated SQL failed warehouse validation; shortfall is 1 executable
model; ModuleNotFoundError: No module named 'psycopg'"*.

**This breaks non-negotiable #3 — every abstention states its reason.** Guard the receipt
on `result.get("status") == "solid"` (or on the presence of `urn`) and print the refusal
as the result. A judge who sees a Python traceback stops watching.

### BUG-2 · `nullspace reset` still does not exist
Slice 0c is still open, and it is now the difference between a clean take and a ruined
one. Rerunning the demo with an already-solid asset makes all three agents **find** the
table, so demand never accrues and the board stays empty — the exact "second run finds
yesterday's asset" defect in `STATE.md`. I cleared it by hand with
`DELETE /openapi/v3/entity/dataset/<urn>` over the seven stale ghosts, filtered to
`dataPlatform:nullspace`.

**Filter on the platform, not on a search for the word "nullspace"** — I did the naive
version first and deleted a real warehouse entity, which had to be restored by
re-ingesting. Make `reset` refuse to touch anything that is not
`urn:li:dataPlatform:nullspace`.

## 4. What I am doing, so we do not collide

Lane B only: the board is rebuilt and pushed (`claude/nullspace-agent-layer`,
`nullspace/static/board.html`) — M1 Darkroom, verified at 1440px and 390px against real
data with both states on screen. Next for me: the OSS PR to `datahub-project/datahub`
(`Morkeeth/datahub` fork now exists), the ≤3-min video, and making
`scripts/eval-nullspace.sh` pass twice in a row on a cold stack.

**I will not touch** `builder.py`, `emit.py`, `client.py`, `persist.py`, `ghosts.py`,
`urns.py`, `config.py`, `cli.py`, `README.md`, `compose.yaml`, `infra/`, `AGENTS.md`,
`STATE.md`, `DECISIONS.md`.

**One thing I need from you in `STATE.md`:** it currently carries a witness table whose
rows do not reproduce on this machine. Re-earn it or delete it. And
`AGENTS.md:75` describes a `daemon.json` that `git ls-files -- daemon.json` says has
never existed in this repo — that is a false claim in a judged artifact.

**Freeze is Mon 18:00 Paris, not 23:00.**
