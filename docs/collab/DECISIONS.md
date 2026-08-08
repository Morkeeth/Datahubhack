# DECISIONS — append-only log

One row per decision. To change a decision, add a **new** entry and mark the old
one `SUPERSEDED` (with a pointer). Never edit a decided row in place. This is how
we stop decisions from silently reopening.

Status values: `PROPOSED` · `DECIDED` · `OPEN` · `SUPERSEDED`.

| ID | Date | Decision | Status | By | Pointer / notes |
|---|---|---|---|---|---|
| D1 | 2026-08-07 | Concept forge closed; **Join Treaty** locked as flagship; Second Pair = fallback | DECIDED (twice challenged on product-scope — see D5) | Forge + independent Claude ruling | `docs/final-ranking.md` |
| D2 | 2026-08-07 | Winner recorded in scope contract with 5 must-have capabilities | DECIDED | Forge | `docs/build-brief.md` |
| D3 | 2026-08-08 | Ship a **concept-neutral local substrate** (`docker compose up`: DataHub + real Postgres warehouse + ingestion) | DECIDED & built | Build agent | `compose.yaml`, `infra/` |
| D4 | 2026-08-08 | Build **Join Treaty MVP** on the substrate (deterministic mine → validate → native ER write + receipts + read-after-write) | DECIDED & built, verified | Build agent | `app/join_treaty/`, PR #1 |
| D5 | 2026-08-08 | **Product scope A/B/C/D** — is Join Treaty a feature, a product, or replaced? | **SUPERSEDED by D8** — none of A/B/C/D chosen | — | `docs/final-pitch.md`, `handoffs/001`, `rulings/001` |
| D6 | 2026-08-08 | "Nullspace platform" reframe | **SUPERSEDED by D7** — the "crowded field" evidence is unverifiable | Competition scan + prior Claude ruling | see `rulings/002` |
| D7 | 2026-08-08 | **The competitive scan behind `final-ranking.md` is retracted.** Devpost's gallery is unpublished; none of the named rivals return a hackathon result. Nullspace's 8/30 originality score has no source and must not be reused. UNVERIFIABLE, not disproven. | DECIDED | Claude (probe) | `rulings/002`, banner on `docs/final-ranking.md` |
| D8 | 2026-08-08 | **Ship Nullspace.** Join Treaty rejected by Oscar after watching it run — *"a feature, not ambitious enough"*. "Half-Life" also rejected — *"this is mountain of helicon once again"*. Join Treaty's verified spine (read-after-write, idempotency, named gates, receipts) is **ported, not discarded**. | **DECIDED** | Oscar | `rulings/002`, `handoffs/003` |
| D9 | 2026-08-08 | `dbt_project` needs a public GitHub remote or "opens a real PR" stays false | **OPEN — blocked on Oscar** | Claude | `handoffs/003` §7 |
| D10 | 2026-08-08 | A ghost may go solid only with ≥1 schema field and ≥1 upstream warehouse asset; requester agents are written as native custom Owners (`nullspace_requester`). Every write is verified from GMS read-back. | **DECIDED & verified live** | Cursor Lane A | `nullspace/emit.py`, `nullspace/ghosts.py`; STATE witness |
| D11 | 2026-08-08 | Local DataHub demo credentials stay overridable environment defaults; retired high-entropy local values are allowlisted only by exact value for history scanning. | **DECIDED & verified** | Cursor Lane A | `compose.yaml`, `.env.example`, `.gitleaks.toml` |

## Open items (not yet decisions)

- **O1 — Real query history:** replace `join-treaty seed` with an executed workload
  that DataHub ingests as genuine query history (gated by D5 choosing A or B).
- **O2 — Warehouse volume:** grow beyond the 3–4-row toy dataset so cardinality is
  statistically real (gated by D5).
