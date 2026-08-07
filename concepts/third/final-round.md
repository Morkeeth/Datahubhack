# Final ideation round — competitive whitespace

Date: 2026-08-07

This independent pass started from the public competitive map rather than from
the earlier Nullspace framing. It deliberately excluded incident response,
SQL/dbt verification, schema-change impact, claim verification, rationale
capture, agent-task staleness, ML drift/leakage, and MCP trust firewalls.

## 1. Join Treaty

**One-liner:** Mine repeated equality joins from DataHub query history, validate
them against schemas and column profiles, and persist the result as a native
DataHub ER model relationship.

**Track:** Agents That Do Real Work, Open / Wildcard.

**User:** Data engineers and analysts who repeatedly rediscover safe join keys
because lineage describes data flow, not how datasets relate.

**DataHub surface**

- Read Query entities (`QueryProperties` and `QuerySubjects`), schemas, field
  profiles, and existing ER model relationships.
- Parse explicit equality predicates deterministically with SQLGlot.
- Require repeated independent query evidence, compatible field types, and
  profile-supported cardinality; otherwise abstain.
- Write `ERModelRelationshipKey` and `ERModelRelationshipProperties` with field
  mappings, inferred cardinality, and evidence properties.
- PATCH a visible receipt onto both datasets, then read both writes back.

**Three-minute demo**

1. Show three query records repeatedly joining
   `orders.customer_id = customers.id`; no treaty exists.
2. Run the miner and show the query URNs, schema compatibility, uniqueness
   evidence, and an `N:1` proposal.
3. Approve and write the native ER relationship.
4. Show the relationship and evidence in the app plus the matching receipt in
   DataHub's Properties tab.
5. Rerun to show idempotency (`0 new relationships`).

**Local path:** Seed two datasets, schemas, profiles, and four Query entities
into current DataHub quickstart. The showcase datapack does not include the
required query/profile evidence, so the seed is explicit and reproducible.

**Artifact:** `join-treaty-receipt.json` containing source aspect versions,
query evidence, emitted MCPs, and read-after-write verification.

**Risks and cuts**

- Current V2 OSS UI does not render ER relationships. Use the relationship
  entity as canonical storage, a small app view for visualization, and
  dataset-property receipts for native UI proof.
- Profiles support cardinality inference, not referential-integrity proof. Say
  “observed join treaty,” never “verified foreign key.”
- Support one dialect, single-column explicit equality joins, and a fixed
  threshold. No composite/implicit joins.

**Why it can win:** Query history, profiles, and ER relationships are
underused DataHub surfaces. The product creates semantic graph context that
lineage does not represent, with positive evidence and a real native write.

## 2. Second Pair

**One-liner:** Find critical graph regions with a sole human expert, select the
smallest evidence-backed set of backup stewards from query authorship and usage,
and record them as candidate owners.

**Track:** Agents That Do Real Work.

**DataHub surface:** Read ownership, domains, criticality, lineage, Query
authors, and usage; create a custom `knowledge_backup_candidate` ownership
type; PATCH candidate owners and evidence scores; read back.

**Demo:** A critical revenue neighborhood starts with one owner and zero backup
coverage. The agent selects two evidence-backed candidates covering all assets;
approval writes them to native Ownership panels and rerun is idempotent.

**Strength:** Clear real-world bus-factor problem and straightforward native
UI. **Risk:** “Suggest an owner” is a familiar shape and authorship does not
prove expertise, so labels must remain candidates.

## 3. Product Foundry

**One-liner:** Cluster assets consumers repeatedly use together, identify the
externally consumed boundary, and materialize a governed DataHub Data Product.

**Track:** Open / Wildcard.

**DataHub surface:** Read query co-use, lineage, domains, ownership and terms;
create a Data Product; add members and output ports; read back.

**Demo:** Scattered ecommerce assets become an “Order Fulfillment” product
after the app shows the deterministic co-use evidence and a human approves.

**Strength:** Beautiful native before/after and a real entity write.
**Risk:** Product boundaries are organizational; threshold-based clustering can
look arbitrary even when technically correct.

## Independent preference

1. **Join Treaty**
2. **Second Pair**
3. **Product Foundry**
