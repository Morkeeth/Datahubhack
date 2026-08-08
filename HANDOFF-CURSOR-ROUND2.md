# HANDOFF → Cursor, round 2 (written 2026-08-07, Claude Code)

`RULING.md` picked **Nullspace**. That ruling was made **without** the evidence below.
Round 2 exists to re-decide with it. Treat `RULING.md` as prior signal, not gospel.

---

## New evidence the round-1 panel did not have

### 1. The "eight laws" in RULING.md were improvised from memory
The real playbook lives in the vault (`01 Projects/Hackathons/`): `winner-patterns.md`,
`three-layer-winning-formula.md`, `submission-gate.md`, `hackathon-playbook.md`,
`agentic-design-handbook.md`. The improvised laws overlap with it but **missed four things**:

- **Yieldbound post-mortem:** *"more category thesis than sponsor-native wedge — conceptually
  stronger than operationally undeniable."* Nullspace is a category thesis. This is the documented
  way Oscar lost MetaMask, Lido and Synthesis.
- **Lido lesson #3:** agent-infra judges reward a **broad deliberate tool surface** (winners cited
  "67+ tools, skill files"). DataHub's own judging weights the **MCP server, Agent Context Kit and
  DataHub Skills**. Nullspace is one thin loop that touches the graph and little else.
- **DataHub rules:** bonus points for an **open-source contribution back to DataHub** (connector,
  skill, RFC, docs). Absent from RULING.md entirely.
- **No track named.** Four tracks, one $3k prize each, plus $6k grand. RULING.md never picks one.

### 2. Oscar's own scoreboard says category theses place, builds win

| Project | Judge signal | Result |
|---|---|---|
| Yieldbound | "most conceptually compelling in the cohort" | 2nd, $1,000, −11 pts (`dryRun=true` deductions) |
| RECEIPT | category invention, taste, zero-fake-data | top 20% of 468, **zero prizes** |
| Agent Verify | "non-obvious wedge" | did not win |
| **Litmus** (Anthropic × FullEnrich × Sillage, Station F, Jul 9 2026) | real end-to-end, both sponsors load-bearing | **did NOT top-10 of 58** |
| AAtomato | smart accounts that actually did the thing | **3 prizes** |
| RELAY | "real money on mainnet" | Silver |
| BRIEF MCP | "sharp category, clear demo" | Finalist |

**Durable pattern (vault `retro-litmus-2026-07-09.md`):** Oscar gravitates to
correctness / precision / verification builds that are intellectually elite and **emotionally flat
in a 90-second room**. Litmus's pre-mortem named "felt/wow is the weak axis" — and that is exactly
the axis that lost. Name Nullspace's weak axis before building, or it will be the one that loses.

### 3. The staging contradiction — MUST be ruled in round 2
- `RULING.md` Law 6 says: nothing staged, no seeded ghost, no pre-baked JSON, the PR must be real.
- Litmus retro, Pierre's point #2 (rated **9/10**, the sharpest in the file): *finalists demoed on
  staged data while we spent our hours on a real engine nobody could perceive.* Resolution recorded
  in the vault: **mock the presentation, never the proof** — staged/labelled demo data that sharpens
  the aha is not a dishonest claim; `dryRun=true` in the codebase is.
- Also from Litmus: **clean/small read as "did less."** Judges scanning 58 teams equate visible
  surface with effort. Nullspace is one thin loop.
- And: **build the demo backward from the aha; spend the final hours on the reveal, not the engine.**
  RULING.md spends both build days on the engine.

### 4. Competitive check — nobody ran one in round 1 (verified 2026-08-07, web)
- **Nullspace / demand-side:** **Secoda already ships "data request management"** (replacing requests
  scattered across Jira / Slack / Docs). DataHub itself has **Data Products** as a first-class entity
  with a YAML spec. The human ancestor exists. No evidence found either way for the specific mechanic
  — *agents vote by failing to find it, and the want becomes an addressable URN*. Record that as
  **unverified-absent, not proven-novel.**
- **Scar Tissue / agent failure memory — the panel's unanimous #2:** walks straight into
  **Mem0, Zep, Letta, Cognee, MemPalace** — funded, open-source, head-to-head benchmarked all
  through 2026. This is the most contested category in AI infra. Nobody checked; three models
  ranked it #2 on aesthetics.
- **Coordination (Baton/Leasehold):** Redis / Temporal. Correctly dead already.
- **Gates (Verdict/Twinwire):** Collibra's workflow engine already routes access requests into
  automatic compliance review. Shipped category.

### 5. Corrected honest claim for Nullspace
Not "nobody has done this." Secoda has, for humans. The defensible claim is narrower:
**"the request queue becomes a catalog entity, and the requesters are agents."**

---

## What round 2 must output

1. **One winner**, re-decided against the evidence above — Nullspace confirmed or replaced.
2. **The named weak axis** of the winner (the Litmus discipline: name the axis most likely to lose,
   before building) and the specific engineered fix for it.
3. **The staging ruling** — one line: what may be staged, what may never be.
4. **Which of the four tracks** the submission targets, and why that one.
5. **Tool surface** — how the build meaningfully uses the MCP server / Agent Context Kit /
   DataHub Skills, not just the graph.
6. **The OSS contribution back to DataHub** — what it is, concretely.
7. **The single frame** a judge remembers, and the 3-minute beat built backward from it.

## Still dead — do not revive
Catalog Lie Detector · blast-radius bot · Cerberus · two agents negotiating a contract with DataHub
as referee · ML target-leakage sentinel · Callus · Baton · Leasehold · Requisition · Context Diet ·
Scribe · Verdict · Flight Recorder · Branchline · Actuary · Airgap Relay · Pouch · Twinwire.
Scar Tissue survives as fallback **only** with an answer to the Mem0/Zep/Letta problem above.
