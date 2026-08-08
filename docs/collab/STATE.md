# STATE — mission control (read this first)

> The single source of truth for where this project is **right now**. If you only
> open one file, open this one. Every agent updates it at the end of its turn.

- **Last updated:** 2026-08-09 ~02:2x Paris by Claude (Opus 5), terminal session
- **Repo:** `Morkeeth/nullspace` (renamed from `Datahubhack`) · PUBLIC · Apache-2.0
- **Phase:** Core pipeline WORKS end to end. Builder agent is still a function, not an agent.
- **Deadline:** Mon 10 Aug 17:00 EDT / **23:00 Paris — ~45h**

## You are here

Concept decided (D8: Nullspace). The pipeline runs against a live DataHub and every
claim below was read back from the graph, not from a log line.

**Cursor has not run yet.** Every commit on this branch is Claude's. Oscar has the
outcome-shaped prompt (four outcomes, see `handoffs/004` + the session's final message)
and will kick it off. Review is Sunday.

## Verified working — do not rebuild

| Capability | Evidence (read back from DataHub) |
|---|---|
| Real agents, not a for-loop | 3 separate MCP client processes converge on one ghost; identity from `clientInfo` |
| Demand converges | `demand` 1→2→3; a 4th agent increments and does **not** duplicate the ghost |
| Contracts | agents register SQL against a table that doesn't exist; union of columns = the schema |
| **Schema derived from demand** | `schemaMetadata` = `rep_id, pipeline_value, quota, coverage_ratio` |
| **Requesters as native Owners** | `ownership` = 3 agents, type `CONSUMER` — renders in the V2 UI |
| Solid tag | `urn:li:tag:solid` |
| Acceptance eval | `scripts/eval_nullspace.py` → **13 pass, 0 fail** |
| Judge-grep (playbook #32) | 2 hits, both benign |

**Two fakes killed on 8 Aug:** the hardcoded `schema_fields=[cohort_id, trials,
conversions, trial_to_paid_rate]` applied to every ghost, and the hardcoded trial-to-paid
dbt SQL. Both now derive from what agents actually asked for.

## THE ONE OPEN THING THAT MATTERS

> **The builder agent is still a function call.**

`build_and_solidify()` cannot choose, cannot refuse, cannot write SQL. The pitch says "a
builder agent claims the ghost and writes the model" — that is false in exactly the way
the three consumer agents were false before they became real MCP clients. **This is
Outcome 1 in the Cursor prompt and it outranks everything else.**

## Still open

| Item | Owner | Note |
|---|---|---|
| Builder as a real agent (Outcome 1) | Cursor | the ambitious one; also the riskiest |
| Lineage still 0 upstream/downstream (Outcome 2) | Cursor | do **not** add `systemMetadata` to the proposal — that caused a 400 for an hour |
| Stranger path breaks at command 1 (Outcome 3) | Cursor | CLI not on PATH; can lose the entry on its own |
| One real OSS PR to DataHub (Outcome 4) | Cursor | a judged dimension sitting at **zero** |
| **D9 — public remote for `dbt_project`** | **Oscar** | unruled after 4 asks. PR claim is cut until it lands |
| Design direction (M1 Darkroom / M2 / paste inspiration) | Oscar | `docs/design/design-prompt.md` |
| Tagline ruling | Oscar | `docs/submission/taglines.md` |
| Video + description | not started | **Submission Quality is a judged dimension at zero** |
| `AGENTS.md:78` documents a `daemon.json` that does not exist | Cursor | `git ls-files -- daemon.json` → nothing |
| `compose.yaml` hardcodes token salt/signing keys | Cursor | local demo values, not real secrets; gitleaks flags 6 |

## Machine state left running (Oscar's laptop)

- DataHub stack up: 6 containers under `datahub-hack`, colima 4 CPU / 6 GiB
- An **SSH tunnel** forwards 8080/9002/5432 from the colima VM — lima's own
  port-forwarder has been stale since 19 Jul, so without the tunnel GMS answers 200
  inside the container and refuses on the host. Re-open with:
  `ssh -F ~/.colima/_lima/colima/ssh.config -N -f -L 8080:127.0.0.1:8080 -L 9002:127.0.0.1:9002 lima-colima`
- `docker compose` was installed tonight (was missing entirely); plugin dir registered
  in `~/.docker/config.json` (backup at `config.json.bak-2026-08-08`)
- Tear down with `docker compose down` in `~/Datahubhack-jt` when done

## Canonical docs

- Build brief: `docs/collab/handoffs/003-nullspace-roadmap.md`
- Night run + steals + moonshot: `docs/collab/handoffs/004-night-run-2026-08-08.md`
- Lanes: `docs/collab/LANES.md` · Rulings: `docs/collab/rulings/001`, `002`
- Design: `docs/design/design-prompt.md` · Submission: `docs/submission/`
- ⚠️ `docs/final-ranking.md` is **SUPERSEDED** and carries a retraction banner
