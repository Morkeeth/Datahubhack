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
| D5 | 2026-08-08 | **Product scope A/B/C/D** — is Join Treaty a feature, a product, or replaced? | **OPEN** — awaiting Claude ruling | — | `docs/final-pitch.md`, `handoffs/001` |
| D6 | 2026-08-08 | "Nullspace platform" reframe | PROPOSED then **advised against** (crowded field; not yet decided — folded into D5 option D) | Competition scan + prior Claude ruling | see `docs/final-pitch.md` §2c |

## Open items (not yet decisions)

- **O1 — Real query history:** replace `join-treaty seed` with an executed workload
  that DataHub ingests as genuine query history (gated by D5 choosing A or B).
- **O2 — Warehouse volume:** grow beyond the 3–4-row toy dataset so cardinality is
  statistically real (gated by D5).
