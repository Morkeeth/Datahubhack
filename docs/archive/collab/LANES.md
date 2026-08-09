# LANES — who owns which files (Claude ↔ Cursor)

- **Set:** 2026-08-08 ~23:4x Paris, by Oscar — *"keep a clean lane between you two"*
- **Rule:** you may **read** any file. You may **write** only files in your own lane.
  If you need a change in the other lane, open a handoff. **Never edit across the line.**

## Branches

| Party | Branch |
|---|---|
| Cursor cloud agent | `cursor/datahub-hack-setup-4c9d` |
| Claude (terminal) | `claude/nullspace-agent-layer` |

Both merge to the cursor branch. **Claude rebases onto Cursor, never the reverse** —
Cursor is the trunk.

## Lane A — CURSOR (the plumbing: make the three false claims true)

Owns, exclusively:

```
nullspace/builder.py        nullspace/emit.py       nullspace/client.py
nullspace/persist.py        nullspace/ghosts.py     nullspace/urns.py
nullspace/config.py         README.md               scripts/install-deps.sh
scripts/up.sh               scripts/demo.sh         compose.yaml   infra/
AGENTS.md                   docs/collab/STATE.md    docs/collab/DECISIONS.md
```

Job: Phase 0 + Phase 1 of `handoffs/003` — **schema**, **lineage**, **real PR**,
read-after-write, idempotency, and the broken stranger path.

## Lane B — CLAUDE (the moonshot: make the agents real)

Owns, exclusively:

```
nullspace/mcp_server.py     nullspace/agents/**     nullspace/board.py
nullspace/static/**         scripts/eval-nullspace.sh
docs/submission/**          docs/collab/LANES.md    docs/collab/handoffs/**
docs/collab/rulings/**
```

Job: §"Why this lane exists" below — plus the acceptance eval and the submission
package (video script, description, OSS PR candidate).

## Why Lane B exists — the honest gap

`nullspace/cli.py::cmd_demo` currently does this:

```python
for agent in ("consumer-a", "consumer-b", "consumer-c"):
    receipt = consumer_search(ns, want=want, agent_id=agent, dh=live)
```

**The three "consumer agents" are three strings in a for-loop.** The whole pitch is
agent-to-agent infrastructure — a shared namespace where independent agents discover
they wanted the same thing. A judge watching a scripted loop sees a slideshow with
extra steps, and the strongest claim in the pitch is the one thing the demo fakes.

Lane B closes that: **any real agent** — Claude Desktop, Cursor, an LLM with tools —
searches DataHub through an MCP surface, misses, and *its own miss* becomes demand.
The builder becomes an agent that decides to claim, not a function that always does.

That is the difference between "we simulated three agents" and "point your agent at
this and watch it happen."

## The contact point

Lane B **calls** Lane A's API (`Nullspace`, `consumer_search`, `build_and_solidify`)
and never edits it. If Lane B needs a signature change, it goes in a handoff — it
does not reach across.

## Shared files — neither side edits without saying so

`pyproject.toml` · `.env.example` · `.gitignore`

## Standing hazards (both lanes)

- **Never `git add -A`.** `dbt_project/` carries a nested `.git`; it lands as a
  broken gitlink. Stage explicitly, every time.
- **DataHub is the witness.** "We wrote it" is not evidence.
- **No README claim the running system does not produce.** That defect is what
  RULING 002 was written about.
