# PROMPT — Cursor, long run: the catalog is the database

Paste into a Cursor cloud agent on `cursor/datahub-hack-setup-4c9d`. This is a long,
autonomous run — hours, not one edit. Work down the checks in order and do not stop at the
first one that is hard.

---

## The sentence that has to stop being true

Weapon 3 of the red team, the maintainer lens, landed this and it is still open:

> **"Ghosts are squatted `Dataset` entities and their lifecycle is a JSON blob in
> `datasetProperties.customProperties` — key-value in a costume, not an extension."**
> And its second half (R5b): *"contracts and the demand board live in `/tmp` sidecars
> DataHub never sees."*

We tell judges the catalog is load-bearing. Right now the catalog is a **display surface**
and the truth lives in `/tmp/nullspace-ghosts.json` and `/tmp/nullspace-contracts.json`.
A DataHub maintainer works this out in about ninety seconds, and when they do, every other
claim we make gets re-read in that light.

The fix is not a better README paragraph. It is to make it **false**.

---

**Objective**

Delete every file Nullspace owns on local disk, mid-demo, and have the product keep
working — because the demand, the requesters, the registered query contracts, the
resolution history and the state machine all live in DataHub, and the local files were
never anything more than a cache.

That is a thirty-second moment in a video, an unanswerable reply in the Q&A, and the
difference between "built on DataHub" and "built **into** DataHub".

**Context**

- Branch `cursor/datahub-hack-setup-4c9d`. Lane A only — `docs/collab/LANES.md`.
- Lane B has already moved **the board** to GraphQL (red-team R1, 3/3, now closed): every
  field it renders is a read-back, and with GMS down it reports the catalog as unreachable
  and shows nothing. **The board is no longer the weak link — the writer is.**
- Your grain planner works: `sum(mrr), sum(churned_mrr) … group by segment, month`,
  `EXPLAIN` → `Aggregate`, tier `claude-cli`, disclosed in the model header.
- **The 403 is gone.** `Morkeeth/nullspace-dbt#1` now carries the grain SQL and a PR body
  that argues its own grain from the three requesters' registered queries. It was pushed
  from the laptop with Oscar's `gh`. Do not try to re-push from the cloud agent; if you
  need a new PR, hand it back in `STATE.md` and Lane B will push it.
- Freeze **Mon 18:00 Paris**. This run has roughly a day.

**Constraints**

- **Never invent a DataHub feature.** If a real PDL aspect cannot be registered against a
  stock v1.7.0 GMS in the time available, say so with the command that proved it, and take
  the strongest legal alternative — a structured property, a first-class `dataProduct`,
  a proper `Assertion`, a real `institutionalMemory` link. Read what DataHub actually
  supports; do not guess and do not fake.
- **Local files may exist as a cache. They may never be the source of truth.** Every read
  path must be able to answer from GMS alone.
- A witness row names the **host** it was witnessed on and the command that printed it.
  Your night-run receipts were true in your sandbox and false on the laptop that records
  the video; that mistake has already cost this project hours.
- Never `git add -A` — `dbt_project/` carries a nested `.git`.
- Do not touch Lane B files: `mcp_server.py`, `agents/**`, `board.py`, `static/**`,
  `docs/submission/**`, `docs/collab/{handoffs,rulings,prompts}/**`.

**Done when — work these in order, each one is a command**

1. **Rehydrate from the graph.** `nullspace hydrate` (or equivalent) rebuilds the entire
   local store from DataHub alone. Prove it: `rm -f /tmp/nullspace-*.json`, run it, and
   `nullspace dump` returns every ghost with its demand, requesters, state and full
   resolution history intact.
2. **The state machine survives the deletion mid-flight.** Take a ghost to `claimed`,
   delete the local files, and let the builder finish and solidify anyway. Paste the run.
3. **Contracts live in the catalog.** `register_query` writes each requester's declared
   query and fields into DataHub against the ghost URN — as a real aspect if one fits, or
   the closest first-class construct if not, with the choice justified in one sentence.
   `contract_status` answers from GMS with the sidecar deleted.
4. **Stop squatting, or defend it in writing.** Either the ghost stops being a plain
   `Dataset` with properties bolted on, **or** `docs/design/why-a-dataset-urn.md` argues in
   under 400 words why a demand-side entity *should* be a dataset URN — searchable,
   ownable, lineage-bearing from the moment it is wanted — and that document becomes the
   spine of the upstream RFC. **A judged maintainer must find one or the other.**
5. **Merge closes the loop.** Merge `nullspace-dbt#1`, run `nullspace finalize`, and show
   DataHub returning the ghost as `solid` with schema, one upstream and three native
   Owners — *after* the merge, not before, read back with the command shown.
6. **`without-datahub.sh` becomes an acceptance test, not a script.** It asserts: three
   refusals, zero ghosts written, the board reporting the catalog unreachable, and it
   **exits non-zero if any of that silently succeeds**. Prove it can fail.
7. **The eval is rerunnable and cold-safe** (red team R8): exact-want matching rather than
   `WANT.split()[0]`, `--cold` performs a reset first, and a `Ctrl-C` halfway through does
   not corrupt receipts. Run it twice in a row on a warm stack and show both passes.

**Stretch, only after 1–7 — the one that would actually impress a maintainer**

Emit Nullspace's demand as a **DataHub ingestion source**, so demand can be ingested by a
stock recipe the way any other source is. If that lands, the upstream RFC stops being a
proposal and becomes a connector with a working implementation behind it.

**Start by** running check 1's deletion on your own host, before writing any code, and
pasting exactly what breaks. That output is the map for everything above it.
