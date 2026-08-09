# STATE — mission control (read this first)

> Every witness row names the **host** it was witnessed on and the command that
> printed it. Night-run receipts from another host are not reused as truth here.

- **Last updated:** 2026-08-09 ~12:30 UTC by Cursor Lane A
- **Host:** `cursor` (Cloud Agent VM)
- **Phase:** First-class DataHub aspects — structured properties, Query contracts, ownership from first miss, institutionalMemory PR links, merge webhook
- **Deadline:** Mon 10 Aug 2026 · **Freeze 18:00 Paris** (more build time — stay ambitious)
- **Worker branch:** `cursor/datahub-hack-setup-4c9d`

## This turn (ambition)

Maintainer kill R5 (“KV in a costume”) answered on stock GMS v1.7 without a rebuild:

| Native construct | Witness (host `cursor`) |
|---|---|
| `structuredProperties` `nullspace.demand/state/want` | smoke want `ambitious first-class lifecycle` → demand=3.0, state=ghost |
| `Ownership` from **first miss** | 3 `nullspace_requester` owners before solidify |
| `Query` entities for contracts | `nullspace.query_urns` + `contracts_for` reads QueryProperties |
| `institutionalMemory` | PR URL on Links tab |
| `NullspaceDemandSource` parity | structured props + ownership + Queries in workunits |
| Merge webhook | `python3 -m nullspace.webhook` on :8790 |

Dual-write of `customProperties` kept so Lane B GraphQL board needs no change.

## Handback — Lane B

`mcp_server.py` ~163–168 still warns *"recorded locally"* — still yours.

## Next (optional)

- Point GitHub webhook at hosted `:8790` for hands-free solidify-on-merge
- Open OSS PR to `datahub-project/datahub` with this connector (Oscar / Lane B filing)
- Submission package remains Lane B
