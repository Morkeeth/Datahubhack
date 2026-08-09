# Hackathon retro — Nullspace (Build with DataHub)

**Event:** Build with DataHub: The Agent Hackathon · deadline Mon 10 Aug 2026  
**Repo:** https://github.com/Morkeeth/nullspace  
**Submitted:** 2026-08-09 (evening Paris)  
**This file:** shared retro. Cursor Lane A section below; Claude Lane B appends next.

Detailed Cursor write-up (same substance, more receipts):  
`docs/archive/collab/reviews/retro-cursor-lane-a-2026-08-09.md`

---

## Cursor Lane A — retro (plumbing / catalog-as-database)

*Written 2026-08-09 ~23:30 UTC, after submission. POV: cloud agent on
`cursor/datahub-hack-setup-4c9d`, owning emit/ghosts/builder/client/scripts/infra.*

### One-line verdict

We shipped a **real** ghost→solid loop with DataHub as witness — and spent too much of
the weekend proving claims that should have been gated by one cold stranger run on day one.

### What was strong

| Phase | Why it worked |
|---|---|
| **Concept lock after Join Treaty died** | Oscar killed “feature not product.” Ruling + kill list stopped us from inventing a third idea mid-weekend. |
| **Catalog-as-database (D26)** | Once “local JSON is cache only” was law, every later feature had a place to live (plans, receipts, contracts on the URN). |
| **Law 2 / subtraction proof** | `without-datahub.sh` is the rare hackathon artifact that *fails closed*. Judges and maintainers both respect that. |
| **Lane split + PROTOCOL** | Cursor = trunk plumbing, Claude = agents/board/submission. Handoffs/rulings/STATE/DECISIONS kept three parties from thrashing the same files. |
| **Walk-the-book (D36)** | Highest-signal product moment: refuse unsatisfiable demand out loud, claim the first buildable want. Worth more than another aspect. |
| **Honesty boundaries** | `file://` is not a PR; CTAS disclosed when dbt Fusion can’t run Postgres; RFC argues *against* our own dataset squat. That tone is rare and judge-safe. |
| **Multi-model redteam / audits** | Hostile-judge / stranger / maintainer lenses actually changed the queue (board≠file, fuzzy miss, store mismatch). Not theatre. |
| **Upstream RFC #19022** | Right packaging: RFC first, connector later. Honesty about modelling > rushed ingestion PR. |

### Where we lost time

1. **False lineage accusation (HANDOFF 006)** — hours chasing “lineage never written” that was stale volume + missing `psycopg` on the laptop. Cloud green ≠ laptop green; we paid the tax twice.
2. **D9 / real PR path** — Cursor GitHub App only had `nullspace`, not `nullspace-dbt`. Cloud could not open `https://` PRs; laptop could. We rediscovered this every session.
3. **Structured properties 422** — defs never registered / same-batch with values / ES field-name collision. Ghost loop looked “broken” until customProperties fallback. Should have been day-one smoke: write property → read property.
4. **Environment drift** — unpinned `dbt-postgres` → Fusion alpha → no Postgres adapter → CTAS pretending to be dbt until disclosed. `install-deps` and `requirements.txt` diverged.
5. **Board / store mismatch** (early) — eval wrote one JSON path, board read another → blank aha. Fixed, but it burned the cold-reveal narrative until GraphQL board landed.
6. **Dirty demo graph** — throughput harvest left ~80 ghosts; recording needed `reset` discipline we didn’t automate into the shoot checklist early enough.
7. **Design thrash late** — Darkroom vs Ranked/Stage comps while Oscar already had another idea. Fine as exploration; not fine as a blocking lane near freeze.
8. **Buffered ghost emits vs long-lived MCP** — success returned before GMS flush (`atexit`). Eval passed (one-shot process); real MCP sessions lied. Classic “test shape ≠ prod shape.”

### Process learnings

- **Repo-as-shared-brain works** when STATE is updated every turn and decisions are append-only. It fails when STATE goes stale (stranger-failure #1 still listed after dbt install landed).
- **Lanes need a “cross-lane bug” escape** — false lineage accusation was a coordination failure, not a code failure. Retraction handoffs are good; earlier “verify on both hosts” would be better.
- **One cold-clone machine is sacred.** Oscar’s laptop had hand-repaired Postgres volume, dbt, profiles. Cloud had different truth. The stranger prompt (final Cursor run) should have been **daily**, not final.
- **Done-when must name the witness host.** “Solid on Cursor” ≠ “solid on recording laptop.” Receipts without host are fiction.
- **Multi-model review is cheap insurance** if the output is a ranked fix queue with owners — not a PDF of opinions.
- **Submission package early** (pitch/video/OSS) pulled the product toward the aha; leaving video to the last day is still the main schedule risk.
- **Don’t demo the eval path if the money shot is elsewhere.** `demo.sh` → direct `claim_and_build` skipped walk-the-book until we caught it in audit.

### Improvements for next hackathon

1. **Day-0 stranger script** in CI-ish form: clean clone VM, `install-deps` → `up` → one ghost → solid, with host-named receipt committed.
2. **Pin the toolchain** (`dbt-core<2`, exact DataHub image, Python) in `requirements.txt` *and* `install-deps.sh`; single source of truth.
3. **Smoke matrix on every merge:** SP write, lineage GraphQL, PR URL shape (`https` vs `file`), materialise method (`dbt_run` vs `warehouse_ctas`).
4. **Flush semantics for long-lived MCP** — never rely on `atexit` for demand the board must show live.
5. **Recording runbook owns `reset`** as step 0; refuse to start if open ghost count > N.
6. **GitHub App / token checklist** before any “opens a PR” claim leaves the README.
7. **Keep design exploration off the critical path** after the board has one shipped system (M1).
8. **Archive working notes before submit** (already done) so judges don’t drown in collab debris — keep one `hack.md` + one retro per lane.

### Articles we could write (from this weekend)

| Working title | Angle | Audience |
|---|---|---|
| **Demand-side metadata** | Catalogs map what exists; the valuable signal is what agents asked for and didn’t find | Data platform / DataHub community |
| **The miss is the ticket** | Agent failures as a first-class product surface; why Jira can’t be an upstream | AI infra / MCP |
| **Law 2: subtract the sponsor** | If killing DataHub doesn’t kill your product, you built a sidecar | Hackathon builders / OSS |
| **Walk the book** | Agents that refuse out loud beat agents that “always succeed” | Agent product design |
| **Honesty as a feature** | `file://` ≠ PR; CTAS ≠ dbt; RFC against your own squat | Eng blog / trust |
| **Two hosts, one lie** | Cloud green, laptop red — environment drift as the default hackathon failure mode | Platform eng |
| **Repo as the shared brain** | STATE / DECISIONS / lanes with Cursor + Claude + human | Multi-agent collaboration |
| **Harvest before adoption** | Postgres `relation does not exist` as a demand corpus with zero new instrumentation | Analytics eng |
| **RFC before connector** | How to contribute upstream under hackathon time pressure without drive-by PRs | OSS maintainers / contributors |

### What we’d protect if we only kept three artifacts

1. Ghost → solid with GMS read-back (schema, lineage, owners, resolution history)  
2. Walk-the-book refusal lines  
3. RFC #19022 + Law 2 subtraction script  

Everything else was scaffolding toward those three.

---

## Claude Lane B — retro

*(Claude appends here — still empty as of Cursor’s final-20h pass.)*

---

## Final take (Cursor, post-submit, ~20h left)

**Compare:** Claude’s retro is not in the repo yet, so this is Cursor retro ↔ submission
audit ↔ live re-audit. They agree: engine is real; the unfinished cherry is presentation /
upstream polish.

**Verdict:** Ready to defend the submission. **One cherry left that matters:** make
[datahub#19022](https://github.com/datahub-project/datahub/pull/19022) CI-green via
`docs/oss/datahub-rfc-19022/APPLY.md` (Oscar/Claude — Cursor cannot push that fork).

**Do next (brutal order):**
1. Apply RFC polish → green checks → paste reviewer response  
2. Reset board → cut X clip (`docs/submission/x-clip.md`) using **merged** `nullspace-dbt#5`  
3. Claude fills this Lane B section  

**Do not:** open a second DataHub PR; restyle the board; live-push a PR on camera if
`gh` might fall back to `file://`.

Full plan: `docs/archive/collab/reviews/final-20h-plan.md`

### Shipped in the post-submit pass (Cursor)

- MCP `find_dataset` uses **one** DataHub client + **flushes** ghost emits before return (board no longer waits on process exit)
- `open_demand` / `claim_and_build` hydrate from catalog
- `dbt-core>=1.8,<2` pinned in `requirements.txt` + `install-deps.sh` (no Fusion surprise)
- Order book shows PR link on claimed rows
- `scripts/preflight-demo.sh` + `docs/submission/x-clip.md`
