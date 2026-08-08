# Nullspace — agent brief

## What this is

Hackathon product: **Nullspace** (demand-side metadata). Law is in `RULING.md`. Do not invent a new concept. Do not revive the kill list.

## Verify

```bash
# unit / contract tests (no Docker required)
python -m pytest nullspace/tests -q

# e2e (needs DataHub up via ./scripts/up.sh)
./scripts/demo.sh
# Done when: board shows ghost demand≥3, a real PR URL exists, then ghost is solid
```

## Hard constraints

- **No mocks** for the ghost loop. No pre-baked JSON replay, no `dryRun` that pretends writeback.
- DataHub is local Docker; stranger must reproduce from README in &lt;3 min.
- Live URL = same stack hosted, **read-only board** over that instance's GraphQL — not a recording API.
- Steal from Scar Tissue **only**: bind resolution history to the URN. Nothing else from the kill list.
- Tracks: Agents That Do Real Work + Metadata-Aware Code Generation (dbt PR).

## Weekend slices (ordered)

1. Ghost upsert + demand increment + board read (GraphQL/REST)
2. Three consumer agents that miss → ghost
3. Builder claims → real dbt PR → solidify on merge
4. Hosted board + &lt;3-min video

Tripwire: if ghost→solid writeback is not visibly working by **Sat 18:00 Paris**, cut to Scar Tissue — not a parallel track.
