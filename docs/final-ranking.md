# Final concept ranking

Date: 2026-08-07

> ## ⚠️ SUPERSEDED 2026-08-08 — read this before using anything below
>
> **The decision below is reversed. Oscar ruled for Nullspace on 2026-08-08.**
> See `docs/collab/rulings/002-nullspace-commit.md` and the build brief at
> `docs/collab/handoffs/003-nullspace-roadmap.md`.
>
> **The "Competitive reality" table below is retracted.** It is attributed to a
> *"Public-entry scan conducted on 2026-08-07"*, but `datahub.devpost.com/project-gallery`
> states *"The hackathon managers haven't published this gallery yet"* — there is no
> public entry list, and search returns no DataHub-hackathon result for any of the
> named rivals. The table is **UNVERIFIABLE, not disproven**: the field may be
> crowded (2,865 registered), but it cannot be observed, so nothing can be scored
> against it.
>
> **Therefore Nullspace's originality score of 8/30 — the single mark that dropped it
> from 1st to 4th — has no source and must not be reused.** The ranking table below
> is retained as history only.
>
> What survives, because it does not come from that table: all three reviewers
> independently ranked Nullspace #1, and it collided with nothing.

Decision: ~~**Join Treaty wins; Second Pair is the fallback.**~~ **REVERSED — see banner.**
Ideation is closed (and stays closed).

## Inputs

- Hackathon requirements and scoring in `docs/playbook.md`
- Final GPT concepts in `concepts/gpt/final-round.md`
- Independent competitive-whitespace concepts in
  `concepts/third/final-round.md`
- An adversarial feasibility review of current DataHub OSS / SDK behavior
- An independent Claude final adjudication
- Public-entry scan conducted on 2026-08-07

No earlier Claude or Nullspace artifacts were present in this repository or its
remote branches, so the final pass evaluated the Nullspace framing directly
rather than pretending those missing artifacts had been read.

## Competitive reality

The public field is already strong and crowded:

| Theme | Public examples | Consequence |
| --- | --- | --- |
| Incident response and self-healing | DataSheriff, CASCADE, Aegisflow | Do not build another lineage incident commander |
| SQL/dbt generation and verification | Groundskeeper, Atlarix | Generic grounded codegen will not differentiate |
| Schema-change impact | LineageGuard | Avoid proposed-change blast-radius workflows |
| Catalog truth / claim verification | Notary, EPISTEME | Broad “trust the graph” claims collide |
| Hidden business rationale | RationaleOps | Avoid documentation interviews and rationale capture |
| Agent task staleness / erasure | Obsel | Avoid agent-work dependency tracking |
| ML drift and leakage | Lineage Sentinel, Silent Drift Sentinel, LeakWatch | Production ML is heavily occupied |
| MCP trust firewall | EPISTEME | Context Firewall is no longer whitespace |

The clearest remaining opening is to turn repeated query behavior into a
first-class semantic relationship that lineage does not capture.

## Rubric

- DataHub depth: 25
- Competitive originality: 20
- Real-world utility: 20
- Two-day feasibility: 20
- Three-minute demo strength: 15

## Ranking

| Rank | Concept | Depth | Originality | Utility | Feasibility | Demo | Total |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| **1** | **Join Treaty** | 24 | 19 | 16 | 16 | 13 | **88** |
| **2** | **Second Pair** | 19 | 15 | 18 | 18 | 12 | **82** |
| **3** | Product Foundry | 20 | 14 | 13 | 14 | 13 | **74** |
| **4** | Nullspace — broad lineage repair | 18 | 8 | 17 | 13 | 13 | **69** |
| **5** | Context Debt Compiler | 16 | 10 | 17 | 13 | 9 | **65** |
| **6** | Context Firewall | 11 | 6 | 13 | 13 | 7 | **50** |

## Winner: Join Treaty

> **Join Treaty mines the equality joins teams repeat in DataHub's query
> history, verifies each one against schema and column profiles, and writes it
> back as a native ER model relationship — the join graph that lineage never
> captures.**

### Why it wins

1. **DataHub is load-bearing:** Query entities supply evidence, schemas validate
   fields, profiles support cardinality, and `ERModelRelationship` is the native
   output.
2. **The distinction is crisp:** lineage answers “where did data flow?”; a join
   treaty answers “how do these datasets safely relate?”
3. **The decision is deterministic:** repeated explicit joins plus positive
   profile evidence; no model key and no LLM verdict.
4. **The write is substantive:** a first-class relationship entity, not only a
   tag or chat response.
5. **The demo has a clean reveal:** no relationship → evidence → approval →
   persisted relationship → idempotent rerun.

### Known constraint

Current DataHub OSS V2 UI does not render ER relationships even though the
backend entity and GraphQL/SDK surfaces work. The MVP must:

- use a minimal app view for the relationship and its evidence;
- PATCH the same receipt onto each dataset for proof in DataHub's Properties
  tab; and
- verify the relationship with a DataHub read-after-write request.

This is an honest platform gap, not a reason to fake a native UI screenshot.

## Nullspace ruling

**Keep Nullspace only as an optional wordmark/metaphor, not as the product
scope.** “Self-healing graph integrity platform” is too broad for two days and
collides with existing trust, verification, and lineage-repair entries.

If used at all:

> Nullspace presents **Join Treaty** — filling the semantic relationships that
> lineage maps to zero.

Do not call Join Treaty “module one,” promise general graph repair, or add
lineage repair to the MVP.

## Fallback: Second Pair

Switch only if Query entity seeding, profile retrieval, or native
`ERModelRelationship` read/write is still unstable at the end of the first
implementation checkpoint.

Second Pair reuses the query-evidence pipeline but writes candidate backup
owners, which renders natively and is technically simpler.

## Scope lock

The winner must ship exactly these capabilities:

1. Enrich two real `showcase-ecommerce` assets with deterministic Query/profile
   evidence, mine explicit single-column equality joins, and require at least
   three independent occurrences.
2. Reject unless both fields exist with compatible types and profile evidence
   supports a cardinality inference.
3. Write a native `ERModelRelationship` carrying the field mapping,
   cardinality, evidence count, and run ID.
4. PATCH a receipt onto both datasets and verify both mutations by reading them
   back from DataHub.
5. Show one minimal relationship/evidence view plus a link to the matching
   native DataHub Properties receipt.

Everything else is cut until these five work end to end.
