# STATE — mission control (read this first)

> Every witness row names the **host** it was witnessed on and the command that
> printed it. Night-run receipts from another host are not reused as truth here.

- **Last updated:** 2026-08-10 ~10:05 UTC by Cursor Lane A (stranger-cold-run)
- **Host:** Oscar laptop (`colima`)
- **Phase:** Stranger cold-clone proven on remapped ports; blockers fixed and
  pushing to `main`
- **Worker branch:** `stranger-cold-run` → `main`

## This turn

| Slice | Status | Witness |
|---|---|---|
| Fresh clone of `main` @ `b049ac6` | ✅ | `git clone …/nullspace.git ~/tmp/nullspace-stranger-cold` |
| `install-deps.sh` pins classic dbt | ✅ | `dbt --version` → core 1.12.0 / postgres 1.9.1 (not Fusion) |
| Remapped compose (live `datahub-hack` untouched) | ✅ | project `stranger-cold`; GMS `:18080` PG `:15432` board `:18787` MCP `:18788` |
| Substrate ready | ✅ | GMS+warehouse+ingestion **84s** (warm images) |
| README cold eval (pre-fix) | ❌→fixed | CHECK 5 `status='claimed'` after real PR (MCP honesty); eval now finalizes |
| Solid table SELECT | ✅ | `ecommerce.ghost_fresh_…` 2 rows via `dbt_run`; MRR ghost 3 rows |
| `remote_agent.py --query` ×3 → claim → PR → merge → solid | ✅ | PR `#19`; `SELECT *` → enterprise/scaleup/startup MRR |
| `sources.yml` overwrite bug | ✅ fixed | second claim wiped `trials`; `_merge_source_tables` + test |
| README example query unfulfillable | ✅ fixed | was `account_id/health_score`; now seeded `segment/mrr` |
| preflight board `:8787` vs live `:8790` | ✅ fixed | respects `NULLSPACE_BOARD_URL` / `NULLSPACE_BOARD_PORT` |
| up.sh board port | ✅ fixed | respects `NULLSPACE_BOARD_PORT` |

## Remap line (only intentional stranger diff)

`18080←8080, 19002←9002, 19092←9092, 15432←5432, 18787←8787, 18788←8788`; compose project `stranger-cold`. Live `datahub-hack` on `:8080` left alone.

## Honest timing

- Warm images: substrate **84s** + eval path under **3 min** once finalize is in CHECK 5.
- Cold Docker pull: **not** under 3 minutes — README now says so.
- `install-deps` here was **10s** (warm pip cache); a true empty machine is longer.

## Still open

1. Live public board (`com.morkeeth.nullspace` / `:8790`) was **down** this morning (Colima off; GMS alone unhealthy). Not restarted by this lane.
2. Durable public hostname — see handback (named Cloudflare tunnel).
3. P0 RFC #19022 / X clip — unchanged ownership (Oscar/Claude).

## Handback

Durable hostname cheapest path: Cloudflare **named** tunnel (`cloudflared tunnel create` + DNS CNAME, or stable `*.cfargotunnel.com`) — survives restart; ~10–15 min once `cloudflared login` is done. Quick tunnels will keep minting new hostnames.
