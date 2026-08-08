# STATE — mission control (read this first)

> The single source of truth for where this project is **right now**. If you only
> open one file, open this one. Every agent updates it at the end of its turn.

- **Last updated:** 2026-08-08 ~23:3x Paris by Claude (Opus 5), terminal session
- **Phase:** **Concept DECIDED — Nullspace. Build not started.**
- **Deadline:** Mon 10 Aug 2026, 17:00 EDT / **23:00 Paris — ~46h**

## You are here

**The A/B/C/D question is closed and none of its options won.** Oscar watched Join
Treaty run — the board on `:3000`, the receipts in DataHub on `:9002` — and ruled
*"a feature, not ambitious enough."* A subsequent proposal ("Half-Life") was rejected
as a re-skin of his existing Mountain of Helicon work. **Oscar has committed to
Nullspace.**

A probe then found that the competitive scan which had scored Nullspace 8/30 on
originality **cannot have happened** — Devpost's project gallery is unpublished. See
D7. That number must not be reused.

**Nothing is blocked on Claude. The build agent is unblocked and should start.**

## THE ONE OPEN DECISION

> **Does `dbt_project` get a public GitHub remote?** (D9)

Until it does, the builder agent cannot open a real PR, and the README must not
claim one. **Owner: Oscar.** Recommendation: create `Morkeeth/nullspace-dbt` public.
Everything else in Phase 1 proceeds without it.

## Workstreams

| # | Workstream | Status | Owner next | Pointer |
|---|---|---|---|---|
| 1 | Dev environment / substrate | ✅ Done & verified live tonight | — | `compose.yaml`, `infra/` |
| 2 | Join Treaty MVP | ✅ Built & verified (13/13) — **not shipping; spine gets ported** | — | `app/join_treaty/`, `scripts/eval.sh` |
| 3 | Product-scope ruling | ✅ **CLOSED** — Nullspace | — | `rulings/002` |
| 4 | **Nullspace Phase 1 — schema · lineage · real PR** | 🔴 **NOT STARTED — critical path** | Cursor agent | `handoffs/003` §3 |
| 5 | Nullspace Phase 2 — read-after-write, idempotency, eval | 🔴 Not started | Cursor agent | `handoffs/003` §5 |
| 6 | Phase 3 — the reveal (board, legible on film) | 🔴 Not started | Cursor agent | `handoffs/003` §3 |
| 7 | **Phase 4 — video, description, OSS PR** | 🔴 **Not started — 2 of 6 judged dimensions at ZERO** | Cursor agent | `handoffs/003` §3 |
| 8 | Stranger path broken at command 1 | 🔴 Not started — breaks submission req. 2 | Cursor agent | `handoffs/003` §6 |

## The three facts the build turns on

Measured against a live DataHub tonight — **the first time Nullspace has ever been
observed running**. It works, and its README overstates it in exactly three places:

| README claims | DataHub returns |
|---|---|
| "goes solid: real schema" | `schemaMetadata: null` |
| "real lineage" | 0 upstream, 0 downstream |
| "a genuinely mergeable dbt PR" | `file://` path; `dbt_project` has **no remote** |

**Closing those three IS the build.** Everything else is polish.

## Next action for each party (right now)

- **Oscar:** rule D9 (public remote for `dbt_project`), and rule the name.
- **Cursor agent:** **start Phase 0 + Phase 1 now** — `handoffs/003`. Do not wait on D9;
  L1 (schema) and L2 (lineage) are unblocked.
- **Claude:** nothing pending.

## Canonical docs (don't re-derive these)

- Build brief: **`docs/collab/handoffs/003-nullspace-roadmap.md`** ← start here
- Ruling + the retracted scan: `docs/collab/rulings/002-nullspace-commit.md`
- Decisions log (append-only): `docs/collab/DECISIONS.md`
- How we collaborate: `docs/collab/PROTOCOL.md`
- ⚠️ `docs/final-ranking.md` is **SUPERSEDED** — retained as history, carries a banner
- Nullspace source: branch `park/nullspace-2026-08-08` (`747eb1b`) — **not yet on the working line**
