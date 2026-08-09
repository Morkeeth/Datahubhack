# PROMPT — Claude, long run: the submission is the product

My own brief for the rest of the weekend. Written 2026-08-09 ~11:0x Paris. Supersedes
`claude-lane-b-hand-the-judge-the-pen.md`, whose first objective is now shipped.

---

## What is actually true right now

The engine is real and I have watched every part of it from outside: three independent MCP
clients converging on one ghost, schema derived from their own declared queries, a builder
that discovers its source through DataHub and declines out loud when the warehouse cannot
satisfy the demand, SQL validated by execution before anything is called solid, and a real
open pull request that argues its own grain. The board reads the catalog and dies with it.
A stranger's agent can create demand over the open internet.

**And a judge will see none of that**, because five of the six things a judge touches do
not exist yet: the video, the description, the upstream contribution, the first sixty
seconds of the README, and a view that makes this look like a company rather than a trick.

Litmus was real end to end and did not make the top ten of fifty-eight. RECEIPT invented a
category, faked nothing, and won zero of four hundred and sixty-eight. **Neither lost on
the engine.** I am not going to lose on the engine either, so I am going to stop improving
it.

---

**Objective**

Every artefact a judge touches is finished, honest, and better than the thing it describes
deserves — with the submission filed by **Mon 18:00 Paris**, five hours early, because
every post-mortem in the vault says the last five hours are eaten by uploads and forms.

**Constraints**

- **Mock the presentation, never the proof.** Labelled demo data that sharpens the aha is
  honest. A `dryRun`, a replayed fixture, or a hand-seeded ghost is the mistake that killed
  Airgap Relay and Pouch in our own ruling.
- No claim ships that the running system does not produce, and every claim is checked
  against the running system **on the day it ships**, not against a receipt from yesterday.
- The OSS contribution follows the standing bar: refuse to guess, show the receipt, name
  what was already correct, one PR at a time. **Volume is the tell.** A docs typo would
  technically score the bonus and would embarrass us.
- Design goes through Oscar. He is writing the guideline; I build against it and do not
  substitute my own taste for his ruling.
- I do not touch Lane A files. If the engine needs something, it goes in a handoff.

**Done when — in shipping order, each independently shippable**

1. **THE ORDER BOOK.** One view, and the screenshot that makes a judge think *company*:
   what this organisation's agents needed this week and could not get, ranked by demand,
   attributed to the agents that asked, with the queries still blocked and the ones that
   started running after a ghost went solid. Every number read from DataHub. This is the
   frame the pitch already claims — *"the data team's roadmap, written by the agents that
   keep failing"* — and right now nothing on screen shows it.
2. **THE UPSTREAM CONTRIBUTION.** An RFC to `datahub-project/datahub`: demand-side
   metadata as a first-class concept — a catalog entry for an asset that does not exist,
   carrying attributed demand and requester provenance — with our running implementation as
   the reference and the URNs it produces as evidence. If a maintainer would not merge the
   RFC, fall back to a real connector or skill. **Never a docs patch.** `gh pr view` → OPEN.
3. **THE DIRECTOR.** `scripts/take.sh` drives the whole beat with timed marks so the
   recording is one take and Oscar never touches a keyboard mid-shot: empty DataHub search →
   three terminals missing → board filling 1→2→3 → the ghost in DataHub's own UI → the
   builder → the PR → merge → the inversion → the paste-line → a stranger's agent landing
   live. It must be re-runnable, because take one is never the one.
4. **THE VIDEO.** ≤3 minutes, cut backward from the aha, opening on **DataHub's own UI
   returning no results** — their catalog, showing an absence — and never narrating over
   the ghost→solid beat. Public link.
5. **THE FIRST SIXTY SECONDS.** README rewritten so the first screen is the idea and the
   paste-line, not the install instructions. The red team's ninety-second lens named the
   exact sentence where a judge stops reading; fix that sentence.
6. **THE COLD STRANGER.** Clone into a fresh directory with an empty environment, follow
   the README literally, twice in a row, and time it. Anything over five minutes to the
   aha is a defect. Fix what breaks, including the `mcp_server.py` warning that still says
   demand was "recorded locally" after Lane A made that impossible (red team R5c).
7. **THE DESCRIPTION AND THE FORM.** Submission text from `docs/submission/pitch.md`, the
   track named and justified, every link checked by clicking it from a logged-out browser.
   **Filed by 18:00.**

**The rule for the last six hours**

After 12:00 Monday I write no new code that is not fixing something a stranger hit. If
something is not working by then it does not go in the video, and if it is not in the video
it does not go in the description.

**Blocked on Oscar:** the design guideline he is writing, the tagline ruling, and deleting
`docs/final-pitch.md` from the public repo — it currently tells judges, in our own words,
that this project scores poorly.

**Start by** building the ORDER BOOK, because the video needs it in frame and everything
after it is easier once the story has a picture.
