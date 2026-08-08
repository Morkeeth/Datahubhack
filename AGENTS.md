# Nullspace — agent brief

## What this is

Hackathon product: **Nullspace** (demand-side metadata). Law is in `RULING.md`.
The concept is decided. Do not reopen ideation or revive the kill list.

## Collaboration

Read these before changing code:

1. `docs/collab/STATE.md`
2. the newest brief under `docs/collab/handoffs/`
3. `docs/collab/LANES.md`

Respect the lane contract. Update `STATE.md` at handoff and append decisions to
`DECISIONS.md`.

## Verify

```bash
# unit / contract tests (no Docker required)
python3 -m pytest nullspace/tests -q

# e2e (needs the repository DataHub Compose stack)
./scripts/up.sh
./scripts/demo.sh
# Done when: DataHub returns one ghost at demand>=3, then schema + lineage +
# native requester owners after it goes solid.
```

## Hard constraints

- DataHub is the witness. Report what DataHub returns, never only what was sent.
- **No mocks** for the ghost loop. No pre-baked JSON replay or fake writeback.
- DataHub is local Docker; stranger must reproduce from README in &lt;3 min.
- Live URL is a read-only board over the same stack, not a recording API.
- Every refusal names its reason and the exact shortfall.
- Never claim a real PR while `pr_url` is `file://`.
- Never `git add -A`; `dbt_project/` has a nested `.git`.
- Tracks: Agents That Do Real Work + Metadata-Aware Code Generation (dbt PR).

## Repo map

| Path | Purpose |
| --- | --- |
| `nullspace/` | Shipping product |
| `compose.yaml` | One-command DataHub + seeded warehouse substrate |
| `infra/warehouse/init.sql` | Real writable warehouse seed |
| `infra/datahub/postgres.yml` | Warehouse-to-DataHub ingestion recipe |
| `app/join_treaty/` | Verified read-after-write/idempotency reference only |
| `docs/collab/` | Mission control, lane contract, handoffs, decisions |

## Local DataHub

Run `docker compose up -d` from a clean clone. It starts DataHub, a writable
Postgres warehouse, and one-shot metadata ingestion. Wait for
`metadata-ingestion` to exit `0`, then run `bash scripts/check-datahub.sh`.

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
- `start` brings up Docker; it does not auto-launch Compose.
- When a task needs a live catalog, run `docker compose up -d`, wait for `metadata-ingestion` to exit `0`, then verify with `bash scripts/check-datahub.sh`.
- Put real tokens in Cloud Agents Secrets; never commit them.
- Ports: `9002` UI, `8080` GMS, `8787` Nullspace board.

### Verified setup notes (non-obvious)

- Nested Docker uses `fuse-overlayfs`; the cloud image configures the daemon in
  `.cursor/Dockerfile`. There is no repository `daemon.json` to edit.
- The repository Compose stack pins DataHub `v1.7.0` and Postgres `16.4`. The `metadata-ingestion` container profiles the live `ecommerce` schema and writes it to GMS; it is intentionally a successful one-shot container while the services stay running.
- Warehouse credentials are local-only (`agent` / `agent`, database `warehouse`). The role owns the seeded schema, so agents can exercise real reads and transactional writes.
- Do not start `datahub docker quickstart` alongside the repository stack: both bind ports `8080` and `9002` and use separate state. Use `docker compose down --volumes` for a destructive clean reset.
