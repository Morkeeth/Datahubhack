# STATE — mission control (read this first)

> The single source of truth for where this project is **right now**. If you only
> open one file, open this one. Every agent updates it at the end of its turn.

- **Last updated:** 2026-08-08 22:01 UTC by Cursor Lane A (`bc-9950b172`)
- **Phase:** **Requester-derived schema payoff verified end-to-end.**
- **Deadline:** Mon 10 Aug 2026, 17:00 EDT / **23:00 Paris**
- **Worker branch:** `cursor/datahub-hack-setup-4c9d` · repo `Morkeeth/nullspace`

## You are here

**The A/B/C/D question is closed and none of its options won.** Oscar watched Join
Treaty run — the board on `:3000`, the receipts in DataHub on `:9002` — and ruled
*"a feature, not ambitious enough."* A subsequent proposal ("Half-Life") was rejected
as a re-skin of his existing Mountain of Helicon work. **Oscar has committed to
Nullspace.**

**Lane A and Lane B now meet at the real payoff.** Three MCP requester agents
registered three different queries. Lane A took the union of their declared
fields—not a hardcoded demo schema—wrote a dbt model over the disclosed revenue
warehouse, and DataHub returned all four fields, one upstream, and all three
requesters as native Owners. Every queued query flipped to `RUNS`: **3 running,
0 blocked**.

Ten simultaneous requester processes wrote through live DataHub and returned one
ghost with `demand=10` and 10 distinct requesters. An offline 20-process stress
also returned one ghost / demand 20. The file store now locks the entire
read→DataHub write→atomic save transaction.

**Still false and stated plainly:** `pr_url` is `file://`; no PR exists until D9.
Cold isolated acceptance eval now reports **16 passed, 0 failed, 1 pending**;
the only pending item is D9. Lane A waits for the lineage search index as well
as the direct aspect, so the UI-facing GraphQL read is green before solidify returns.

## THE ONE OPEN DECISION

> **Does `dbt_project` get a public GitHub remote?** (D9)

Until it does, the builder agent cannot open a real PR, and the README must not
claim one. **Owner: Oscar.** Recommendation: create `Morkeeth/nullspace-dbt` public.
Everything else in Phase 1 proceeds without it.

## Workstreams

| # | Workstream | Status | Owner next | Pointer |
|---|---|---|---|---|
| 1 | Dev environment / substrate | ✅ Done & verified live tonight | — | `compose.yaml`, `infra/` |
| 2 | Join Treaty MVP | ✅ Built & verified (13/13) — **not shipping; spine gets ported** | — | `app/join_treaty/`, `scripts/eval.sh` |
| 3 | Product-scope ruling | ✅ **CLOSED** — Nullspace | — | `rulings/002` |
| 4 | **Nullspace Phase 1 — schema · lineage · native Owners** | ✅ **DataHub read-back verified** | — | Lane A `nullspace/emit.py` |
| 5 | Nullspace Phase 2 — read-after-write + idempotency | ✅ **20-process concurrency verified** | — | `nullspace/persist.py` |
| 6 | Phase 3 — the reveal (board, legible on film) | 🔴 Not started | Cursor agent | `handoffs/003` §3 |
| 7 | **Phase 4 — video, description, OSS PR** | 🔴 **Not started — 2 of 6 judged dimensions at ZERO** | Cursor agent | `handoffs/003` §3 |
| 8 | Stranger path / secret hygiene | ✅ `datahub` on PATH; Compose valid; gitleaks clean | — | `scripts/install-deps.sh`, `compose.yaml` |

## Live DataHub witness (2026-08-08 21:55 UTC)

| Claim | DataHub returned |
|---|---|
| solid schema | `segment VARCHAR`, `mrr DOUBLE`, `month VARCHAR`, `churned_mrr DOUBLE` |
| schema source | `requester contracts: union of declared query fields` |
| upstream lineage | `total=1` → `postgres,local-warehouse.warehouse.ecommerce.revenue_events,DEV` |
| native ownership | 3 Owners: `revenue-copilot-1.0.0`, `finance-agent-2.3.1`, `board-deck-writer-0.9.0`; type `nullspace_requester` |
| contract payoff | `3 running, 0 blocked`; schema read back from DataHub |
| PR | **still false**: `file:///workspace/dbt_project#...`; no remote |
| cold acceptance | `16 passed, 0 failed, 1 pending` (D9 only), solid in 8s |

Concurrency witness: 10 simultaneous requester processes through live DataHub
returned one deterministic ghost URN, `demand=10`, `unique_requesters=10`; offline
stress reached 20/20.

## Next action for each party (right now)

- **Oscar:** rule D9 (public remote for `dbt_project` / `Morkeeth/nullspace-dbt`).
- **Cursor Lane A:** keep trunk; contract-derived build + concurrency complete.
- **Claude Lane B:** rebase onto Cursor; make acceptance eval rerunnable (current
  fixed demand finds yesterday's solid asset on a second run), then board reveal
  and submission package. Do not overwrite Lane A files.

## Canonical docs (don't re-derive these)

- Build brief: **`docs/collab/handoffs/003-nullspace-roadmap.md`** ← start here
- Ruling + the retracted scan: `docs/collab/rulings/002-nullspace-commit.md`
- Decisions log (append-only): `docs/collab/DECISIONS.md`
- How we collaborate: `docs/collab/PROTOCOL.md`
- ⚠️ `docs/final-ranking.md` is **SUPERSEDED** — retained as history, carries a banner
- Lane A worker: `cursor/datahub-hack-setup-4c9d`
- Night brief: `docs/collab/handoffs/004-night-run-2026-08-08.md`
- Lane contract: `docs/collab/LANES.md`
