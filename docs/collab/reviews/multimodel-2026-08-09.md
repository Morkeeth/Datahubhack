# Multimodel review — 2026-08-09

Union of three independent LENS runs (hostile judge / cold stranger / DataHub
maintainer). Sort key: `confirmed_by` desc, then score cost.

Known-bad excluded from scoring (already owned): lineage REST `/aspects` NPE on
this GMS; `pr_url` file:// until write token; no video.

| rank | defect | confirmed_by | lenses | file:line or repro | cost if unfixed | fix (≤2 lines) | status |
|---|---|---|---|---|---|---|---|
| 1 | Cold / unique demand falsely `found` via fuzzy search (other solids + warehouse noise) | **2/3** | 2, 3 | Was: `eval_nullspace.py --cold` → `status='found'`; root in `ghosts.consumer_search` | Judge path dies before aha | Match solid nullspace by exact want; require majority want-tokens in non-nullspace URNs | **FIXED this turn** (`ghosts.py`); cold eval now `16 passed, 0 failed, 1 pending` |
| 2 | README/board `:8787` reads a different `NULLSPACE_STORE` than the cold eval (sidecar, not GraphQL) | **2/3** | 2, 3 | `nullspace/board.py:16-19`, `README.md` cold reveal, `scripts/up.sh` | Live URL shows empty/stale board after a green eval | Lane B: board reads GMS GraphQL; or `up.sh`+eval share one store | **OPEN — Lane B** |
| 3 | Disclosed fallback fabricates trials schema when no builder plan / contracts | **2/3** | 1, 2 | `builder.py:plan_for_demand` fallback; eval `claim_and_build` without `register_query` | Judge path looks staged (“I asked for X, got trials”) | Lane B: register queries in eval/MCP path; Lane A keeps fallback only as disclosed direct-tool escape | **OPEN — needs Lane B contracts on judged path**; README already labels fallback |
| 4 | STATE witness rows without commands (HANDOFF 005 rule) | **1/3** (+ hard blocker) | 3 | Was `STATE.md` 2026-08-08 table | Credibility loss on “DataHub is the witness” | Re-earn every row with command | **FIXED this turn** — STATE rewritten with command column |
| 5 | Late miss can re-mirror solid with empty schema/upstreams and wipe aspects | **1/3** (+ hard blocker) | 1 | `ghosts._from_datahub` lacked schema hydrate; `emit` subset check | Mid-demo schema/lineage vanish | Hydrate from `solid_witness`; refuse empty solid emit | **FIXED this turn** |
| 6 | Hosted board is file JSON, not GraphQL witness (sponsor-native) | **1/3** (overlaps #2) | 3 | `board.py` `FileGhostStore()` only | Live URL not catalog-native | Board ← GraphQL | **OPEN — Lane B** |
| 7 | OSS contribution absent | **1/3** | 3 | no fork / PR | OSS bonus = 0 | Oscar fork + one docs PR | **OPEN — Oscar** |
| 8 | GMS down degrades to local JSON instead of refusing | **1/3** | 3 | `mcp_server.py` local-only warning | Not sponsor-native | Fail closed when GMS unreachable on miss/build | **OPEN — Lane B** |
| 9 | Lifecycle in `customProperties` = KV-with-badge until solid | **1/3** | 3 | `emit.py` ghost-phase props | Maintainer smell | Accept for freeze; native aspects already on solid | **ACCEPT — do not expand scope** |
| 10 | Demand identity is caller-asserted | **1/3** | 1 | `mcp_server._identify` | “Three agents” is spoofable | Disclose in receipt; don’t overclaim | **ACCEPT — disclose only** |
| 11 | `RULING.md` missing at repo root | **1/3** | 2 | `test -f RULING.md` | Agents/judges can’t find law | Symlink/copy from rulings | **OPEN — tiny** |
| 12 | Docs say `python` not `python3` | **1/3** | 2 | `AGENTS.md` verify block | First command fails on clean Linux | Prefer `python3` | **OPEN — tiny** |

## Build queue (only ≥2/3 or hard blockers)

1. ~~Fuzzy false `found`~~ — done (Lane A).
2. **Board = GraphQL witness / shared store** — Lane B (blocks reveal).
3. **Judged path must register query contracts** — Lane B (kills fabrication frame).
4. ~~STATE command-backed witnesses~~ — done (Lane A).
5. ~~Solid overwrite on late miss~~ — done (Lane A).

## Do not touch

- Honest `file://` boundary until `NULLSPACE_DBT_TOKEN` / write on `nullspace-dbt`.
- Read-after-write harness (`emit._verify_solid_witness`, `wait_for_*`).
- `nullspace reset` (verified hollow).
- Warehouse `EXPLAIN` gate + builder receipt replay.
- File-lock transaction around demand updates.

## Single frames (per lens)

- **L1:** *I asked for a table; you handed me the canned trials model.*
- **L2:** *Their own agent asks; a hollow node appears; demand counts in public.*
- **L3:** *The graph had the story; the URL at :8787 was reading an empty temp file.*

Merged memorable frame to protect: **a stranger’s agent misses → ghost demand appears on a board that is reading DataHub → builder solidifies with schema/lineage/owners the graph returns.** Anything that breaks that frame is above the freeze line.
