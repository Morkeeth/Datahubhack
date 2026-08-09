# HANDOFF 002 — BUILD BRIEF: Half-Life

- **From:** Claude (Opus 5) · 2026-08-08 ~23:0x Paris
- **To:** Cursor cloud build agent
- **Supersedes:** the A/B/C/D question in HANDOFF 001 (see RULING 001 for why)
- **Deadline:** Mon 10 Aug 2026, 17:00 EDT / 23:00 Paris — **~46 hours from this file**

---

## The product, in one paragraph

A data catalog is documentation about a live system, and documentation rots. Every
dataset in DataHub carries claims — this description, this owner, this freshness,
this glossary term — and not one of them is ever re-tested against the data actually
in the warehouse. That was survivable when the reader was a human who could smell a
stale description. The reader is now an agent, which believes the claim and writes
the query. **Half-Life probes every claim in the catalog against the live system and
writes back a verdict — upheld, contradicted, or unverifiable — each carrying the
probe that produced it. Then an agent reads the verdict instead of the claim, and
refuses to act on the contradicted ones.**

The headline artifact is a number: *of N claims in this catalog, M are false.*

---

## The one design move that makes this a product and not a report

**The demo must end with an agent refusing to act, citing a probe.**

A dashboard of rot is a feature. A machine that stops another machine from shipping
a wrong number is infrastructure. If the build runs out of time, cut anything else
before cutting the refusal.

---

## The causal chain (build in this order — it is also the demo order)

1. **Harvest** — pull claims off DataHub entities: dataset + column descriptions,
   owners, tags, glossary assignments, any freshness/SLA statement in properties.
2. **Probe** — each claim type gets a **named, deterministic** probe run against the
   live warehouse. No LLM verdicts. Examples:
   - description names columns that no longer exist → **CONTRADICTED**
   - "source of truth for X" but the table is empty → **CONTRADICTED**
   - freshness claim vs `max(updated_at)` → **UPHELD / CONTRADICTED**
   - owner is a deactivated or activity-free `corpuser` → **UNVERIFIABLE**
   - a claim with no probe available → **UNVERIFIABLE**, never silently upheld
3. **Verdict write-back** — native, on the entity: structured properties (verdict,
   probe name, probe output, timestamp) **plus a tag** (`halflife:contradicted`).
   **Tags render in DataHub's V2 UI** — this is the deliberate fix for the gap that
   made Join Treaty's output invisible on film.
4. **Read-after-write** — prove every mutation by reading it back from DataHub.
5. **The gate** — an agent-facing tool that, before using a dataset, reads its
   verdict and **refuses on CONTRADICTED, quoting the probe output**.

## Reuse, do not rebuild

`app/join_treaty/` already contains a verified spine: evidence gathering → named
gates with stated reasons → native write → read-after-write → idempotency. It is at
**13/13** on `scripts/eval.sh`, which also fails correctly (exit 1) when GMS is
unreachable. **Port that spine. The gates, the receipts and the idempotency logic
transfer almost unchanged** — only the evidence source and the written aspect differ.

---

## Lanes (parallel, one branch each, file ownership stated to avoid collisions)

| Lane | Owns these paths | Done when |
|---|---|---|
| **L1 harvest + probes** | `app/halflife/harvest.py`, `probes/` | ≥4 probe types, each deterministic, each naming itself in its output |
| **L2 verdict write-back** | `app/halflife/write.py` | verdict + tag land natively; DataHub returns both on read-back; rerun adds nothing |
| **L3 the gate** | `app/halflife/gate.py` | an agent asks for a contradicted dataset and **refuses, quoting the probe** |
| **L4 realistic seed** | `infra/warehouse/`, `infra/datahub/` | a catalog with realistic wrong claims **and a README section disclosing it** |
| **L5 eval + stranger path** | `scripts/eval.sh`, `README.md` | eval extended to Half-Life; **PATH bug fixed** (see below); cold run < 3 min |
| **L6 submission** | `docs/submission/` | ≤3-min video script, text description, one real OSS PR to DataHub |

**Critical path is L1 → L2 → L3.** L4/L5/L6 run alongside. **L6 is not optional** —
two of the six judged dimensions (Submission Quality, OSS Bonus) are currently at
**zero**, and they are the cheapest points on the board.

---

## Non-negotiables (five inherited from HANDOFF 001, all still binding, plus one)

1. Real ingested evidence — never self-seeded evidence presented as observed.
2. Realistic volume.
3. Native read-after-write proof; DataHub saying it has it, not our log saying we wrote it.
4. Honest hedged language — "contradicted by probe X", never "wrong".
5. One review surface.
6. **NEW — every headline number discloses its source in the same breath.** If the
   rot figure comes from a seeded catalog, the README and the video say so *next to
   the number*. This is the single biggest risk in the whole build: an undisclosed
   seeded number is a worse version of the faked-evidence tell we are removing.
   `RULING.md`'s Nullspace README is the cautionary case — it claims schema, lineage
   and a mergeable PR, and the running system produces none of the three.

---

## Known defects to fix on the way past (observed 2026-08-08, not guessed)

- **Stranger path is broken at command 1.** `scripts/install-deps.sh` puts
  `join-treaty` in `~/Library/Python/3.12/bin`, which is not on `PATH`, and prints
  `datahub: command not found` twice. Anyone following the README fails immediately.
  This breaks the "repo with clear setup instructions" route to submission
  requirement 2. **Fix in L5.**
- **`AGENTS.md:64` describes a `daemon.json` that does not exist** — not tracked by
  git, not on disk (`git ls-files -- daemon.json` → no output). Either commit it or
  delete the guidance; as written it cannot be followed.
- **Host-side, for your notes (not repo defects):** `docker compose` was not
  installed on the operator's machine at all (colima, no plugin), and lima's
  port-forwarder had been stale since 19 Jul — GMS answered 200 inside the container
  while refusing connections from the host. Together these cost about an hour before
  anything could be tested. The compose stack itself came up clean once both were
  fixed: ingestion reported *"Pipeline finished successfully"*, 52 events, GMS v1.7.0.

---

## The eval, before any new code

Extend `scripts/eval.sh`. It must assert, with DataHub as the witness:

- a cold run on a fresh stack produces verdicts **DataHub returns on read-back**
- running twice produces **no duplicate** verdict
- **every UNVERIFIABLE states why no probe applied** — silence is not a verdict
- **the gate actually refuses**, and the refusal quotes the probe output
- a stranger reaches the refusal **in under 3 minutes from the README**

Prove the eval can fail before trusting it passing. The current one was verified
both ways.

---

## What is already safe

- `43bfa03` — Apache-2.0 LICENSE **pushed to main**. GitHub previously reported *no
  licence at all*, which can void the entry on its own.
- `747eb1b` — the uncommitted Nullspace tree parked on `park/nullspace-2026-08-08`.
- `~/backups/git-bundles/datahubhack-dbt_project-2026-08-08.bundle` — verified.
- `cdc2f98` — `scripts/eval.sh`, 13/13 live, exit 1 when GMS is down.

## Open for Oscar, not for the build agent

The name. **Half-Life** is a working title chosen for retell, not a ruling.
