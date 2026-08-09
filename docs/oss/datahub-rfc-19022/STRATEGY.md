# STRATEGY — what to ship tonight for the upstream contribution

_Consensus from a multi-model pass (hostile judge / cold stranger / DataHub maintainer
lenses). This is the decision, not a menu._

## Decision

**Harden the RFC only. Do not open the `NullspaceDemandSource` connector PR tonight.**

The judged upstream artifact is the RFC at
https://github.com/datahub-project/datahub/pull/19022. The whole package in this directory
exists to make that one PR as strong as it can be, and to let Oscar apply it in ~5 minutes
after his recording.

## Why (consensus reasoning)

1. **A strong RFC beats a rushed connector.** An RFC is judged on the clarity and honesty of
   the argument; it *wins* by leaving the hard parts open in writing (atomic append,
   `resolvedBy` relationship, lifecycle enforcement, requester spoofing, URN collisions).
   A connector is judged on whether the code is correct, tested, and idiomatic to
   `metadata-ingestion` — none of which we can guarantee against the sponsor's repo tonight.

2. **A weak connector PR actively hurts.** A drive-by source PR opened hours before the
   deadline, against DataHub's ingestion conventions, invites a "this isn't ready" review on
   the exact repo we're trying to impress. Worse, it would ship the `dataset`-squat modelling
   that the RFC explicitly argues against — contradicting our own contribution.

3. **Sequencing is the honest story.** RFC first (argue the shape), connector second
   (implement the agreed shape), each referencing the other. That's how DataHub's own process
   works, and saying so is more credible than dumping code.

4. **Time risk.** Tonight's remaining budget goes to the video and the demo reset, not to
   fighting `metadata-ingestion` entry points and recipe docs under deadline.

## What we DO ship tonight

- Polished RFC body (`19022-demand-side-metadata.md`) with the correctness fixes and the
  open questions written up.
- `APPLY.md` so Oscar's post-recording apply is mechanical.
- `REVIEWER-RESPONSE.md` to answer the automated review on the PR.
- `DEVPOST-BLURB.md` and the SUBMISSION.md pointer so the contribution is legible to judges.

## What we DEFER (and where it's already sketched)

- The `NullspaceDemandSource` metadata-ingestion connector. Design already exists at
  `docs/design/oss-nullspace-demand-source.md`. When opened, it **references #19022** and
  implements the RFC's new-entity shape, not the current `dataset` squat.

## Tripwire

If, against this decision, someone wants to open the connector PR tonight: it must (a)
reference #19022 in its description, (b) be marked draft, and (c) not claim the RFC's
modelling is settled. Absent all three, don't open it.
