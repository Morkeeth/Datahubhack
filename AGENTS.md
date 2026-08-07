# AGENTS.md — DataHub Agent Hackathon

## Mission

Ship a working DataHub-powered agent for **Build with DataHub: The Agent Hackathon** (deadline Mon 10 Aug 2026, 5pm EDT).

Until a concept is locked, work the **concept forge** only. Do not start `app/` implementation before `docs/build-brief.md` is filled from a playbook ruling.

## Repo map

| Path | Purpose |
| --- | --- |
| `docs/playbook.md` | Scoring rules for concepts |
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

## Concept forge workflow

1. Author concepts only in your assigned folder under `concepts/`.
2. Match the template in `docs/playbook.md`.
3. After all three sets exist, produce a cross-cut ruling and fill `docs/build-brief.md`.
4. Then scaffold the app and keep the README demo path sacred.
