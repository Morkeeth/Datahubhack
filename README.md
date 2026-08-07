# Join Treaty — DataHub Agent Hackathon

Parallel multi-model ideation for **Build with DataHub: The Agent Hackathon** (deadline Mon 10 Aug 2026, 5pm EDT).

Public repo · Apache-2.0 · local DataHub Docker for judge demos.

## Purpose

The concept forge is complete. **Join Treaty** is the locked winner:

> Mine the equality joins teams repeat in DataHub's query history, verify each
> one against schema and column profiles, and write it back as a native ER model
> relationship — the join graph that lineage never captures.

Read the [final ranking](docs/final-ranking.md) and locked
[build brief](docs/build-brief.md).

## Quick setup

```bash
# 1) Tooling (CLI, Agent Context Kit, MCP warm cache)
bash scripts/install-deps.sh

# 2) Local DataHub + sample data (Docker required)
bash scripts/setup-datahub.sh

# 3) Sanity check
bash scripts/check-datahub.sh
```

- UI: http://localhost:9002 — login `datahub` / `datahub`
- GMS: http://localhost:8080
- Details: [infra/datahub/README.md](infra/datahub/README.md)

## Concept forge

| Folder | Owner |
| --- | --- |
| [concepts/grok](concepts/grok) | Grok concepts |
| [concepts/gpt](concepts/gpt) | GPT concepts |
| [concepts/third](concepts/third) | Competitive-whitespace pass |

Rules and scoring: [docs/playbook.md](docs/playbook.md). Final ruling:
[docs/final-ranking.md](docs/final-ranking.md). Agent instructions:
[AGENTS.md](AGENTS.md).

## Constraints (hard)

- ~2 build days after concept lock; agents write the code
- Stranger demos from README in &lt;3 minutes
- Live URL + &lt;3-min video + Apache-2.0 public repo
- DataHub local Docker — judges cannot reach a private instance

## Cloud agents

`.cursor/environment.json` builds a Docker-capable image and installs DataHub tooling on each Build. Docker starts with the environment; run `scripts/setup-datahub.sh` when a live catalog is needed.

## Status

**Ideation closed. Join Treaty locked; implementation is next.**

## License

Apache-2.0 — see [LICENSE](LICENSE).
