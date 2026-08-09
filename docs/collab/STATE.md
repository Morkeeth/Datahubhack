# STATE — mission control (read this first)

> Every witness row names the **host** it was witnessed on and the command that
> printed it. Night-run receipts from another host are not reused as truth here.

- **Last updated:** 2026-08-09 ~08:25 UTC by Cursor Lane A
- **Host:** `cursor` (Cloud Agent VM)
- **Phase:** Law 2 refuse path + redteam merge shipped. Builder grain code ready; remote PR still blocked.
- **Deadline:** Mon 10 Aug 2026 · **Freeze 18:00 Paris**
- **Worker branch:** `cursor/datahub-hack-setup-4c9d`

## You are here

Redteam merge: `docs/collab/reviews/redteam-2026-08-09.md`.

**3/3 kill R1 — board is file store, not GraphQL** — outranks in-flight Lane A polish.
Lane B must ship GraphQL board. Lane A closed the MCP local-ghost hole via
`consumer_search` (D24) without editing `mcp_server.py`.

## Lane A this turn

| Check | Status | Host | Proof |
|---|---|---|---|
| Law 2: GMS down → refuse, no local ghost | ✅ | `cursor` | `./scripts/without-datahub.sh` → 3× `status=refused`; `consumer_search(dh=None)` refuses unless `offline=True` |
| MCP degrade closed at API | ✅ | `cursor` | `dh=None` → refused (MCP passes `live=None` when unhealthy) |
| `up.sh` waits on warehouse | ✅ | `cursor` | `pg_isready` gate; stack already up → “Warehouse ready.” |
| MRR grain + warehouse Aggregate | ✅ | `cursor` | `build_sql_plan` → `sum("mrr")…group by`; `EXPLAIN` → `HashAggregate` |
| Push grain SQL to `nullspace-dbt` | 🔴 | `cursor` | App install total=1; 403 to `cursor[bot]`. OPEN PR #1 still pre-think SQL |
| Solidify on merge | 🔴 | — | Blocked on real PR write + merge |

## Next actions (priority = redteam 3/3 then blockers)

1. **Lane B:** GraphQL board (R1 / multimodel 3/3) — judged URL must die if GMS dies.
2. **Oscar:** Cursor GitHub App → add `Morkeeth/nullspace-dbt` (or run builder as Morkeeth) → new PR with grain SQL + body → merge → `python3 -m nullspace.cli finalize --want "…"`.
3. **Lane A:** do not rewrite `emit.py`; keep generation tier disclosed; optional eval Ctrl-C hygiene (R8, 1/3).

## Canonical docs

- Redteam: `docs/collab/reviews/redteam-2026-08-09.md`
- Multimodel: `docs/collab/reviews/multimodel-2026-08-09.md`
- HANDOFF 006: `docs/collab/handoffs/006-to-cursor-retraction-and-two-bugs.md`
