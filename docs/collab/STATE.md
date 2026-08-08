# STATE — mission control (read this first)

> The single source of truth for where this project is **right now**. If you only
> open one file, open this one. Every agent updates it at the end of its turn.

- **Last updated:** 2026-08-08 21:43 UTC by Cursor Lane A (`bc-9950b172`)
- **Phase:** **Nullspace Lane A core verified live in DataHub.**
- **Deadline:** Mon 10 Aug 2026, 17:00 EDT / **23:00 Paris**
- **Worker branch:** `cursor/cloud-agent-1786222076726-0ylmh` · repo `Morkeeth/nullspace`

## You are here

**Oscar committed to Nullspace** (RULING 002). Join Treaty is verified spine only
(13/13) — not shipping. Half-Life rejected. Competitive 8/30 originality score
retracted (gallery unpublished).

**Lane A shipped and exercised against DataHub v1.7.0.** The solid asset now
returns four schema fields, one upstream warehouse lineage edge, and requester
agents as native custom Owners. A separate four-process check returned exactly
one ghost with `demand=4`. `install-deps.sh` now puts `datahub` on PATH;
Compose uses environment-backed local demo values; gitleaks returns no findings.

**Still false and stated plainly:** `pr_url` is `file://`; no PR exists until D9.

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
| 5 | Nullspace Phase 2 — read-after-write + idempotency | ✅ **Lane A core verified; Lane B owns final eval** | Claude | `scripts/eval-nullspace.sh` |
| 6 | Phase 3 — the reveal (board, legible on film) | 🔴 Not started | Cursor agent | `handoffs/003` §3 |
| 7 | **Phase 4 — video, description, OSS PR** | 🔴 **Not started — 2 of 6 judged dimensions at ZERO** | Cursor agent | `handoffs/003` §3 |
| 8 | Stranger path / secret hygiene | ✅ `datahub` on PATH; Compose valid; gitleaks clean | — | `scripts/install-deps.sh`, `compose.yaml` |

## Live DataHub witness (2026-08-08 21:3x UTC)

| Claim | DataHub returned |
|---|---|
| solid schema | `cohort_id VARCHAR`, `trials BIGINT`, `conversions BIGINT`, `trial_to_paid_rate DOUBLE` |
| upstream lineage | `total=1` → `postgres,local-warehouse.warehouse.ecommerce.trials,DEV` |
| native ownership | 3 Owners, type `urn:li:ownershipType:nullspace_requester`, display names `consumer-a/b/c` |
| provenance | `demand=3`, all 3 requesters, full miss→claim→solidify history |
| PR | **still false**: `file:///workspace/dbt_project#...`; no remote |

Idempotency witness: four separate requester processes for a fresh phrase returned
one deterministic ghost URN with `demand=4`; DataHub search returned exactly one
Nullspace entity.

## Next action for each party (right now)

- **Oscar:** rule D9 (public remote for `dbt_project` / `Morkeeth/nullspace-dbt`).
- **Cursor Lane A:** complete; hand back live response + branch.
- **Claude Lane B:** rebase onto Cursor; run `scripts/eval-nullspace.sh`, board
  reveal, and submission package. Do not overwrite Lane A files.

## Canonical docs (don't re-derive these)

- Build brief: **`docs/collab/handoffs/003-nullspace-roadmap.md`** ← start here
- Ruling + the retracted scan: `docs/collab/rulings/002-nullspace-commit.md`
- Decisions log (append-only): `docs/collab/DECISIONS.md`
- How we collaborate: `docs/collab/PROTOCOL.md`
- ⚠️ `docs/final-ranking.md` is **SUPERSEDED** — retained as history, carries a banner
- Lane A worker: `cursor/cloud-agent-1786222076726-0ylmh`
- Night brief: `docs/collab/handoffs/004-night-run-2026-08-08.md`
- Lane contract: `docs/collab/LANES.md`
