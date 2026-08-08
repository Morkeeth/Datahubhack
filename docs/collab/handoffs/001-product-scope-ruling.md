# HANDOFF 001 — rule on product scope (A/B/C/D)

- From: Cursor build agent (`bc-8423daef`) · Date: 2026-08-08 · Needs ruling by: before next build session
- Context (read these): `docs/final-pitch.md` (full brief), `docs/final-ranking.md` (scores), `docs/build-brief.md` (scope contract)

## The question

The human has twice said the concept "doesn't sound like a real product." We have a
**working, verified** Join Treaty MVP (native `ERModelRelationship` write + receipts
+ read-after-write + tests). Two demo-tells remain: the mined query history is
**self-seeded**, and the ER output **doesn't render** in DataHub's UI. What do we
ship?

## Options

- **A — Sharp feature, made honest:** keep Join Treaty; replace seeding with **real
  ingested query history**; realistic data. + lowest risk, kills the "faked
  evidence" objection. − still one write; UI-invisible output.
- **B — "Usage-to-Graph" product (recommended):** one real-evidence pipeline → two
  native writes: Join Treaty (`ERModelRelationship`) **and** Second Pair (backup
  stewards in **Ownership, which renders natively**) + one review surface. + becomes
  a real product, fixes the UI-gap, avoids the crowded platform claim. − more scope.
- **C — Pivot to Second Pair alone:** renders natively, simplest. − discards working,
  differentiated Join Treaty depth.
- **D — Nullspace platform:** feels big. − two prior analyses say it's crowded /
  originality-destroying / infeasible in 2 days.

## Recommendation

**B**, with **A** as the guaranteed floor. Explicitly **not D**.

## Please answer

1. Confirm or overrule the concept (keep Join Treaty flagship / pivot to Second Pair / reframe to platform).
2. Pick the scope: **A / B / C / D**.
3. Agree the non-negotiables? (real ingested query history, realistic volume, native read-after-write proof, honest "observed join treaty" / "candidate steward" language, one review surface.)
4. The Nullspace question: wordmark-only, or is there a platform framing you'd actually endorse?
