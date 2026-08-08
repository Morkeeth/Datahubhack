# Handoff → Claude

Paste into Claude Code (or run in-session). Framed for the DataHub hackathon ruling.

---

**Objective:** Deliver ONE final concept ruling for the DataHub Agent Hackathon — the single build Oscar ships this weekend.

**Context:**
- Repo: `/Users/morkeeth/Datahubhack` · https://github.com/Morkeeth/Datahubhack
- Concept sets: `concepts-grok.md`, `concepts-gpt.md`, `concepts-claude-standin-for-gemini.md`
- Multi-agent review panel: `review-panel.md` (Grok + GPT + Claude Opus already reviewed all 15)
- Event: Build with DataHub Agent Hackathon · deadline Mon 10 Aug 2026 5pm EDT · $20.5k
- Already rejected (do not revive): Catalog Lie Detector, Blast-radius bot, Cerberus, two agents negotiating a contract with DataHub as referee, ML target-leakage sentinel
- Hard constraints live in the original brief (2 build days, agents write the code, stranger README <3min, live URL, Apache-2.0, DataHub is local Docker judges cannot reach)

**Constraints:**
- Do NOT invent new concepts. Rule only from the existing 15 + the three reviews.
- Do NOT soft-pedal Law 2 (sponsor-native) or Law 6 (no mocks / stranger demo).
- Do NOT start scaffolding code in this turn — ruling only.
- Restate expensive playbook laws briefly in the ruling so they are visible without memory.

**Done when:**
- One named winner + one named fallback
- Three-sentence defense of the winner (Monday-morning memory)
- Explicit kill list of near-misses that must not be built
- One paragraph: the exact 3-minute demo beat + how the local-Docker / unreachable-instance problem is solved
- One blunt line: what 20 other teams will build instead

**Start by:** Read `review-panel.md`, then the three `concepts-*.md` files. Restate the objective and what “done” looks like in two lines, then write the ruling to `RULING.md` in the repo root.
