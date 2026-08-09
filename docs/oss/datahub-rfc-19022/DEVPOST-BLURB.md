# DEVPOST — upstream contribution blurb (paste as-is)

**Upstream contribution: an RFC to DataHub for demand-side metadata.**

Nullspace isn't just a hackathon repo — the idea it's built on is proposed back to the
project itself. We opened an RFC to `datahub-project/datahub` arguing that a catalog should
be able to record not only what exists, but what its consumers keep asking for and can't
find: a first-class **demand** entity, with attributed requesters, a resolvable lifecycle,
and a reciprocal edge to the dataset that eventually satisfies the want.

The RFC is deliberately honest about our own reference implementation: Nullspace currently
models demand as a squatted `dataset` URN, and the RFC argues *against* that shape and for a
proper new entity. It leaves the hard parts open in writing — the atomic-append mechanism
for concurrent requesters, the graph relationship on `resolvedBy`, server-side lifecycle
enforcement, requester spoofing / a separate `recordedBy` identity, and URN-normalisation
collisions — rather than pretending they're solved.

**RFC (open, judged artifact):** https://github.com/datahub-project/datahub/pull/19022

The running system is the evidence that the lifecycle is implementable and useful; the RFC
is the argument for the shape it should take upstream. The connector PR (a
`NullspaceDemandSource` metadata-ingestion source) comes later, referencing this RFC — we're
not rushing production code into the sponsor's repo the night before the deadline.
