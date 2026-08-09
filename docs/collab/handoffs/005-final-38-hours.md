# HANDOFF 005 — the last 38 hours

- **Written:** 2026-08-09 ~09:2x Paris by Claude (Opus 5), terminal
- **Deadline:** Mon 10 Aug 2026, 17:00 EDT / **23:00 Paris**
- **Supersedes** the "Next actions" block in `STATE.md` as of Cursor tip `86ccfe3`.

---

## The review that triggered this file

Cursor's night run (5 commits, tip `86ccfe3`) is the strongest single push this
project has had. Outcome 1 (builder as a real agent) is real, and the executable-SQL
gate was not asked for and should have been.

**But one claim does not survive read-back.** Probed 2026-08-09 ~09:1x Paris against
the live stack (`datahub-hack-*`, up 11h, GMS 200):

```
search type:DATASET query:"nullspace"  → 7 assets, all tagged solid, all demand=3
for each: GraphQL lineage(UPSTREAM).total → 0        (7 of 7)
           GET /aspects/<urn>?aspect=upstreamLineage → HTTP 404   (7 of 7)
```

- **Upstream lineage is 0 on every ghost in the graph, and the aspect is absent.**
  This is not search-index lag — nothing was written. `STATE.md`'s witness row
  *"upstream lineage total=1 → …revenue_events"* does not hold now.
- The asset whose schema `STATE.md` quotes
  (`ghost_monthly_recurring_revenue_by_segment_0d3a3d17`: `segment, mrr, month,
  churned_mrr`) has **no `schemaMetadata` aspect at all** — 404 on the aspect API.
- Owners landed on only **2 of 7** ghosts.

**The rule this breaks is our own rule #2:** *DataHub is the witness.* A witness table
in `STATE.md` may only contain rows a command printed in the same session, with that
command written next to it. Rows that age into fiction are worse than no rows.

---

## Where the points actually are

Six judged dimensions. Two sit at **zero** and are the cheapest on the board:
**Submission Quality** (video + description) and **OSS Bonus** (a PR back to DataHub).
They cannot be bought late. Neither depends on the engine.

The engine is ~85% done. The **reveal is 0% done.** Litmus lost on exactly this axis
(`retro-litmus-2026-07-09.md`): *"finalists demoed on staged data while we spent our
hours on a real engine nobody could perceive."* We now have the opposite problem in our
favour — a real engine — and 38 hours to make it perceivable.

---

## The moonshot, named

> **The judge's own agent creates the demand.**

Every other team will demo *their* agents. We publish an MCP endpoint, a judge points
Claude Desktop / Cursor / any tool-using model at it, asks for a table that does not
exist — **and their own miss appears as a demand edge on a public board, in front of
them.** Then the builder agent turns it real.

That single move answers three requirements at once:
1. **Live URL** judges can reach without touching a private network.
2. **Law 3 (agents, not humans)** at full strength — the user is literally their agent.
3. The subtraction frame becomes *participatory* instead of narrated.

Nobody remembers a video. They remember the thing that responded to them.

**Tripwire:** if the hosted MCP endpoint is not answering a real client by
**Mon 10 Aug 12:00 Paris**, cut it. Ship local compose + the board + the video.
Not a parallel track — a tripwire.

---

## Build plan — sliced, each slice independently verifiable

| # | Slice | Owner | Done when | Blocks |
|---|---|---|---|---|
| **0a** | Create `Morkeeth/nullspace-dbt` **public** (D9) | **Oscar** | `gh repo view` → PUBLIC | 1b, the pitch's ending |
| **0b** | Fork `datahub-project/datahub` → `Morkeeth/datahub` | **Oscar** | fork exists | 3 |
| **0c** | `nullspace reset` — wipe the 7 junk ghosts | Cursor | search returns 0 nullspace assets | clean demo |
| **1a** | **Lineage true** — `upstreamLineage` written and read back | Cursor | aspect API 200 **and** GraphQL `total ≥ 1` on a ghost created *after* the fix | the "real lineage" claim |
| **1b** | **Real PR** — builder opens it, `pr_url` is `https://` | Cursor | `gh pr view --json state` → `OPEN`; URL bound into resolution history | the ending |
| **1c** | Merge → solid closes the loop | Cursor | merge triggers dbt run → ghost flips solid, verified by read-back | the ending |
| **2a** | **Public MCP endpoint** — a stranger's agent can connect | Claude | an MCP client *not on this laptop* registers demand | the moonshot |
| **2b** | **The board** — ghost → solid in one continuous shot | Claude | hollow node visibly fills; no narration needed | the video |
| **3** | **OSS PR to DataHub** | Claude | PR open upstream, `gh pr view` → OPEN | OSS bonus |
| **4** | **Video ≤3 min + description** | Claude | public YouTube link, built backward from the aha | Submission Quality |
| **5** | **Multi-model adversarial review** | Cursor | ranked defect list, ≥2-model confirmation flag per defect | the freeze |
| **6** | **Freeze + submit** | Oscar | submitted **Mon 18:00 Paris**, 5h of slack, not 0 | — |

**Freeze is 18:00 Paris Monday, not 23:00.** Every hackathon post-mortem in the vault
says the last five hours are lost to upload, form fields, and a broken link.

---

## Non-negotiables (unchanged, restated so this file works alone)

1. No claim in the README the running system does not produce.
2. **DataHub is the witness** — and a witness row must carry the command that printed it.
3. Every abstention states its reason. Silence is not a verdict.
4. Demo data disclosed at the point of the claim.
5. Never `git add -A` — `dbt_project/` carries a nested `.git`.
6. **Mock the presentation, never the proof.** Staged, labelled demo data that sharpens
   the aha is honest. `dryRun=true` in the codebase is not.

## Prompts

- Cursor build → `docs/collab/prompts/cursor-lane-a-close-the-gap.md`
- Cursor multi-model review → `docs/collab/prompts/cursor-multimodel-review.md`
- Claude Lane B → `docs/collab/prompts/claude-lane-b-the-reveal.md`
