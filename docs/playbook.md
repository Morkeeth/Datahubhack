# Concept Forge Playbook

Score every concept against this sheet before locking a build brief.
Deadline: **Mon 10 Aug 2026, 5:00pm EDT**.

## Hard constraints

| Constraint | Rule |
| --- | --- |
| Build window | ~2 agent-led build days after concept lock |
| Stranger demo | README alone → working demo in &lt;3 minutes |
| Submission | Live URL **or** clear local setup + &lt;3-min public video + Apache-2.0 public repo |
| DataHub access | Local Docker quickstart — judges cannot reach a private instance |
| DataHub usage | Must use ≥1 of: MCP Server, Agent Context Kit, DataHub Skills, Analytics Agent, OSS platform |

## Challenge tracks (pick one or combine)

1. **Agents That Do Real Work** — read context, act, write results back to the graph
2. **Metadata-Aware Code Generation** — generate merge-ready pipelines/models/scripts from real schemas + lineage
3. **Production ML Agents** — protect models via end-to-end ML lineage
4. **Open / Wildcard** — creative uses of DataHub as the foundation

## Judging lenses (weight mentally, then rank)

1. **Use of DataHub** — depth beyond read-only metadata; write-back when it helps
2. **Technical execution** — end-to-end works; claims match the demo
3. **Originality** — compose / extend shipped features; do not reimplement core DataHub
4. **Real-world usefulness** — a data/ML/platform team would care
5. **Submission quality** — README, video, setup path for strangers
6. **Bonus** — meaningful OSS contribution to DataHub (connector, skill, fix, RFC, docs)

## Concept template (required fields)

Each concept file must answer:

- **One-liner** — what it is in one sentence
- **Track** — which challenge(s)
- **User** — who runs it and why today
- **DataHub surface** — MCP / ACK / Skills / lineage / mutations used
- **Demo story (&lt;3 min)** — beat sheet a stranger can follow
- **Local path** — how Docker quickstart + sample data powers the demo
- **Artifact** — what judges can open without running code (examples/)
- **Risks** — what can fail in 48h and how we cut scope
- **Why we win** — one sharp differentiator vs. generic chatbot-on-catalog

## Ruling process

1. Collect independent sets under `concepts/grok/`, `concepts/gpt/`, `concepts/third/`
2. Cross-cut against this playbook (no vibe picks)
3. Lock **one** winning concept into `docs/build-brief.md`
4. Only then start implementation under `app/` (or agreed layout)

## Anti-patterns

- Private-only DataHub Cloud demos with no local fallback
- Thin wrappers that only call `search` and print chat
- Hero UIs with no durable artifact or write-back
- Ideas that need credentials judges cannot obtain
