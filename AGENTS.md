# AGENTS.md — DataHub Agent Hackathon

## Mission

Ship a working DataHub-powered agent for **Build with DataHub: The Agent Hackathon** (deadline Mon 10 Aug 2026, 5pm EDT).

The concept forge is closed. **Join Treaty** is locked in
`docs/build-brief.md`; implement only that scoped MVP. Do not reopen ideation or
add broad Nullspace/lineage-repair features.

## Repo map

| Path | Purpose |
| --- | --- |
| `docs/playbook.md` | Scoring rules for concepts |
| `docs/final-ranking.md` | Final ruling and competitive analysis |
| `docs/build-brief.md` | Locked winner + ship scope |
| `concepts/{grok,gpt,third}/` | Independent concept sets |
| `scripts/setup-datahub.sh` | Local DataHub Docker + sample data |
| `scripts/install-deps.sh` | Cloud/local Python + MCP warm install |
| `examples/` | Offline artifacts for judges |
| `LICENSE` | Apache-2.0 (required) |

## Hard rules

- Stranger must go README → demo in &lt;3 minutes
- Judges use **local Docker DataHub**, not a private instance
- Prefer MCP Server and/or Agent Context Kit; write back to the graph when it strengthens the story
- Keep the demo path boring and reliable over ambitious scope

## Local DataHub

```bash
bash scripts/install-deps.sh
bash scripts/setup-datahub.sh
bash scripts/check-datahub.sh
```

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
- `start` brings up the Docker daemon; it does **not** auto-launch full DataHub quickstart (too heavy for every boot).
- When a task needs a live catalog, run `bash scripts/setup-datahub.sh` once, then verify with `bash scripts/check-datahub.sh`.
- Secrets: put `DATAHUB_GMS_TOKEN` (and optional OpenAI/Anthropic keys) in the Cloud Agents Secrets tab — never commit tokens.
- Ports forwarded: `9002` (UI), `8080` (GMS), `3000` (app).
- Prefer committing on branch `cursor/<name>-4c9d` and opening a PR against `main`.

### Verified setup notes (non-obvious)

- Nested Docker needs `fuse-overlayfs`. Docker 29 defaults to the containerd snapshotter, which ignores the `fuse-overlayfs` storage-driver, so `.cursor/Dockerfile` sets `features.containerd-snapshotter: false` in `daemon.json`. Keep that or quickstart can fail to start containers in the VM.
- Sample data: the pinned CLI (`acryl-datahub 1.6.0.6`) has no working `datahub datapack load showcase-ecommerce` (missing bundled resource), so `scripts/setup-datahub.sh` logs a graceful failure for that step. To load a live catalog for demos, run `datahub docker ingest-sample-data` after quickstart — it seeds ~7 sample datasets.
- Quickstart pulls DataHub `v1.7.0` images (~a few minutes on first boot) and runs 6 containers (gms, frontend, mysql, kafka-broker, opensearch, actions). Wait for `datahub-datahub-gms-quickstart-1` to be `healthy` before querying.
- The DataHub CLI runs on Python 3.12 here and prints a benign "Python versions above 3.11 are not actively tested" warning; the CLI and Agent Context Kit work fine. The image ships Python 3.11 as `python3`; a JIT (non-Build) pod may only have 3.12, and `scripts/install-deps.sh` falls back to it automatically.
- Agent read/write to the graph works via the new SDK client that Agent Context Kit wraps: `from datahub.sdk import DataHubClient; client = DataHubClient.from_env()` (reads `~/.datahubenv`, written by `datahub init --username datahub --password datahub`). Wrap tools with `datahub_agent_context.DataHubContext(client=client)`.

## Locked build workflow

1. Treat `docs/build-brief.md` as the scope contract.
2. Build the five must-have capabilities before any nice-to-have.
3. Keep verdicts deterministic and require positive evidence; abstain on gaps.
4. Persist native DataHub metadata and prove it via read-after-write.
5. Keep the README-to-demo path under three minutes.
