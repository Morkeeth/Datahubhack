# PROMPT — Claude, Lane B: hand the judge the pen

My goal for the remaining hours. Written 2026-08-09 ~10:2x Paris. Replaces the scope in
`claude-lane-b-the-reveal.md`; the board is done and pushed, so what is left is the part
that was hedged behind a tripwire — and hedging it was the mistake.

---

## The swing

Fifty-eight teams will show a judge a video of *their* agents doing something. We are going
to give the judge a line to paste into their own terminal, and **their** agent — Claude
Desktop, Cursor, whatever they already have open — will search a catalog, miss, and
discover it is the third agent this week to want that exact table. On a board they can
watch, live, while they are still on the call.

The moment a judge's own tool writes to your product, you stop being a submission and
become a thing that exists. **Nobody scores that against a rubric. They remember it.**

Everything else on my list is in service of that or is a judged dimension sitting at zero.

## Why this and not more engine

The vault is unambiguous and it has cost real money three times. Yieldbound: *"most
conceptually compelling in the cohort"* → 2nd, $1,000. RECEIPT: category invention, taste,
zero fake data → top 20% of 468, **zero prizes**. Litmus: real end-to-end, both sponsors
load-bearing, **did not top-10 of 58** — and its own pre-mortem named the axis that killed
it before a line was written: *felt/wow is the weak axis.* The pattern has a name in
`retro-litmus-2026-07-09.md`: **intellectually elite, emotionally flat in a ninety-second
room.** The engine is not the risk. It has never been the risk.

**Weak axis, named:** one thin loop, clean and small, which a judge scanning 58 submissions
reads as *did less*.
**Engineered fix:** the judge is not an audience. The judge is requester #3.

---

**Objective**

1. A stranger's agent, on a stranger's machine, creates demand on a public Nullspace board
   and watches its own miss become a catalog entry — with no clone, no Docker, no Python.
2. A contribution to `datahub-project/datahub` that a maintainer would merge **on its
   merits**, not as a hackathon courtesy.
3. A ≤3-minute video that opens on the aha and never explains itself.

**Context**

- Branch `claude/nullspace-agent-layer`, rebased on Cursor trunk. Lane B files only.
- Board rebuilt and pushed: M1 Darkroom, verified at 1440 and 390 against real data, both
  the hollow negative and the developed print on screen.
- The loop is live end to end on this laptop; `Morkeeth/nullspace-dbt#1` is a real OPEN PR
  the builder agent opened by itself.
- `Morkeeth/datahub` fork exists. The OSS dimension is at **zero**. So is the video.
- Cursor is fixing the passthrough SQL, `builder.py:389` and `nullspace reset` in Lane A.
  I do not touch those files.

**Constraints**

- **Mock the presentation, never the proof.** Labelled demo data that sharpens the aha is
  honest; a `dryRun` flag, a replayed JSON fixture, or a hand-written "example" ghost is
  the mistake that killed Airgap Relay and Pouch in our own ruling. If the public endpoint
  cannot be real, it does not ship — a fake one is worse than none.
- A public write endpoint is a public write endpoint. **Rate-limit it, cap the ghost
  namespace, never accept arbitrary URNs, and put nothing on it that matters.** It is a
  demo instance and it says so on the page.
- No claim ships that the running system does not produce.
- The OSS PR follows the standing bar in `feedback_oss_contribution_not_slop`: refuse to
  guess, show the receipt, name what was already correct, one PR at a time. **Volume is
  the tell.** A docs typo fix would technically score the bonus and would embarrass us.

**Done when**

1. **The endpoint is real.** An MCP client on a machine that is not this laptop connects
   over the network, searches, misses, and the miss appears on a public board URL within
   seconds. Proven from a clean container or a second machine — *not* from localhost with
   a different port. The README carries the one line a judge pastes.
2. **The board is public and read-only**, reading live from a running DataHub the judge
   never has to reach, with the demo-data disclosure on the page.
3. **The DataHub contribution is substantive.** Not a typo. The honest candidate: an
   **RFC for demand-side metadata as a first-class concept** — a catalog entry for an asset
   that does not exist, carrying a demand counter and requester provenance — with our
   running implementation as the reference and the URNs it produces as the evidence. If a
   maintainer would not merge the RFC, the fallback is a real connector or skill, never a
   docs patch. `gh pr view` returns OPEN and the body shows a receipt.
4. **The video, ≤3 min, cut backward from the aha.** First 15 seconds: the catalog grows a
   thing that does not exist. Last 30 seconds: the subtraction proof — DataHub gone, three
   agents failing in three silos, no namespace in which the want can be named. No narration
   over the ghost→solid beat; it plays in one continuous shot or it gets recut.
5. **`scripts/eval-nullspace.sh` passes twice in a row on a cold stack.** Today the second
   run finds the first run's solid asset and lies. Prove it can fail, too.

**Order, and the ruthless part**

3 and 4 are judged dimensions at zero and they cannot be bought late. **They ship first.**
1 and 2 are the swing, and the swing goes in the bin at **Mon 12:00 Paris** if a real
off-laptop client has not connected — not extended, not descoped, binned. Submission
freezes **18:00 Monday**, five hours before the deadline, because every post-mortem in the
vault says the last five hours go to uploads and form fields.

**Blocked on Oscar:** the M1 Darkroom design ruling (shipped, unruled), the tagline, and a
host for the public instance.

**Start by** proving the hard half first: get one MCP client talking to a Nullspace server
over the network rather than over stdio. Everything in objective 1 is downstream of that
one fact, and if it is not possible by 12:00 tomorrow I want to know today, not tomorrow.
