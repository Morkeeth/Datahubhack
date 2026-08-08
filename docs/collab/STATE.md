# STATE — mission control (read this first)

> The single source of truth for where this project is **right now**. If you only
> open one file, open this one. Every agent updates it at the end of its turn.

- **Last updated:** 2026-08-08 ~22:5x UTC by Cursor cloud agent (`bc-9950b172`)
- **Phase:** **Concept DECIDED — Nullspace. Build agent READY; Phase 0 in progress.**
- **Deadline:** Mon 10 Aug 2026, 17:00 EDT / **23:00 Paris**
- **Worker branch:** `cursor/cloud-agent-1786222076726-0ylmh` · repo `Morkeeth/nullspace`

## You are here

**Oscar committed to Nullspace** (RULING 002). Join Treaty is verified spine only
(13/13) — not shipping. Half-Life rejected. Competitive 8/30 originality score
retracted (gallery unpublished).

**Cursor cloud worker is online and ready.** Phase 0 started: collab docs + compose
substrate + Join Treaty spine brought onto the worker branch; `install-deps.sh`
fixed so `datahub` lands on `PATH` (stranger path defect). Unit tests: **3/3 pass**.
Docker not available in this cloud pod yet (`docker info` fails) — L1/L2 emit code
can land; live GraphQL witness needs DataHub up (compose / local).

**Nothing is blocked on Claude.**

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

- **Oscar:** rule D9 (public remote for `dbt_project` / `Morkeeth/nullspace-dbt`).
- **Cursor agent (this run):** READY — on GO: L1 schemaMetadata emit + L2 lineage
  emit + L5 eval skeleton. Do not wait on D9 for L1/L2. Never claim a real PR until D9.
- **Claude:** nothing pending.

## Canonical docs (don't re-derive these)

- Build brief: **`docs/collab/handoffs/003-nullspace-roadmap.md`** ← start here
- Ruling + the retracted scan: `docs/collab/rulings/002-nullspace-commit.md`
- Decisions log (append-only): `docs/collab/DECISIONS.md`
- How we collaborate: `docs/collab/PROTOCOL.md`
- ⚠️ `docs/final-ranking.md` is **SUPERSEDED** — retained as history, carries a banner
- Nullspace source: branch `park/nullspace-2026-08-08` (`747eb1b`) — **not yet on the working line**
