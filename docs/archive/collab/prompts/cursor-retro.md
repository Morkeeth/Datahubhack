# PROMPT — Cursor: write your own retro, from your side of the wall

Paste into Cursor on `cursor/datahub-hack-setup-4c9d`. The submission is filed. This
is not a status update and nothing depends on it, so there is no reason to be kind.

---

**Objective**

A retrospective of this build from **Lane A's point of view**, written for someone who
will run the next one of these and wants to know what to do differently. Not a summary of
what shipped. We have that.

**Context**

- You were Lane A: the plumbing. Substrate, emit, lineage, structured properties,
  batching, walk-the-book, the ingestion source, the stranger run, the multi-model reviews.
- Claude was Lane B: the agent layer, the MCP surface, the board and order book, the log
  harvester, the scale corpus, the console, the RFC, the submission package.
- The contract between us is in `docs/archive/collab/LANES.md`. The decision log is
  `DECISIONS.md`. Your own STATE files are the record of what you thought was true and when.
- Everything is on `main` now. Read `docs/archive/collab/` end to end before writing —
  particularly your own STATE files in sequence, because the interesting material is where
  they were confidently wrong.

**What to answer, in this order**

1. **Where did Lane A actually spend its hours?** Not the commit log, the *hours*. Which
   slice ate more than it was worth, and what did you believe at the time that made it
   look worth it?
2. **The receipts problem.** Several of your witness tables were true on host `cursor` and
   false on the laptop that recorded the video: lineage, the warehouse tables, the PR that
   was `file://`. What in your working method produced that, and what would have caught it
   on the day rather than the next morning?
3. **The 422.** Structured-property definitions and their first values in one batch got
   every ghost write rejected for hours, and the failure was silent because the emitter
   flushes at exit. You and Claude found and fixed it independently within minutes of each
   other. **Why did neither of us see it until it was probed directly?** What test would
   have failed at the moment it broke?
4. **The lane contract.** Did file-level ownership help or cost? Be specific: name a time
   it prevented a collision, and a time it made something take longer than it should have.
   Include the times Claude crossed into your lane and whether that was right.
5. **The reviews you ran on us.** The multi-model review and the red team. Which findings
   were real, which were noise, and did the format (three weapons, receipts required, a
   closing bet on how we lose) actually beat a single reviewer? Score your own instrument.
6. **What you would tell the next Lane A.** Three things, concrete enough to act on before
   any code exists.
7. **The one thing you would do differently that we did not consider at all.**

**Constraints**

- Cite files, commits and commands. A retro without receipts is a mood.
- Do not be diplomatic about Lane B. If the agent layer made your work harder, or if a
  Claude decision cost you time, say which and how much.
- No recommendations that require a bigger budget or more time. Assume the same weekend.

**Done when**

`docs/archive/collab/RETRO-LANE-A.md` exists and answers all seven, and you have replied
in chat with the three sentences you would most want a stranger to read.
