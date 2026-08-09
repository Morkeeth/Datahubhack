# PROMPT — Claude, Lane B: make a stranger's own agent create the demand

My own goal for the next 38 hours. Written 2026-08-09 ~09:3x Paris.

---

**Objective**
A judge, on their own laptop, points their own coding agent at our public MCP endpoint,
asks it for a table that does not exist — and **watches their own miss appear as a
demand edge on a public board, live.** Then a builder agent turns that want into a real
table. Not "we simulated three agents." *Point your agent at this and watch it happen.*

That is the live-URL requirement, Law 3, and the subtraction frame solved by one move,
and it is the only part of this submission that no other team can copy in a weekend.

**Context**
- Repo `Morkeeth/nullspace`, my branch `claude/nullspace-agent-layer`, rebased onto
  Cursor trunk `86ccfe3`. Lane B owns `nullspace/mcp_server.py`, `nullspace/agents/**`,
  `nullspace/board.py`, `nullspace/static/**`, `scripts/eval-nullspace.sh`,
  `docs/submission/**`, `docs/collab/{handoffs,rulings,LANES.md}`.
- I call Lane A's API and never edit it. Signature changes go in a handoff.
- Engine is ~85% real (Cursor's night run). **The reveal is 0%.** Two judged dimensions
  sit at zero: Submission Quality and the OSS bonus.
- The documented way Oscar loses: *intellectually elite, emotionally flat in a
  90-second room* (`retro-litmus-2026-07-09.md`). Litmus named "felt/wow is the weak
  axis" before building and then lost on exactly that axis.

**The named weak axis, and its engineered fix**
- **Weak axis:** felt. One thin loop, clean and small, which a judge scanning 58
  submissions reads as *did less*.
- **Fix:** the judge is not an audience, they are requester #3. Participation is the
  only cure for flat that survives contact with a tired room.

**Constraints**
- **Mock the presentation, never the proof.** Labelled demo data that sharpens the aha
  is honest. A `dryRun` flag, a pre-baked JSON replay, or a hand-written "example"
  ghost is the exact mistake that killed Airgap Relay and Pouch in our own ruling.
- Build the demo **backward from the aha**. The board exists to make one moment legible;
  anything that does not serve that moment does not get built.
- No claim ships that the running system does not produce. Read it back from DataHub or
  do not say it.
- Design goes through `docs/design/design-prompt.md` and Oscar's ruling — no default
  dashboard slop, no purple gradient, no shadcn-out-of-the-box tell.
- Scope frozen. `RULING.md`'s kill list stays dead.

**Done when — in this order, each shippable alone**
1. **Board.** Ghost → solid legible in **one continuous shot, no narration**: hollow
   outline, demand counter ticking 1→2→3, then the fill — schema, owners, upstream
   snapping in. Verified by recording it and watching it with the sound off.
2. **Public MCP endpoint.** An MCP client **not running on this laptop** connects,
   misses, and its miss shows on the public board within seconds. Proven from a second
   machine or a clean container — not from localhost.
3. **OSS PR to `datahub-project/datahub`.** Open, real, mergeable, not drive-by. Needs
   Oscar's fork (blocker 0b). Standing bar: refuse to guess, show the receipt, name what
   was already correct.
4. **Video ≤3 min + description.** Public link. Cut backward from the aha; the first
   15 seconds must show the catalog growing a thing that does not exist.
5. **Rerunnable eval.** `scripts/eval-nullspace.sh` passes on a cold stack *twice in a
   row* — today it finds yesterday's solid asset on the second run and lies.

**Tripwire (not a parallel track)**
If the public MCP endpoint is not answering a real off-laptop client by **Mon 12:00
Paris**, cut it entirely and ship local compose + board + video. Do not let the
moonshot eat the submission package. Submission freezes **18:00 Paris Monday**.

**Blocked on Oscar**
- **D9** — `Morkeeth/nullspace-dbt` public (blocks Cursor's ending, not mine).
- **0b** — fork `datahub-project/datahub` (blocks my #3).
- Design direction ruling · tagline ruling (`docs/submission/taglines.md`).

**Start by**
Record the current demo end to end with the sound off and watch it as a judge. Write
down the exact second boredom starts. Build the board backward from that second — not
from the data model.
