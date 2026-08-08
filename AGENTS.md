# AGENTS.md — Nullspace

## Mission

Ship **Nullspace**, demand-side metadata, for Build with DataHub (deadline Mon
10 Aug 2026, 5pm EDT). The concept is decided. Do not reopen or re-rank it.

## Collaboration (read this first, every session)

Many Cursor agents + an external Claude coordinate through the repo, not through
chat. Before doing anything:

1. **Read `docs/collab/STATE.md`** — the single source of truth for the current
   phase, the one open decision, and who moves next.
2. Follow `docs/collab/PROTOCOL.md` (roles + the handoff loop).
3. **Update `docs/collab/STATE.md` at the end of your turn**, and log any decision
   in `docs/collab/DECISIONS.md` (append-only; never silently reopen a decided
   item — add a `SUPERSEDED` entry instead).
4. Agent↔Claude exchanges are numbered files under `docs/collab/handoffs/` and
   `docs/collab/rulings/`, not ad-hoc chats.

## Repo map

| Path | Purpose |
| --- | --- |
| `nullspace/` | Shipping product: demand, builder agent, native DataHub writeback |
| `docs/collab/STATE.md` | Current verified state |
| `docs/collab/LANES.md` | File ownership contract |
| `compose.yaml` | One-command DataHub + seeded warehouse substrate |
| `infra/warehouse/init.sql` | Real writable warehouse seed |
| `infra/datahub/postgres.yml` | Warehouse-to-DataHub ingestion recipe |
| `scripts/setup-datahub.sh` | Detached wrapper around Compose startup |
| `scripts/install-deps.sh` | Cloud/local Python + MCP warm install |
| `examples/` | Offline artifacts for judges |
| `LICENSE` | Apache-2.0 (required) |

## Hard rules

- Stranger must go README → demo in &lt;3 minutes
- Judges use **local Docker DataHub**, not a private instance
- DataHub is the witness: report what it returned, never merely what was sent
- Never claim a PR while `pr_url` is `file://`
- Never `git add -A`; `dbt_project/` has a nested `.git`

## Local DataHub

Run `docker compose up` from a clean clone. It starts DataHub, a writable
Postgres warehouse, and a one-shot metadata ingestion job. Use
`bash scripts/check-datahub.sh` for the end-to-end check and
`bash scripts/query-seeded-entity.sh` for the live GraphQL proof.

UI: http://localhost:9002 (`datahub` / `datahub`)
GMS: http://localhost:8080

After creating a PAT in the UI:

```bash
export DATAHUB_GMS_URL=http://localhost:8080
export DATAHUB_GMS_TOKEN=...
npx -y @acryldata/mcp-server-datahub
```

## Cursor Cloud specific instructions

- Environment is defined in `.cursor/environment.json` (Dockerfile + install/start).
- `install` runs `scripts/install-deps.sh` during Builds.
- `start` brings up the Docker daemon; it does **not** auto-launch the repository Compose stack (too heavy for every boot).
- When a task needs a live catalog, run `docker compose up -d`, wait for `metadata-ingestion` to exit `0`, then verify with `bash scripts/check-datahub.sh`.
- Secrets: put `DATAHUB_GMS_TOKEN` (and optional OpenAI/Anthropic keys) in the Cloud Agents Secrets tab — never commit tokens.
- Ports forwarded: `9002` (UI), `8080` (GMS), `3000` (app).
- Prefer committing on branch `cursor/<name>-4c9d` and opening a PR against `main`.

### Verified setup notes (non-obvious)

- Nested Docker needs `fuse-overlayfs`. Docker daemon configuration belongs to
  the environment image; this repository intentionally has no `daemon.json`.
- The repository Compose stack pins DataHub `v1.7.0` and Postgres `16.4`. The `metadata-ingestion` container profiles the live `ecommerce` schema and writes it to GMS; it is intentionally a successful one-shot container while the services stay running.
- Warehouse credentials are local-only (`agent` / `agent`, database `warehouse`). The role owns the seeded schema, so agents can exercise real reads and transactional writes.
- Do not start `datahub docker quickstart` alongside the repository stack: both bind ports `8080` and `9002` and use separate state. Use `docker compose down --volumes` for a destructive clean reset.
- The DataHub CLI runs on Python 3.12 here and prints a benign "Python versions above 3.11 are not actively tested" warning; the CLI and Agent Context Kit work fine. The image ships Python 3.11 as `python3`; a JIT (non-Build) pod may only have 3.12, and `scripts/install-deps.sh` falls back to it automatically.
- Agent read/write to the graph works via the new SDK client that Agent Context Kit wraps: `from datahub.sdk import DataHubClient; client = DataHubClient.from_env()` (reads `~/.datahubenv`, written by `datahub init --username datahub --password datahub`). Wrap tools with `datahub_agent_context.DataHubContext(client=client)`.

### Join Treaty reference (`app/`)

- Join Treaty is not the product. Its read-after-write and idempotency code is a
  verified reference only. Tests remain useful: `pytest app/tests`.
- The pipeline needs the substrate up (`docker compose up`) and `DATAHUB_GMS_URL=http://localhost:8080`. It reasons over the ingested `ecommerce` Postgres datasets, so run it only after `metadata-ingestion` has exited `0`.
- `join-treaty audit`/`serve` enumerate Query entities via the **search index**, which is async: after `join-treaty seed`, wait a few seconds before auditing or newly seeded queries may be missing. Aspect reads (schema/profile/ER/receipt) are immediate.
- `DatasetProfile` is timeseries — read it with `get_latest_timeseries_value`, not `get_aspect`. Cardinality inference keys off `fieldProfiles[].uniqueProportion`.
- Writes are idempotent by construction: query URNs hash the SQL, and the ER relationship URN + receipt key are derived from the join, so re-running `seed`/`apply` overwrites identically (`apply` reports `0 new`).
- DataHub OSS V2 UI does not render `ERModelRelationship`; verify writes via GraphQL/`get_aspect` and the `join_treaty:*` custom property in each dataset's Properties tab. The web view runs on port `3000`.

## Locked build workflow

1. Run `python3 scripts/eval_nullspace.py` before and after changes.
2. Keep the causal chain: miss → demand → builder decision → claim → solid.
3. Persist native DataHub metadata and prove it via read-after-write.
4. Keep the README-to-reveal path under three minutes.
