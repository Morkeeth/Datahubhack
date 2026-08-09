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
`nullspace_requester`), and **lineage-ready** (solidify attaches
`UpstreamLineage` to the real source). Resolution history and registered query
contracts ride in `datasetProperties.customProperties` today because stock
DataHub v1.7.0 exposes no Demand aspect we can register without rebuilding GMS;
that JSON is a stand-in for a future first-class aspect, not a private database.
The local JSON files are a cache. Delete them mid-demo; hydrate from GMS; the
state machine continues.

When the ghost goes solid it does not migrate to another type — the same URN
gains `SchemaMetadata`, loses the `ghost` tag for `solid`, and keeps the
requesters who asked. Demand and fulfillment are one object in one catalog.
That is the RFC spine: a Demand aspect (or structured property) on Dataset, plus
an ingestion source that emits unmet-search events — not a sidecar product that
happens to deep-link into DataHub.
