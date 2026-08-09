# PROMPT — Cursor multi-model RED TEAM: three models, one job, kill this submission

Run in Cursor **three times, once per model** (Claude Opus / GPT / Gemini — whichever
three are available), swapping `WEAPON`. Then run the merge step.

> This replaces `cursor-multimodel-review.md`, which asked three models to *review* the
> repo. Reviews produce politeness. We already know the polite findings. **These three are
> not reviewers. They are trying to end us**, and the only output that counts is a kill.

---

## The rules of the exercise

You are not on this team. You are on a **rival team**, two hours from the same deadline,
and the organisers have — bizarrely — given you a copy of Nullspace and one instruction:
**find the reason it does not win.** You do not get points for finding it competent. There
are 58 teams and one grand prize; the only useful sentence you can write is the one that
makes a judge put this submission down.

**A kill must be a sentence a judge could say out loud in the room.** Not "the README could
be clearer." Something like: *"They claim agents write the code, but the agent writes
SELECT-star with extra steps."* That is a kill. It is also, as of this morning, **true** —
so it is proof the exercise works, and it is now out of scope because it is already being
fixed. Find the next one.

**Every kill carries its receipt**: a `file:line`, a command with its actual output, or a
quoted sentence from the repo. A kill without a receipt is a smear and scores zero.

## Your WEAPON — use exactly one, state it in your first line

- **WEAPON 1 · The ninety seconds.** You are judge #4 on submission 34 of 58 and you have
  ninety seconds. You will not clone anything. You have the README, the board screenshot,
  the video, and the PR. **Where exactly do you stop reading?** Quote the sentence. Then:
  what does this look like it is, to someone who never gets past that sentence? If you can
  retell the idea to another judge on Monday, write your retelling verbatim — and if your
  retelling is more boring than the product, that gap is the kill.
- **WEAPON 2 · The cold machine.** Clean laptop, no Docker images cached, no Python
  environment, no tokens, no goodwill. Follow the README **literally** — no charitable
  substitutions, no "obviously they meant". Stop at the first failure and report the exact
  command and the exact error. Then keep going and count: **how many minutes to the aha?**
  Anything over five is a kill. Also try the things a stranger does that we never do: run
  it twice in a row, run it with the stack already up, run it with the stack half up,
  Ctrl-C in the middle and start again.
- **WEAPON 3 · The maintainer.** You maintain DataHub. You have seen four hundred projects
  bolt a badge onto your graph. **Is this sponsor-native or is it a key-value store with
  our logo on it?** Would deleting DataHub *break* this or merely inconvenience it — and
  can you prove your answer from the code rather than from the pitch? Then read our
  proposed contribution back to DataHub: would you merge it, or is it drive-by? Name the
  thing a real DataHub engineer finds naive within thirty seconds.

## What you may not do

- Do not re-find the three we already know: the passthrough SQL, the missing
  `nullspace reset`, `builder.py:389`. All three are in flight.
- Do not suggest features. You are killing, not designing. A kill that requires us to
  build something new by Monday is not a kill, it is a wish.
- Do not soften. If the honest answer is "the idea is a category thesis with a thin loop
  under it, and Oscar has lost with exactly that shape three times" — say that. The vault
  says it happened with Yieldbound, RECEIPT and Litmus. Check whether it is happening again.

## Done when

A table: `# | the kill (one sentence a judge would say) | weapon | receipt | can we survive it by Monday 18:00?`

Then one closing paragraph, and it is the whole point of your run:
**"If I had to bet, this submission loses because ______."** One blank. Fill it.

## Merge step, after all three

Write `docs/collab/reviews/redteam-2026-08-09.md`: every kill, deduped, with
`confirmed_by: N/3`. **Any kill at 3/3 goes straight to the top of the build queue and
outranks whatever is in flight.** For every 1/3 kill, say why the other two missed it —
sometimes one model is the only one looking in the right place, and the vault rule is that
a multi-model panel scores memorability and is blind to the market, so a lone finding about
a *rival product* is worth more than a unanimous finding about *taste*.

Close the file with the three "if I had to bet" sentences side by side. If all three name
the same cause, we have until 18:00 Monday to change it, and nothing else matters.

**Start by** stating your weapon in one line, then going straight for the throat. Do not
warm up with a summary of what Nullspace is. We know what it is.
