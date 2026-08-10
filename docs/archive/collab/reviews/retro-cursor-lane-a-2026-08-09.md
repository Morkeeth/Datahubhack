# Retro — Cursor Lane A (Nullspace)

- **When:** 2026-08-09, after submission  
- **Who:** Cursor cloud agent, branch `cursor/datahub-hack-setup-4c9d`  
- **Lane:** A — plumbing (`builder`, `emit`, `client`, `ghosts`, `scripts/up|demo`, compose, infra, STATE/DECISIONS)  
- **Shared summary:** repo-root [`hack.md`](../../../../hack.md) (Claude appends Lane B there)

This is the full Cursor POV. Prefer receipts over vibes. Host for most witnesses: Cursor
cloud VM unless named otherwise.

---

## 1 · Arc of the weekend (as Lane A lived it)

| Beat | What happened | Outcome |
|---|---|---|
| Join Treaty substrate | Real Compose DataHub + warehouse + ingestion | Kept as spine after product kill |
| Product kill → Nullspace | Oscar: feature ≠ product; Half-Life killed | Concept locked in rulings; kill list held |
| Native solid assets | Schema, lineage SDK path, owners, tags | D10/D14/D20 — read-back became religion |
| D9 PR path | `nullspace-dbt` public; App install shortfall | Cloud = `file://`; laptop = real PR |
| Catalog is the database | Hydrate, contracts, finalize, plans/receipts on URN | D26–D31 — local JSON demoted to cache |
| Law 2 | Refuse when GMS gone; `without-datahub.sh` | Hard constraint made testable |
| First-class demand attempt | Structured props + Queries + webhook | SP 422 → customProperties fallback (D35) |
| Scale / harvest | Lane B harvested errors; Lane A batch emits | 629 pairs &lt;60s (D32); dirty board risk |
| Walk the book | Skip unsatisfiable, claim first buildable | D36 — money shot for video |
| Stranger + submission audit | Cold clone report; multi-model SHIP WITH GAPS | Recording checklist, not more features |
| OSS cherry | Package RFC #19022 polish; hand to Claude | Connector deferred (correct) |

---

## 2 · Phases that were strong

### 2.1 Concept discipline
After Join Treaty and Half-Life died, we did **not** invent a third product. `RULING.md`
kill list + DECISIONS append-only stopped silent reopening. That alone saved a day.

### 2.2 Witness culture
“Report what DataHub returned, not what we sent” forced:
- `_verify_solid_witness`
- GraphQL lineage `total ≥ 1` (not stock `/aspects` NPE)
- board → GraphQL (Lane B) after multimodel ranked the file-sidecar as 3/3 kill

### 2.3 Collaboration machinery
PROTOCOL + LANES + STATE + numbered handoffs let Cursor cloud + Claude terminal + Oscar
share one brain. Merge rule (“Claude rebases onto Cursor”) reduced branch wars.

### 2.4 Product moments that survive retelling
1. **Miss → ghost → demand N** as a real dataset URN  
2. **Walk-the-book** skip lines (churn/NRR) → claim pipeline coverage  
3. **Agents return** — blocked SQL runs after solid  
4. **Law 2** — kill DataHub, product gone  
5. **RFC honesty** — argue against our own squat  

### 2.5 Late honesty over late features
Submission audit + REVIEW-NOTES preferred “don’t say dbt/PR unless this take shows it”
over shipping Ranked-book UI. Right call at freeze.

---

## 3 · Where we lost time (ranked)

| Rank | Loss | Cost | Root |
|---|---|---|---|
| 1 | Lineage “never written” false alarm | Hours across hosts | Laptop stale Postgres + missing deps; cloud already green |
| 2 | Real GitHub PR from cloud | Recurring rediscovery | App install list = `nullspace` only (D18) |
| 3 | Structured property 422 | Blocked all ghosts until fallback | Defs not registered / same-batch / ES name collision |
| 4 | dbt Fusion surprise | Solid ≠ dbt on stranger path | Unpinned `dbt-postgres` → `dbt-core` 2.0a5 |
| 5 | Board vs store / early file board | Blank cold reveal | Two JSON paths; board not GraphQL yet |
| 6 | Harvest pollution | Recording prep | No auto-reset in shoot path |
| 7 | MCP buffer vs eval shape | Hidden live bug | `atexit` flush; one-shot eval masks it |
| 8 | Design options near freeze | Attention | Comps useful; shipping them was not the ask |

**Pattern:** almost every big loss was **environment asymmetry** or **claim ahead of
witness**, not “we don’t know what to build.”

---

## 4 · Process learnings

1. **STATE without hostnames is a rumor.** Night receipts from another machine must not
   re-enter as truth (we wrote the banner; we still violated it under pressure).
2. **Stranger cadence beats stranger finale.** Final-walk-the-book-then-be-a-stranger
   found install/dbt/profile gaps that had been “fixed by hand” on the laptop for days.
3. **Lanes need a joint incident format.** HANDOFF 006 retraction was correct but late.
   A shared “repro on host X / host Y” template would have cut the lineage thrash.
4. **Multi-model review works when it produces owners.** Multimodel table → build queue
   beat freeform debate. Submission audit → recording checklist beat more features.
5. **Eval green ≠ session green.** Long-lived MCP + buffered emits is the cautionary tale.
6. **Submission-is-the-product was the right Lane B brief** — Lane A felt it as pull toward
   walk-the-book and honest boundaries rather than more aspects.
7. **Append-only decisions are gold** until someone edits STATE without superseding
   DECISIONS (stranger-failure staleness). Treat STATE like a dashboard, DECISIONS like law.

---

## 5 · Improvements (actionable)

### Next hackathon — operating system
- [ ] Day-0 `scripts/stranger.sh` (clean dir, install, up, one solid, host receipt → `examples/`)
- [ ] Single dependency lock: `requirements.txt` owns versions; `install-deps.sh` only invokes it
- [ ] Merge smoke: SP round-trip, lineage GraphQL, PR URL class, materialise method
- [ ] `NULLSPACE_REQUIRE_HTTPS_PR=1` for recording hosts
- [ ] Demo preflight fails if `counts.ghost > 20` without explicit `--i-know`
- [ ] MCP: flush ghost batch on every tool return, not `atexit`

### This product — if continued
- [ ] Finish RFC #19022 CI green (handed to Claude)
- [ ] Connector PR **after** RFC shape discussion — implement `demand` entity, not squat
- [ ] Fix long-lived MCP visibility (buffer flush)
- [ ] Pin dbt-core&lt;2 everywhere strangers land
- [ ] Commit or drop harvest corpus numbers in README

### Collaboration
- [ ] Claude retro section in `hack.md`
- [ ] One postmortem meeting: pick top 3 process changes only (don’t boil the ocean)

---

## 6 · Article / essay seeds

Detailed pitches for later writing. Star = highest leverage from *this* weekend’s scars.

1. ★ **Demand-side metadata** — category essay; RFC #19022 as the spine; Nullspace as
   existence proof, not the proposed shape.
2. ★ **Subtract the platform** — Law 2 as a design test for “sponsor-native” hackathon work
   and for vendor lock-in theatre.
3. ★ **Walk the book** — why ranked refusal is more persuasive than autonomous success porn.
4. **Two greens, one lie** — cloud vs laptop drift; how to structure dual-host witness.
5. **The miss corpus** — harvesting `relation does not exist` / query logs before adoption.
6. **Repo as shared brain** — Cursor ↔ Claude ↔ human with STATE/DECISIONS/lanes.
7. **RFC against yourself** — contributing upstream by arguing your hack is the wrong model.
8. **Buffered truth** — when your API says success and the catalog disagrees (MCP + atexit).
9. **Honesty copy** — writing README boundaries that survive a hostile judge.
10. **From Join Treaty to Nullspace** — killing your own MVP when it’s a feature.

---

## 7 · Emotional / team note (brief)

The weekend felt like two products: the **engine** (mostly real by Saturday) and the
**presentation surface** (board, PR URL, dbt truth, dirty graph) that kept trying to
lie. The teams that win these rooms usually finish the second product a day earlier than
we did. Lanes helped us not collide; they did not help us share one physical demo host
early enough.

Still: shipping Law 2, walk-the-book, and an honest RFC in one weekend is a real thing.
I’d run this collaboration pattern again with a harder stranger gate.

---

## 8 · Pointers

| Doc | Role |
|---|---|
| [`hack.md`](../../../../hack.md) | Shared retro (Lane B appends) |
| [`SUBMISSION-AUDIT.md`](../SUBMISSION-AUDIT.md) | Pre-submit multi-model verdict |
| [`multimodel-2026-08-09.md`](multimodel-2026-08-09.md) | Mid-weekend redteam union |
| [`redteam-2026-08-09.md`](redteam-2026-08-09.md) | Weapon scores |
| [`DECISIONS.md`](../DECISIONS.md) | Append-only law |
| [`handoffs/008-…`](../handoffs/008-to-claude-harden-rfc-19022.md) | OSS handoff to Claude |
| [`docs/oss/datahub-rfc-19022/`](../../../oss/datahub-rfc-19022/) | RFC polish kit |
