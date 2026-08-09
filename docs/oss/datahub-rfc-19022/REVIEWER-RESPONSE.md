# REVIEWER-RESPONSE — paste as a comment on PR #19022

> For the automated review (cubic) points 1–10. Each is marked **FIX** (changed in this
> revision) or **Open Question** (deliberately deferred and now written into the RFC's
> _Unresolved questions_ so it's tracked rather than hidden). Thanks for the read — several
> of these sharpened the proposal.

Thanks for the thorough review. Mapping each point:

1. **Basic example fails to import `MetadataChangeProposalWrapper`.** — **FIX.** Added
   `from datahub.emitter.mcp import MetadataChangeProposalWrapper` to the example so it's
   copy-runnable.

2. **`DemandRequester.source` is mandatory but the example omits it.** — **FIX.** The
   example requester now sets `source="query-log"`, matching the "source is deliberately
   mandatory" prose.

3. **Emitter retries would double-count a requester.** — **FIX.** Added a mandatory
   `requestId` field (stable per-event key) and prose stating a retry replaces its own prior
   entry instead of counting as a second requester; the emitter defines request identity and
   it's opaque to DataHub.

4. **`query` could leak literal user data into the catalog.** — **FIX.** Added an explicit
   sentence that `query`, when populated, must be redacted of literals before emission — the
   aspect stores a query *shape* for provenance, not a queryable copy of user data.

5. **A plain UPSERT of the aspect races on concurrent requesters and overwrites, so demand
   won't actually converge.** — **FIX (acknowledged) + Open Question.** New _Convergence_
   paragraph states the whole-value UPSERT race plainly and that merging `requesters` needs an
   atomic append (server-side keyed-collection mutation or a client read-modify-conditional-write
   loop). We do **not** claim it's solved — the concrete mechanism is Unresolved question 5.

6. **`resolvedBy` is a bare `Urn`; the "provenance backwards" claim needs a real graph
   relationship.** — **Open Question (5→now Unresolved question 6).** Making "which demand
   caused this dataset to exist" traversable requires picking a relationship name, direction,
   and whether the dataset side is derived or needs its own aspect write. Written up rather
   than glossed.

7. **Lifecycle transitions (e.g. `RESOLVED` with no `resolvedBy`, reopening a terminal
   record) aren't validated.** — **Open Question (Unresolved question 7).** Whether the state
   machine is enforced server-side or left to convention (as most DataHub aspects are today)
   is called out explicitly.

8. **`requester` is caller-asserted and therefore spoofable — "3 agents" can be fabricated.**
   — **Open Question (Unresolved question 8).** Any principal that can write the aspect can
   attribute a want to any actor URN; whether that needs a separate `recordedBy`/collector
   identity is now an open question. Also disclosed in the reference impl's honesty section.

9. **Punctuation-stripping normalisation silently collides distinct wants.** — **Open
   Question (Unresolved question 3).** `re-sign` vs `resign`, `foo.bar` vs `foobar` collapse
   onto one URN with no collision detection; escaping-instead-of-stripping and accepting a
   higher duplicate rate are both on the table.

10. **The reference implementation squats a `dataset` URN — isn't this RFC just that?** —
    **FIX (kept honest).** No: the RFC argues *against* the squat and for a new `demand`
    entity. We kept the admission that Nullspace models demand as a `dataset` today precisely
    so reviewers can see we're proposing the honest shape, not defending the expedient one.
    The squat's cost (every dataset consumer inheriting entities that don't exist) is spelled
    out under _Detailed design_ and _Alternatives_.

Net: the copy-runnability and correctness points (1–4) are fixed in place; the modelling
questions the review surfaced (5–9) are now first-class _Unresolved questions_ so they're
tracked in the open rather than assumed away; and the core thesis — demand as a new
first-class entity — is unchanged.
