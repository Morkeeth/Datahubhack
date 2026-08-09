# PROTOCOL — how Cursor agents, Claude, and you collaborate

The problem this solves: many Cursor agents + subagents + an external Claude +
scattered transcripts = nobody knows the current truth, and decisions silently
reopen. The rule set below is deliberately small.

## Core idea: the repo is the shared brain

Nothing important lives only in a chat or a transcript. If it matters, it is a
file in `docs/collab/`. Chats are how we think; the repo is what we remember.

## Roles

| Party | Does | Does NOT |
|---|---|---|
| **You (human)** | Route handoffs ↔ Claude; approve; set priorities | Track state in your head |
| **Claude (external)** | Adjudicate strategy/scope; rule with rationale | Build or run code |
| **Cursor agent** | Build, verify, report; keep `STATE.md` + `DECISIONS.md` current | Reopen a decided decision silently |
| **Subagents** | Scoped research/verify/demo, report up | Be treated as a source of truth |

## The loop (one cycle)

```
Cursor agent ──writes──▶ handoffs/NNN-*.md ──you paste──▶ Claude
                                                            │
                                                          rules
                                                            ▼
Cursor agent ◀──you paste── rulings/NNN-*.md ◀────────── Claude
     │
   executes + updates STATE.md and DECISIONS.md
```

One cycle = one open question. Keep exactly **one** open decision in `STATE.md` at
a time; queue the rest.

## Rules that keep us un-lost

1. **`STATE.md` is always current truth.** Every agent updates it at the end of its
   turn (phase, the one open decision, who moves next). Read it first.
2. **Decisions are append-only** in `DECISIONS.md`. To change a decision you add a
   new entry that marks the old one `SUPERSEDED` — **no silent reopening**. This is
   the fix for "we locked Join Treaty, then re-questioned it twice without record."
3. **Every agent↔Claude exchange is a numbered file**, not a chat you have to
   reconstruct. Handoffs and rulings share the same number (`001` ↔ `001`).
4. **Handoffs are self-contained**: the ask, the minimum context links, and the
   exact questions to answer. Claude should not need the whole repo to rule.
5. **Rulings are actionable**: the decision, the rationale in one line, and any
   constraints/non-negotiables. The agent turns a ruling into a `DECISIONS.md` entry.

## Templates

### Handoff (agent → Claude): `docs/collab/handoffs/NNN-slug.md`

```md
# HANDOFF NNN — <one-line ask>
- From: <agent/session>  · Date: <date>  · Needs ruling by: <when>
- Context (read these): <1–3 links>

## The question
<the single decision to make>

## Options (if any)
<A/B/C… each: one line for + one line against>

## Recommendation
<agent's recommendation + one-line why>

## Please answer
1. <question>
2. <question>
```

### Ruling (Claude → agent): `docs/collab/rulings/NNN-slug.md`

```md
# RULING NNN — <decision in one line>
- Ruling on: HANDOFF NNN  · By: Claude  · Date: <date>

## Decision
<A/B/C… chosen, unambiguous>

## Why (one line)
<rationale>

## Constraints / non-negotiables
- <constraint>

## Answers
1. <answer>
2. <answer>
```

## How you (human) use this in 3 steps

1. Open `STATE.md` → see the one open decision and who moves next.
2. If it's Claude's move: paste the linked `handoffs/NNN` into Claude; paste the
   answer back as `rulings/NNN` (or just hand it to the Cursor agent — it will file
   it).
3. Tell the Cursor agent "go" — it executes and updates `STATE.md` + `DECISIONS.md`.

That's the whole system.
