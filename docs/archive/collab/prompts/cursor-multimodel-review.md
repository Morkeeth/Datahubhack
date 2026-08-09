# PROMPT — Cursor multi-model review: three models, three lenses, one list

Run this in Cursor **three times, once per model** (e.g. Claude Opus / GPT / Gemini —
whichever three are available). Same prompt, different `LENS`. Then run the merge step.

> Why three models and not one: a single reviewer confirms its own taste. Our own
> memory rule — a multi-model panel scores memorability and is blind to the market —
> means the value here is **disagreement**, not consensus. We fix what **≥2 models
> independently flag**. Unanimity on a compliment is worth nothing.

---

**Objective**
Produce one ranked defect list for the Nullspace submission, where every entry is
reproducible and carries how many of the three models found it. We fix only what ≥2
confirm, plus any single-model finding that is a hard blocker (broken clone, false
claim, leaked secret).

**Context**
- Repo `Morkeeth/nullspace`, branch `cursor/datahub-hack-setup-4c9d`. Public, Apache-2.0.
- Read: `README.md`, `docs/collab/handoffs/005-final-38-hours.md`, `RULING.md`,
  `docs/collab/STATE.md`, `nullspace/**`.
- Submission is judged on six dimensions including **Submission Quality** and an
  **OSS-contribution bonus**. Deadline Mon 10 Aug 23:00 Paris; freeze 18:00.
- Known-bad already: lineage aspect absent on all 7 existing ghosts; `pr_url` is
  `file://`; no video yet. **Do not spend your run re-finding those three.**

**Your LENS — use exactly one, stated at the top of your output**

- **LENS 1 — the hostile judge.** You are scanning submission 34 of 58 with 90 seconds
  each. Where do you get bored, confused, or suspicious? Which sentence makes you think
  "this is a wrapper"? What does the repo look like it *did less* than it did
  (small/clean reads as low-effort to a scanner)? What is the one frame you would
  actually retell to another judge on Monday — and can you retell it at all?
- **LENS 2 — the cold stranger.** You have never seen this repo, you are on a clean
  machine, you follow the README literally and stop at the first thing that does not
  work. Report the exact command and the exact error. Then: how many minutes to the aha?
  Count them.
- **LENS 3 — the DataHub maintainer.** Is this **sponsor-native** — does deleting
  DataHub *break* the product, or merely degrade it? Are we using the graph as a graph
  or as a key-value store with a badge? Would you merge our proposed OSS contribution,
  or is it drive-by noise? Name what a real DataHub engineer would find naive.

**Constraints**
- Every defect needs `file:line` **or** a copy-pasteable repro command. No vibes.
- Rank by *cost to the score*, not by ease of fixing.
- Say plainly what is already good and should not be touched — the wrong fix is a
  real risk with 38 hours left.
- Do not propose new features. Scope is frozen.
- If you find a claim in the README or `STATE.md` that the running system does not
  produce, that is automatically a top-3 defect.

**Done when**
A single markdown table: `rank | defect | lens | file:line or repro | cost if unfixed |
fix (≤2 lines)`. Plus one closing line: **the single frame a judge remembers**, in your
words — if you cannot write that line, say so, because that is the finding.

**Merge step (run after all three)**
Write `docs/collab/reviews/multimodel-2026-08-09.md`: union of the three tables,
deduped, with a `confirmed_by: N/3` column. Sort by N descending, then by cost.
Anything at `3/3` goes to the top of the build queue immediately.

**Start by**
State your lens in one line, then read the README as your lens would — not as an
engineer reading for correctness.
