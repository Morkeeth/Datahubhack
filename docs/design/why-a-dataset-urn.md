# Why a demand-side ghost is a Dataset URN

Nullspace models unmet demand as a `urn:li:dataset` under platform `nullspace`.
That is intentional, not laziness.

A missing table is still a **data asset someone tried to use**. Search, ownership,
lineage, and schema are the verbs requesters and builders already speak. Putting
demand on a sibling entity type that cannot appear in search, cannot own
requesters natively, and cannot grow upstream edges when it solidifies would
force a second product beside DataHub. We refuse that split.

From the first miss the ghost is **searchable** (same index as warehouse tables),
**ownable** (requester agents as native `Ownership` with type
`nullspace_requester` — written on the first miss, not only at solidify), and
**lineage-ready** (solidify attaches `UpstreamLineage` to the real source).

Lifecycle fields are first-class **structured properties**
(`nullspace.demand`, `nullspace.state`, `nullspace.want`) on stock DataHub
v1.7 — not only a JSON bag. Requester SQL is emitted as real **Query** entities
(`QueryProperties` + `QuerySubjects` → ghost URN). The PR lives in
`institutionalMemory` so it shows on the Links tab. Resolution history remains
bound to the URN (Scar Tissue). `datasetProperties.customProperties` is kept as
a dual-write so existing GraphQL board reads keep working; it is a cache of the
first-class aspects, not the database.

When the ghost goes solid it does not migrate to another type — the same URN
gains `SchemaMetadata`, loses the `ghost` tag for `solid`, and keeps the
requesters who asked. Demand and fulfillment are one object in one catalog.

The connector is real: `datahub ingest -c infra/datahub/nullspace_demand.yml`
(`NullspaceDemandSource`). That is the RFC spine with an implementation behind
it — not a sidecar product that happens to deep-link into DataHub.
