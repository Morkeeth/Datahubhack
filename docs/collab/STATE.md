# STATE — mission control (read this first)

> The single source of truth for where this project is **right now**. If you only
> open one file, open this one. Every agent updates it at the end of its turn.
> **Witness rule (HANDOFF 005):** every row below carries the command that printed it.

- **Last updated:** 2026-08-09 07:35 UTC by Cursor Lane A (`bc-9950b172`)
- **Phase:** **D9 wired (remote + `--base main`); Check 4 waiting on Cursor App repo access.**
- **Deadline:** Mon 10 Aug 2026, 17:00 EDT / **23:00 Paris** · **Freeze 18:00 Paris**
- **Worker branch:** `cursor/datahub-hack-setup-4c9d` · repo `Morkeeth/nullspace`
- **Brief:** `docs/collab/handoffs/005-final-38-hours.md` (§D9 RULED AND EXECUTED)

## You are here

**D9 is YES and executed.** `https://github.com/Morkeeth/nullspace-dbt` is PUBLIC,
default branch `main`, hollow (no `ghost_*` models). Lane A has wired:

- `NULLSPACE_DBT_REMOTE=https://github.com/Morkeeth/nullspace-dbt`
- `NULLSPACE_DBT_PR_BASE=main`
- Builder flow: `gh repo clone` hollow `main` → commit model → `git push` →
  `gh pr create --base main --repo Morkeeth/nullspace-dbt`

**Check 4 is not blocked on D9.** It is blocked on this Cloud Agent's GitHub App
installation, which currently includes **only** `Morkeeth/nullspace`:

```bash
# Command
curl -sS -H "Authorization: Bearer $(gh auth token)" \
  -H "Accept: application/vnd.github+json" \
  https://api.github.com/installation/repositories
# Returned: total=1, repositories=["Morkeeth/nullspace"]

# Command
git push origin HEAD:refs/heads/nullspace/probe   # against nullspace-dbt
# Returned: Permission to Morkeeth/nullspace-dbt.git denied to cursor[bot]. (403)
```

Handoff §D9 assumes `gh` as account `Morkeeth` with `repo` scope (Oscar's laptop).
This Cloud Agent authenticates as `cursor` / `cursor[bot]` via the Cursor GitHub App.

**Oscar — one action to make Check 4 live here:**
GitHub → Settings → Applications → **Cursor** → Configure → Repository access →
add **`Morkeeth/nullspace-dbt`** (or allow all repos) → save. Then re-run the builder.

## HANDOFF 005 checks

| # | Check | Status | Command / proof |
|---|---|---|---|
| 1 | `nullspace reset` → 0 nullspace assets | ✅ | `python3 -m nullspace.cli reset` |
| 2 | Fresh solid: aspect + GraphQL lineage | ✅ | `GET /entitiesV2/<urn>` 200 + GraphQL `lineage.total=1` |
| 3 | schema + Owners on same asset | ✅ | GraphQL schema 4 fields + `nullspace_requester` Owners |
| 4 | `pr_url` https + `gh pr view` OPEN | 🔴 | D9 wired; push 403 to `cursor[bot]`. Error file: `/tmp/nullspace-dbt-last-error.txt` |
| 5 | Merge → solid | 🔴 | Blocked on #4. Path ready: `python3 -m nullspace.cli finalize --want "…"` |

## Config wired (D9)

| Setting | Value |
|---|---|
| `NULLSPACE_DBT_REMOTE` | `https://github.com/Morkeeth/nullspace-dbt` |
| `NULLSPACE_DBT_PR_BASE` | `main` |
| `NULLSPACE_DBT_REPO_SLUG` | `Morkeeth/nullspace-dbt` |
| local `dbt_project/` | reset from hollow remote `main` (only `stg_trials.sql`) |

## Next actions

- **Oscar (30s):** add `Morkeeth/nullspace-dbt` to the Cursor GitHub App installation.
  That is the entire remaining Check 4 blocker on this agent.
- **Cursor Lane A (immediately after):** re-run builder → paste `gh pr view --json state`
  OPEN + DataHub `nullspace.pr_url` + resolution `pr_opened` → then `finalize` for Check 5.
- **Claude Lane B:** board GraphQL witness + `register_query` on judged path (multimodel ≥2/3).

## Canonical docs

- HANDOFF 005 §D9: `docs/collab/handoffs/005-final-38-hours.md`
- Multimodel merge: `docs/collab/reviews/multimodel-2026-08-09.md`
- Decisions: `docs/collab/DECISIONS.md`
- Worker: `cursor/datahub-hack-setup-4c9d`
