# Final take + 20-hour plan (post-submit)

- **When:** 2026-08-09 ~23:40 UTC  
- **Inputs:** Cursor retro (`hack.md`), submission audit, redteam, live multi-model pass (Opus / GPT / Sonnet)  
- **Claude Lane B retro:** **not filed yet** — `hack.md` section still empty. Compare is Cursor retro ↔ audits until Claude appends.

---

## 1 · Compare (what we have vs what we don’t)

| Lens | Verdict | Overlap with Cursor retro |
|---|---|---|
| Cursor retro | Engine real; presentation surface lied; stranger cadence too late | — |
| Submission audit | **SHIP WITH GAPS** — board pollution, file://, Fusion CTAS, walk-the-book not in demo.sh | Same P0s |
| Redteam (earlier) | Board≠GMS, no OSS, hedged PR | Partially **stale**: board is GraphQL now; many real merged `nullspace-dbt` PRs (#5–#15); RFC open |
| Live audit (now) | **Ready with one cherry:** RFC #19022 still **RED** (title + prettier); polish kit **unapplied** | New top action |

**Final take:** Submitted and defensible. Not “done improving.” The single unfinished judged artifact is the **red upstream RFC**. Everything else for the next 20h is amplification (X clip, green RFC, clean board) — not new product.

---

## 2 · Ranked plan for the remaining ~20h

### TIER S — do even if only 2h left (~90 min)

| # | Action | Who | Why |
|---|---|---|---|
| 1 | **Apply `docs/oss/datahub-rfc-19022/APPLY.md`** — retitle `docs(rfc): …`, copy polished body, push, green CI | Oscar / Claude (needs write on `Morkeeth/datahub`) | Cursor cannot push the fork. Red RFC is what judges click. |
| 2 | **`nullspace reset`**, then cut the **X clip** (see `docs/submission/x-clip.md`) using **already-merged** PR #5 — do not live-push on camera | Oscar | Simplest real-PR path = choreography, not code. |
| 3 | Paste `REVIEWER-RESPONSE.md` on #19022 | Oscar / Claude | Maintainer credibility after green checks |

### TIER A — next ~6h

| # | Action |
|---|---|
| 4 | Claude fills `hack.md` Lane B retro (even 10 honest lines) |
| 5 | Post X with clip + RFC link + PR #5 |
| 6 | Confirm hosted read-only board URL stable for judging window |
| 7 | Soften harvest number drift in pasted Devpost text if still precise-and-uncommitted |

### TIER B — only if bored

| # | Action |
|---|---|
| 8 | Order-book shows PR on **claimed** rows too (shipped in this pass — tiny) |
| 9 | Pin `dbt-core<2` in requirements (stranger path) — only if not already done on laptop |
| 10 | Discussion issue linked from RFC header |

### DO NOT TOUCH

- Engine / ghost loop / no-mocks spine  
- Board restyle (Darkroom stays)  
- Second DataHub PR (connector / recipe) — **hurts** more than helps  
- Live `file://` on camera narrated as a PR  
- Rewriting RFC prose after prettier-clean body is applied  

---

## 3 · OSS: what’s best?

**One move:** green RFC #19022.  
**Not:** a second upstream PR tonight.  
**Story for X/Devpost:** *“We proposed demand-side metadata upstream — and argued against our own dataset squat.”*

Connector / `NullspaceDemandSource` = **after** freeze, referencing #19022.

---

## 4 · Simpler real-PR path

**Not a code change.** Real merged PRs already exist (`nullspace-dbt#5` is the clean citation).

| Approach | Use when |
|---|---|
| **A. Zero-risk:** board/order-book already solid + click `#5` | 45–90s X clip |
| **B. Live claim → finalize:** only on laptop with `gh` push | Longer demo; risk of `file://` |
| **Never:** cloud host / no token live push | |

`finalize --want` is the elegant one-command merge+solidify if you insist on live.

---

## 5 · X clip (summary)

Full sheet: **`docs/submission/x-clip.md`**  
Spine: empty search → demand 1→2→3 → walk-the-book refuse/claim → **merged PR #5** → solid owners → queries run.  
Tweet body: SUBMISSION.md §5 (long version) + RFC + PR links.
