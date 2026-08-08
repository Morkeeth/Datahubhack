# STATE — mission control (read this first)

> The single source of truth for where this project is **right now**. If you only
> open one file, open this one. Every agent updates it at the end of its turn.

- **Last updated:** 2026-08-08 by Cursor build agent (`bc-8423daef`)
- **Phase:** Concept locked; **product-scope decision OPEN**
- **Deadline:** Mon 10 Aug 2026, 5:00pm EDT (~2 build days)

## You are here

We have a **working, verified** build (DataHub substrate + Join Treaty MVP). The
open question is **not technical** — it's scope: is Join Treaty shipped as a sharp
feature, grown into a real product, or replaced. That question is waiting on a
**Claude ruling**.

## THE ONE OPEN DECISION

> **What do we ship: A (sharp feature, real evidence), B (Usage-to-Graph product),
> C (pivot to Second Pair), or D (Nullspace platform)?**

- Full context: `docs/final-pitch.md`
- One-screen ask to paste into Claude: `docs/collab/handoffs/001-product-scope-ruling.md`
- **Owner of next move:** **Claude** (adjudicate) → then **You** (approve) → then Cursor agent (build)
- Recommended by the build agent: **B**, with **A** as the guaranteed floor. Not recommended: **D**.

## Workstreams

| # | Workstream | Status | Owner next | Pointer |
|---|---|---|---|---|
| 1 | Dev environment / substrate | ✅ Done & verified | — | `compose.yaml`, `infra/` |
| 2 | Join Treaty MVP (mine → validate → native write) | ✅ Built & verified | — | `app/join_treaty/`, PR #1 |
| 3 | Product-scope ruling (A/B/C/D) | ⛔ OPEN — needs Claude | Claude → You | `docs/final-pitch.md` |
| 4 | "Real query history" (kill seeding crutch) | ⏳ Not started (gated by #3) | Cursor agent | Option A/B in pitch |

## Roles (who does what)

- **You (human):** router + final approver. Carry handoffs to Claude and rulings back. Approve builds.
- **Claude (external):** strategy adjudicator. Rules on scope/direction. Writes to `docs/collab/rulings/`.
- **Cursor agent (this):** builds, verifies, reports; keeps STATE + DECISIONS current.
- **Subagents:** scoped one-off tasks (research, verify, demo). Not a source of truth.

## Next action for each party (right now)

- **You:** paste `handoffs/001-product-scope-ruling.md` into Claude; paste Claude's answer back into a new file under `docs/collab/rulings/` (or just tell this agent).
- **Claude:** rule on A/B/C/D and the four questions at the end of `docs/final-pitch.md`.
- **Cursor agent:** on hold for the ruling; will execute the chosen option and update this file.

## Canonical docs (don't re-derive these)

- Decisions log (append-only): `docs/collab/DECISIONS.md`
- How we collaborate: `docs/collab/PROTOCOL.md`
- The pitch under review: `docs/final-pitch.md`
- Locked ruling + scores: `docs/final-ranking.md` · Scope contract: `docs/build-brief.md`
