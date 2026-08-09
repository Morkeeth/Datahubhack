# SUBMISSION AUDIT — multi-model review

**When:** 2026-08-09 ~20:20 UTC · **Branch:** `cursor/datahub-hack-setup-4c9d`  
**Models:** Bugbot · security-review · Opus (submission) · GPT-5.5 (judge honesty) · Sonnet (code-path)  
**Lane A wrap:** design comps filed; UI pick deferred (Oscar has another idea). `board.html` stays Darkroom.

---

## Consensus verdict: **SHIP WITH GAPS / RISKY**

The ghost loop is real (DataHub SDK writes + GMS read-back; Law 2 subtraction holds; Scar Tissue steal only).  
What fails a 3-minute judge is **presentation surface**, not the concept.

---

## P0 — fix or script around before recording

| # | Finding | Evidence | Owner |
|---|---|---|---|
| 1 | **Board is polluted** — ~80+ `throughput_want_*` bury the demo | Live GraphQL counts; board sorts solid then demand-desc | Oscar / whoever records: `python3 -m nullspace.cli reset` then `scripts/demo.sh` |
| 2 | **"Real PR" is `file://` on Cursor host** | `gh` has no push to `nullspace-dbt`; no `NULLSPACE_DBT_TOKEN` (D18) | Record where token exists, or never say "opened a PR" while showing `file://` |
| 3 | **dbt Fusion cannot run Postgres** → silent CTAS fallback | `dbt-postgres` unpinned → `dbt-core 2.0.0a5`; `dbt1005` | Pin `dbt-core<2` or say "warehouse CTAS (D33)" aloud |
| 4 | **Walk-the-book is not what `demo.sh` runs** | `demo.sh` → `eval_nullspace.py` → direct `claim_and_build` | Video must run `python3 -m nullspace.builder` (or watcher) for the money shot |

---

## P1 — honesty / stranger / MCP

| # | Finding | Evidence |
|---|---|---|
| 5 | **Buffered ghost emits may not hit GMS until process exit** | `emit_ghost` buffers `state=ghost`; `_mirror` checks in-memory witness; MCP long-lived sessions hide demand until atexit flush (Sonnet live probe) |
| 6 | **SP defs still 422 on this GMS** (ES `nullspace_demand` collision) → customProperties-only | Live 422; fallback works for ghosts |
| 7 | **`open_demand` / MCP builder pre-check use unhydrated file store** | `mcp_server.py` vs `cli._ns` hydrate |
| 8 | **Harvest "1,205 → 41"** unverifiable from clean clone | No committed corpus in `examples/` |
| 9 | **Public MCP refuses `claim_and_build`** | By design (`NULLSPACE_PUBLIC`) — do not claim judges fulfill via public MCP |
| 10 | **Schema mismatch risk** | `install-deps` profile schema `nullspace` vs builder default `ecommerce` vs `agents_return` |

---

## P2 — security / hygiene (demo localhost OK)

- Join Treaty `POST /apply` + GMS auth off — medium if exposed beyond localhost.
- Compose defaults (weak secrets, open `8080`/`5432`) — fine local; dangerous if tunneled raw.
- Webhook HMAC no-op when `NULLSPACE_WEBHOOK_SECRET` empty.
- Cloud `environment.json` omits board port `8787`.
- Cold eval vs real-PR path: with push creds + no auto-merge, CHECK 5 may not see `solid` until finalize.

---

## Law compliance (all models agree)

| Constraint | Status |
|---|---|
| No mocks on ghost loop | ✅ |
| DataHub load-bearing / Law 2 | ✅ |
| Kill list not revived | ✅ |
| Scar Tissue = resolution on URN only | ✅ |
| Never claim PR while `file://` (code) | ✅ code honest · ⚠️ board can still *display* solid+`file://` from CTAS path |

---

## What to show in 3 minutes

1. Reset board → empty / one want  
2. Three MCP misses → demand ≥3 on **DataHub-backed** board  
3. `python3 -m nullspace.builder` — **skipped** churn/NRR, **claiming** pipeline coverage  
4. Open real `https://` PR (or disclose local reference)  
5. Board plate inverts to solid + schema/lineage  
6. `agents_return.py` — blocked queries return rows  
7. Optional: `without-datahub.sh` — board gone  

## What NOT to claim

- Public hosted MCP builds / opens PRs  
- Every solid came from `dbt run` (unless receipt `method: dbt_run`)  
- Design comps (Ranked/Stage) are the shipped board  
- Harvest 1,205 unless artifact is committed  

---

## Go / no-go for Oscar tonight

- [ ] `nullspace reset` → board clean  
- [ ] Recording host has write to `nullspace-dbt` **or** scripted honesty about `file://`  
- [ ] Working `dbt-core<2` **or** disclose CTAS  
- [ ] Video uses walk-the-book CLI, not only `demo.sh`  
- [ ] Hosted read-only board URL up  
- [ ] Soften or commit harvest numbers  

**Already green:** 24 unit tests · GMS/warehouse healthy · PR #2 merged · Law 2 script · no-mocks spine.

---

## Design wrap

Comps + screenshots: `docs/design/board-options-v2.html`, `docs/design/options/{01,02,03}-*.png`.  
Oscar has another design idea — **do not ship a board restyle from these comps** until that lands.
