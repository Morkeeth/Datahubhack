# Multimodel review — 2026-08-09

Union of three independent LENS runs (hostile judge / cold stranger / DataHub
maintainer). Sort key: `confirmed_by` desc, then score cost.

Known-bad excluded from scoring (already owned): lineage REST `/aspects` NPE on
this GMS; `pr_url` file:// until Cursor App includes `nullspace-dbt`; no video.

| rank | defect | confirmed_by | lenses | file:line or repro | cost if unfixed | fix (≤2 lines) | status |
|---|---|---|---|---|---|---|---|
| 1 | Board / cold-reveal store mismatch — eval writes one JSON file, board reads another (blank aha) | **3/3** | 1, 2, 3 | Was README `NULLSPACE_STORE=/tmp/nullspace-eval-fresh.json` vs `up.sh` default `/tmp/nullspace-ghosts.json` + `board.py` | Reveal is empty at the exact moment that matters | Share one store; board should read GraphQL | **PARTIAL — README/demo aligned to default store (Lane A)**; GraphQL board still **OPEN — Lane B** |
| 2 | Hosted board is file sidecar, not GraphQL witness | **3/3** | 1, 2, 3 | `nullspace/board.py` `FileGhostStore()` | Sponsor-native / “recording API” risk | `/api/board` ← GMS GraphQL | **OPEN — Lane B** |
| 3 | Cold / unique demand falsely `found` via fuzzy search | **2/3** | 2, 3 | Was `eval --cold` → `status='found'` | Judge path dies before aha | Exact-want + token match | **FIXED** (`ghosts.py`); cold eval 16/0/1 |
| 4 | Disclosed fallback fabricates trials schema without contracts | **2/3** | 1, 2 | `builder.plan_for_demand` fallback; judged path without `register_query` | Looks staged | Register queries on judged path | **OPEN — Lane B** |
| 5 | README claimed eval reads resolution history; eval does not | **1/3** (+ hard claim) | 1 | Was `README.md` cold-reveal paragraph vs `eval_nullspace.py` | Automatic top-3 false claim | Drop claim or add assertion | **FIXED** — README wording corrected |
| 6 | `demo.sh` ran offline `cli demo` for-loop, not MCP agents | **1/3** | 1 | Was `scripts/demo.sh` → `nullspace.cli demo` | Headline demo undercuts “independent agents” | Point at `eval_nullspace.py` | **FIXED** — `demo.sh` now runs cold eval |
| 7 | One-command `docker compose up` does not start board | **1/3** | 1 | Was `README.md` vs `up.sh` | Stranger stalls at :8787 | Document `./scripts/up.sh` | **FIXED** — README one-command is `up.sh` |
| 8 | STATE witness rows without commands | **1/3** (+ hard blocker) | 3 | Was stale STATE table | Credibility loss | Command-backed rows | **FIXED** |
| 9 | Late miss could wipe solid schema/lineage | **1/3** (+ hard blocker) | 1 | `_from_datahub` / empty solid emit | Mid-demo data loss | Hydrate + refuse empty | **FIXED** |
| 10 | Eval CHECK 5 accepts `refused` as PASS | **1/3** | 1 | `scripts/eval_nullspace.py:191` | Inflates pass count | Accept only `solidified` | **OPEN — Lane B** (eval owned by Lane B) |
| 11 | OSS contribution absent | **1/3** | 3 | no upstream PR yet | OSS bonus = 0 | Docs/recipe PR | **OPEN — Oscar/Claude** (fork exists per HANDOFF 005) |
| 12 | GMS down degrades to local JSON | **1/3** | 3 | `mcp_server.py` | Not sponsor-native | Fail closed | **OPEN — Lane B** |
| 13 | Lifecycle in `customProperties` = KV-with-badge until solid | **1/3** | 3 | `emit.py` ghost-phase | Maintainer smell | Accept for freeze | **ACCEPT** |
| 14 | Demand identity caller-asserted | **1/3** | 1 | `mcp_server._identify` | Spoofable “3 agents” | Disclose, don’t overclaim | **ACCEPT** |
| 15 | `RULING.md` missing | **1/3** | 2 | repo root | Scope doc hard to find | Pointer file | **FIXED** |
| 16 | Docs say `python` not `python3` | **1/3** | 2 | verify blocks | First command fails | Prefer `python3` | **OPEN — tiny** |

## Build queue (only ≥2/3 or hard blockers)

1. **Board = GraphQL witness** — Lane B (**3/3**).
2. **Judged path must `register_query`** — Lane B (**2/3**).
3. ~~Store mismatch / blank board on README path~~ — Lane A aligned README+demo to shared default store; GraphQL still required.
4. ~~Fuzzy false `found` / STATE / late-miss wipe / README overclaim / demo.sh / up.sh docs / RULING.md~~ — done (Lane A).

## Do not touch

- Honest `file://` boundary until Cursor App includes `nullspace-dbt` (or `NULLSPACE_DBT_TOKEN`).
- Read-after-write harness (`emit._verify_solid_witness`, `wait_for_*`).
- `nullspace reset` + warehouse `EXPLAIN` gate + builder receipt replay.
- File-lock transaction around demand updates.

## Single frames (per lens)

- **L1:** *Miss → shared board → builder → solid dataset with me as Owner* — frame is retellable only if the board shows the miss (defects 1–2).
- **L2:** *Their own agent asks; a hollow node appears; demand counts in public.*
- **L3:** *The graph had the story; the URL at :8787 was reading an empty temp file.*

Merged memorable frame to protect: **a stranger’s agent misses → ghost demand appears on a board that is reading DataHub → builder solidifies with schema/lineage/owners the graph returns.**
