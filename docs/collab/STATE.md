# STATE — mission control (read this first)

> The single source of truth for where this project is **right now**. If you only
> open one file, open this one. Every agent updates it at the end of its turn.
> **Witness rule (HANDOFF 005):** every row below carries the command that printed it.

- **Last updated:** 2026-08-09 07:25 UTC by Cursor Lane A (`bc-9950b172`)
- **Phase:** **Close-the-gap: reset + fresh solid lineage re-earned; real PR blocked on write token.**
- **Deadline:** Mon 10 Aug 2026, 17:00 EDT / **23:00 Paris** · **Freeze 18:00 Paris**
- **Worker branch:** `cursor/datahub-hack-setup-4c9d` · repo `Morkeeth/nullspace`
- **Brief:** `docs/collab/handoffs/005-final-38-hours.md`

## You are here

HANDOFF 005 reported lineage missing on Oscar's laptop (aspect 404 / GraphQL
total=0 on 7 ghosts). **On this Cloud Agent stack that finding is refuted for
assets created after the SDK lineage emit** — see witness table. The stock
`GET /aspects/<urn>?aspect=upstreamLineage` path NPEs (HTTP 500) on this GMS;
the working aspect witness is `GET /entitiesV2/<urlencoded-urn>` (HTTP 200)
plus GraphQL `lineage(UPSTREAM).total`.

`python3 -m nullspace.cli reset` hard-deletes platform `nullspace` datasets and
clears the file store. Verified hollow. A fresh ghost created after that reset
solidified with schema, 3 requester Owners, aspect lineage, and GraphQL
lineage ≥ 1.

**D9 repo exists and is PUBLIC** (`gh repo view Morkeeth/nullspace-dbt` → PUBLIC).
**Still blocked:** `cursor[bot]` has **no push** to that repo (git push → 403).
Until Oscar grants write or sets `NULLSPACE_DBT_TOKEN`, `pr_url` stays honest
`file://`. Merge→solidify path is wired (`nullspace.cli finalize`) and waiting
on that token.

## HANDOFF 005 checks

| # | Check | Status | Command / proof |
|---|---|---|---|
| 1 | `nullspace reset` → 0 nullspace assets | ✅ | `python3 -m nullspace.cli reset` → `deleted_count=6`, `datahub_nullspace_count=0`; follow-up `DataHubClient().list_nullspace_urns()` → `[]` |
| 2 | Fresh solid: aspect + GraphQL lineage | ✅ | Asset `ghost_close_the_gap_revenue_lineage_1786260037_f60d0e8e` created after reset. `GET /entitiesV2/<urn>` → HTTP 200, `upstreamLineage.upstreams=[…revenue_events…]`. GraphQL `dataset.lineage(UPSTREAM).total=1`. Stock `GET /aspects/<urn>?aspect=upstreamLineage` → HTTP 500 (GMS NPE; not used as witness). |
| 3 | schema + 3 Owners on same asset | ✅ | Same GraphQL read: fields `segment,mrr,month,churned_mrr`; 3 Owners type `nullspace_requester`. |
| 4 | `pr_url` https + `gh pr view` OPEN | 🔴 | Blocked: `Morkeeth/nullspace-dbt` PUBLIC but push denied to `cursor[bot]`. `pr_url` = `file:///workspace/dbt_project#…`. Need `NULLSPACE_DBT_TOKEN` or collaborator write. |
| 5 | Merge flips ghost to solid | 🔴 | Blocked on #4. Code path ready: `python3 -m nullspace.cli finalize --want "…"`. |

## Live DataHub witness (2026-08-09 07:22 UTC) — fresh post-reset asset

Asset:
`urn:li:dataset:(urn:li:dataPlatform:nullspace,ghost_close_the_gap_revenue_lineage_1786260037_f60d0e8e,PROD)`

| Claim | Command | Returned |
|---|---|---|
| reset hollow | `python3 -m nullspace.cli reset` then list platform nullspace | `datahub_nullspace_count=0` |
| upstreamLineage aspect | `GET http://localhost:8080/entitiesV2/<urlencoded-urn>` | HTTP 200; upstreams = `postgres,local-warehouse.warehouse.ecommerce.revenue_events,DEV` |
| GraphQL lineage | GraphQL `dataset(urn:…){ lineage(input:{direction:UPSTREAM,…}){ total } }` | `total=1` → revenue_events |
| schemaMetadata | same GraphQL / entitiesV2 | `segment TEXT`, `mrr NUMERIC(14,2)`, `month TEXT`, `churned_mrr NUMERIC(14,2)` |
| ownership | same GraphQL | 3 Owners: `revenue-copilot-1.0.0`, `finance-agent-2.3.1`, `board-deck-writer-0.9.0`; type `nullspace_requester` |
| SQL gate | resolution event `sql_validated` on ghost | `EXPLAIN` Seq Scan; 4 columns; 3 sample rows |
| PR | custom property `nullspace.pr_url` | **still false**: `file://…` — no push to nullspace-dbt |

## THE OPEN BLOCKER (was D9)

> **`Morkeeth/nullspace-dbt` is PUBLIC. Oscar must grant write access** (add
> collaborator / install app / provide `NULLSPACE_DBT_TOKEN`) so the builder can
> open an OPEN PR. Until then the pitch ending stays `file://`.

## Workstreams

| # | Workstream | Status | Owner next | Pointer |
|---|---|---|---|---|
| 1 | Dev environment / substrate | ✅ Done | — | `compose.yaml`, `infra/` |
| 2 | Join Treaty MVP | ✅ Built — **not shipping** | — | `app/join_treaty/` |
| 3 | Product-scope ruling | ✅ CLOSED — Nullspace | — | `rulings/002` |
| 4 | Phase 1 schema · lineage · Owners | ✅ Re-earned on fresh post-reset ghost | — | `nullspace/emit.py` |
| 5 | read-after-write + idempotency | ✅ | — | `nullspace/persist.py` |
| 6 | Builder-agent decision + SQL gate | ✅ | — | `python3 -m nullspace.builder` |
| 6b | **`nullspace reset`** | ✅ Verified hollow | — | `python3 -m nullspace.cli reset` |
| 6c | **Real GitHub PR + merge→solid** | 🔴 Blocked on write token to nullspace-dbt | Oscar | `NULLSPACE_DBT_TOKEN`, `cli finalize` |
| 7 | OSS contribution | 🔴 Blocked: no fork / write | Oscar | — |
| 8 | Stranger path / secret hygiene | ✅ | — | `scripts/install-deps.sh` |
| 9 | Multi-model review (LENS 1/2/3) | ✅ Merged defect list | Cursor | `docs/collab/reviews/multimodel-2026-08-09.md` |

## Cold eval (post-fix, 2026-08-09)

```bash
python3 -m nullspace.cli reset
NULLSPACE_STORE=/tmp/nullspace-eval-fresh3.json \
NULLSPACE_EVAL_WANT="fresh-nullspace-$(date +%s)" \
python3 scripts/eval_nullspace.py --cold
```

Returned: **16 passed, 0 failed, 1 pending** (pending = real PR / D18 write token).
Schema 4 fields, lineage 1, native Owners present on the solid asset.

## Next actions

- **Oscar:** grant write on `Morkeeth/nullspace-dbt` or export `NULLSPACE_DBT_TOKEN` — unblocks checks 4–5 (the pitch ending).
- **Oscar:** fork `datahub-project/datahub` → `Morkeeth/datahub` if OSS bonus stays required.
- **Claude Lane B (from multimodel ≥2/3):** board must read DataHub GraphQL (not a divergent temp file); judged MCP path must `register_query` so fallback trials schema is never the moonshot.
- **Cursor Lane A:** waiting on write token for real PR; do not fake it.

## Canonical docs

- Last 38h plan: **`docs/collab/handoffs/005-final-38-hours.md`**
- Lane A prompt: `docs/collab/prompts/cursor-lane-a-close-the-gap.md`
- Multimodel review: `docs/collab/prompts/cursor-multimodel-review.md`
- Decisions log: `docs/collab/DECISIONS.md`
- Lane contract: `docs/collab/LANES.md`
- Worker branch: `cursor/datahub-hack-setup-4c9d`
