# Final ideation round — GPT

Date: 2026-08-07

This round deliberately avoids crowded public entries: incident commanders,
ML drift/leakage sentinels, schema-change blast-radius guards, catalog-claim
verification, and generic SQL/dbt generation.

## 1. Nullspace — Self-Healing Context Graph

**One-liner:** Nullspace compares DataHub's declared lineage with executable SQL
evidence, finds missing or contradictory edges, proposes the smallest safe graph
patch, and proves the repair with read-after-write.

**Track:** Agents That Do Real Work (primary), Open / Wildcard.

**User:** A data platform engineer who needs agents and humans to trust the
catalog before they use its lineage for impact analysis, governance, or code
generation.

**DataHub surface**

- Read: `get_lineage`, `get_entities`, `list_schema_fields`,
  `get_dataset_queries` where available.
- Evidence: local dbt/SQL fixtures plus DataHub schemas and transformation/query
  history. SQL parsing is deterministic; an LLM may explain but never invent an
  edge.
- Write: DataHub Lineage SDK `add_lineage` with transformation text and
  column-level mappings, plus a durable audit document/tag/description.
- Verify: fetch lineage again and attach the before/after receipt to the run.

**Three-minute demo**

1. Show a retail revenue mart in DataHub whose lineage silently omits an orders
   dependency and contains one self-cycle.
2. Run Nullspace; it overlays declared vs. observed lineage and displays
   evidence for `MISSING`, `COLUMN_HOLE`, and `SELF_CYCLE` findings.
3. Approve the evidence-backed additive patch. Nullspace writes lineage into
   DataHub and stores the audit receipt.
4. Refresh DataHub to show the repaired graph; rerun Nullspace and show that the
   missing-edge finding is gone.
5. Open `examples/lineage-patch.json` so judges can inspect the result offline.

**Local path:** Seed a small `nullspace-retail` graph into DataHub quickstart.
Use project-authored SQL transformations so the failure and repair are fully
deterministic and require no warehouse or model key.

**Artifact:** Before/after graph JSON, evidence-linked patch, generated
column-lineage map, and read-after-write receipt.

**Risks and cuts**

- Query history ingestion may vary by DataHub version: use committed SQL as the
  primary evidence source and query history as an enhancement.
- Never auto-delete a questionable edge in the MVP. Additive repairs can be
  approved; stale/ghost edges remain review-only findings.
- Scope parsers to one SQL dialect and four fixture transformations.

**Why it can win:** Most entries assume DataHub's graph is correct. Nullspace
improves the substrate every other agent depends on. The before/after change is
visible in DataHub itself, and the verdict is evidence-first rather than an LLM
guess.

## 2. Context Firewall — Least-Privilege Context for Agents

**One-liner:** A DataHub-aware MCP gateway compiles the smallest governed graph
slice an AI agent needs for a task, redacts forbidden fields, and records exactly
what context was released.

**Track:** Open / Wildcard, Agents That Do Real Work.

**User:** An AI platform owner who wants agents to use enterprise metadata
without exposing every sensitive schema, query, owner, or downstream asset.

**DataHub surface**

- Read domains, ownership, tags/glossary terms, schema fields, and lineage.
- Compute task-conditioned graph closure and deterministic policy decisions.
- Proxy a subset of DataHub MCP responses with field-level redaction.
- Write a context-release receipt/document and tag unresolved policy gaps.

**Three-minute demo:** Ask the same coding agent for a revenue task directly and
through Context Firewall. Direct access reveals a PII-tagged customer field;
the governed context packet substitutes a safe join key, preserves enough
lineage to complete the task, and leaves a receipt in DataHub.

**Artifact:** Signed context manifest, deny/allow evidence, redacted MCP trace,
and generated policy.

**Risks and cuts:** A complete MCP proxy is too large. MVP wraps three read tools
(`search`, `get_entities`, `get_lineage`) and one deterministic policy. No claim
of production authorization.

**Why it can win:** It treats DataHub as an active security control for agents,
not merely a retrieval source. The angle appears less crowded than generation,
incidents, or ML monitoring.

## 3. Context Debt Compiler — Task-Conditioned Readiness

**One-liner:** Given a concrete agent task, compile the DataHub graph into a
readiness report that identifies the minimum missing context, routes precise
questions to owners, and writes verified answers back.

**Track:** Agents That Do Real Work.

**User:** A data/AI platform team trying to determine why agents repeatedly
abstain or hallucinate on specific workflows.

**DataHub surface**

- Read schemas, ownership, terms, descriptions, lineage, and sample queries.
- Evaluate task-specific requirements, not a generic metadata completeness
  percentage.
- Generate owner-addressed question cards for only blocking gaps.
- On approval, write descriptions, glossary terms, owners, or a DataHub
  document; rerun the task readiness check.

**Three-minute demo:** A "generate compliant customer LTV model" task initially
fails because the semantic definition and approved join path are absent. The
compiler finds two blockers, obtains fixture-backed answers, writes them to
DataHub, and turns the same task from `ABSTAIN` to `READY`.

**Artifact:** Machine-readable readiness manifest, question cards, before/after
score, and mutation receipt.

**Risks and cuts:** "Readiness" can look subjective. Use a transparent,
versioned requirement schema and only claim readiness for one demo task.

**Why it can win:** It converts metadata quality into a concrete agent outcome.
However, it overlaps more with documentation/rationale projects than Nullspace.

## GPT preference

1. **Nullspace**
2. **Context Firewall**
3. **Context Debt Compiler**
