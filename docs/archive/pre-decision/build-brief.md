# Build Brief

Status: **LOCKED — ideation closed**

Ruling: `docs/final-ranking.md`

## Locked concept

- Name: **Join Treaty**
- Optional wordmark: **Nullspace presents Join Treaty**
- Track: Agents That Do Real Work (primary), Open / Wildcard
- One-liner: Join Treaty mines the equality joins teams repeat in DataHub's
  query history, verifies each one against schema and column profiles, and
  writes it back as a native ER model relationship — the join graph that
  lineage never captures.
- Source concept: `concepts/third/final-round.md`
- Fallback: **Second Pair**, only if native relationship read/write or seed
  evidence is unstable at the first implementation checkpoint.

## Scope for shipping

### Must have (demo path)

1. Load `showcase-ecommerce`, select two stable existing datasets, then enrich
   them with compatible profiles and at least four Query entities. Create
   project-authored datasets only as a documented fallback.
2. Parse explicit single-column equality predicates and require the same join
   in at least three independent Query URNs.
3. Validate field existence/type compatibility and infer cardinality only when
   profile evidence is positive; otherwise abstain.
4. Human-approved write of `ERModelRelationshipKey` and
   `ERModelRelationshipProperties` with mapping, cardinality, and evidence.
5. PATCH a compact treaty receipt onto both datasets and perform
   read-after-write verification for all persisted metadata.
6. Minimal app view showing the candidate, supporting queries, validation gates,
   relationship, and link to DataHub Properties.
7. Commit an offline example receipt and deterministic tests.

### Nice to have (cut first)

1. Multiple proposed relationships in one run.
2. DataHub Document containing a richer evidence dossier.
3. Optional LLM-generated explanation that cannot affect the verdict.

### Explicit non-goals

1. Composite joins, `USING`, implicit joins, CTE-heavy resolution, and multiple
   SQL dialects.
2. Referential-integrity or “verified foreign key” claims.
3. Automatic approval or removal of any metadata.
4. Native ER relationship rendering in current DataHub V2 UI.
5. Broad Nullspace graph repair, lineage repair, incidents, or code generation.
6. Dependence on a warehouse, private DataHub, or paid model key.

## Architecture sketch

- Runtime: Python 3.11, deterministic pipeline, SQLGlot parser, typed run model.
- DataHub reads: GraphQL `listQueries`, `QueryProperties`, `QuerySubjects`,
  `SchemaMetadata`, latest `DatasetProfile`, existing ER relationships.
- DataHub writes: REST-emitted MCPs for `ERModelRelationshipKey` and
  `ERModelRelationshipProperties`; `DatasetPatchBuilder` custom-property
  receipts; read-back through GraphQL / SDK.
- UI / CLI: one small local web view plus seed/audit/apply CLI commands.
- Sample data: real `showcase-ecommerce` dataset entities loaded by
  `scripts/setup-datahub.sh`, enriched by a deterministic treaty fixture. The
  datapack does not contain the required Query/profile aspects, so seed those
  explicitly while preserving the real asset URNs.

## Demo script (&lt;3 minutes)

1. **0:00–0:20** — Open the selected `showcase-ecommerce` datasets and show no
   treaty receipt. Explain: lineage is flow; joins are semantic relationships.
2. **0:20–0:55** — Run discovery. Show three Query URNs supporting
   `orders.customer_id = customers.id`.
3. **0:55–1:25** — Show schema compatibility and profile-supported `N:1`
   inference; contrast one rejected low-evidence candidate.
4. **1:25–1:55** — Approve. Persist the native ER relationship and both dataset
   receipts.
5. **1:55–2:25** — Show read-after-write success in the app and the same receipt
   in DataHub Properties.
6. **2:25–2:45** — Rerun: `0 new relationships`; open
   `examples/join-treaty-receipt.json`.

## Submission checklist

- [x] Apache-2.0 `LICENSE` present
- [ ] README stranger path &lt;3 minutes
- [ ] Local DataHub Docker instructions verified
- [ ] Live URL and/or flawless local setup
- [ ] Demo video &lt;3 minutes (YouTube/Vimeo public)
- [ ] `examples/` sample outputs if code-gen / reports
- [ ] Devpost description drafted
