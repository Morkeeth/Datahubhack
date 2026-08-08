# RULING — Build with DataHub: The Agent Hackathon

**Deadline:** Mon 10 Aug 2026, 5pm EDT · 2 build days · Apache-2.0 public repo · live URL · <3-min video
**Inputs:** `concepts-grok.md`, `concepts-gpt.md`, `concepts-claude-standin-for-gemini.md`, `review-panel.md` (15 concepts, 3 independent reviews)
**Status:** FINAL. One build. No re-litigation after this file.

---

## The eight laws (restated so this file works without memory)

1. **Name a category** — the idea and its name are the same object in a judge's head.
2. **Sponsor-native** — delete DataHub and the product *breaks*, not degrades.
3. **Agents, not humans** — the user is another agent; humans watch.
4. **Pipeline, not pile** — one causal chain end-to-end beats five features.
5. **Dramatize subtraction** — the demo's best frame is what's missing, then filled.
6. **No mocks** — a stranger demos from the README in under 3 minutes; local Docker; live URL that does not require judges to reach a private instance.
7. **Execution > concept** — a shipped B beats an unshipped A.
8. **Fun and pitchable** — it survives being retold badly.

---

## WINNER — **Nullspace**

*Demand-side metadata: a catalog entry for data that does not exist yet.*

Consumer agents search DataHub for an asset that isn't there. Instead of failing silently, each failed search materializes or increments a **ghost entity** — a real DataHub dataset URN, tagged `ghost`, carrying a demand counter and edges back to every requesting agent. When demand crosses threshold, a **builder agent** claims the ghost, writes a real dbt model, opens a real PR against a real repo, and on merge the ghost **goes solid**: real schema, real lineage, and provenance edges pointing back at the three agents that asked for it.

**All three reviewers ranked it #1. It collided with nothing.** Every other finalist had a cousin in another model's list (Scar Tissue↔Callus, Airgap↔Pouch, Leasehold↔Requisition↔Baton). Nullspace was invented once, by one prior, and independently top-ranked by the other two. That is the strongest available signal in this dataset.

### Fallback — **Scar Tissue**

*Graph-bound failure memory: one agent bleeds, the next inherits immunity.*
Ranked #2 by all three reviewers. Lowest build risk, highest legibility-per-minute. **Cut to this only if, by Saturday 18:00, the ghost→solid writeback is not visibly working end-to-end.** Not a parallel track — a tripwire.

---

## Three-sentence defense (the Monday-morning memory)

Nullspace inverts the founding assumption of every catalog — that a catalog is an inventory of things that exist — and that inversion *is* the category, so the name and the idea are one object a judge can still retell on Monday. It is unambiguously agent-to-agent infrastructure: consumer agents post demand into a shared namespace, a producer agent claims and fulfils it, and DataHub is the only place on earth that handshake can occur, because deleting it means three agents fail silently in three separate contexts forever with no way to discover they wanted the same thing. It hits READ and WRITE at full strength in one causal chain, ends in a genuinely mergeable dbt PR rather than a printed intention, and the ghost-going-solid moment is a single continuous shot that needs no narration.

**Steal exactly one thing from Scar Tissue and nothing else:** bind resolution history to the URN, so the solidified asset permanently carries who asked, when, and what failed first. That is the whole cross-pollination budget.

---

## KILL LIST — near-misses that must not be built

These are not "later." They are not "if time." They are not bolt-ons to Nullspace.

| Killed | Law broken |
|---|---|
| **Callus** | Duplicate of Scar Tissue; two models produced the same wound metaphor. Same product, weaker theatre. |
| **Baton** | Law 2 — a semaphore that runs equally well on SQS, Redis, or a JSON file, wearing a catalog badge. |
| **Leasehold** | Law 2 — `SETNX` with a badge. Cousin of the already-rejected referee concept. |
| **Requisition** | Law 1 + Law 2 — mutex again, plus Nullspace's demand signal, plus a package-manager bow. Correct, useful, forgettable. |
| **Context Diet** | Law 1 — RAG-over-catalog is the default idea of the entire field. Near-zero writeback. |
| **Scribe** | Law 1 + Law 4 — ordinary lineage emission; joins a shipped category as a feature tour. |
| **Verdict** | Law 1 — lineage-gated model promotion; crowded CI-gate-on-metadata, and a remix of the already-rejected Cerberus. |
| **Flight Recorder** | Remix of the already-rejected Catalog Lie Detector, plus Law 3 (human forensics UI). |
| **Branchline** | Law 1 + Law 3 — Git metaphors for metadata; human merge theatre; HIGH two-day risk on merge semantics. |
| **Actuary** | Law 6 — invented economics cannot be executed in two days, so premiums and claims become mock-grade. Blast-radius bot in an insurance costume. |
| **Airgap Relay** | Law 6 — air-gap plus live URL forces `dryRun` replay of pre-baked JSON. That is theatre. |
| **Pouch** | Law 6 — capsule answers are read-only, unverifiable without mocks; judges remember the trick, not the product. |
| **Twinwire** | Law 3 — privacy plumbing for humans; weak agent-to-agent subtraction. |

**Also still dead, from before the forge:** Catalog Lie Detector, blast-radius bot, Cerberus, two-agents-negotiating-a-contract-with-DataHub-as-referee, ML target-leakage sentinel.

**Specific temptations to refuse mid-build:** do not add Requisition's dedupe resolver "since we already have demand counters"; do not add Pouch's export "so judges can try it offline"; do not add Context Diet's token-savings panel "because it demos well." Each one converts a category into a pile and costs the Sunday hours that make the PR real.

---

## The three-minute demo beat, and the unreachable-instance problem

**The beat (one continuous shot, no narration required).** 0:00–0:25: three independent consumer agents, in three separate contexts, each ask for *trial-to-paid conversion by cohort*. Each searches DataHub. Each finds nothing. 0:25–0:55: instead of three silent failures, the catalog visibly grows a hollow node — a real dataset URN tagged `ghost`, demand counter ticking 1 → 2 → 3 on camera, with three edges snapping back to the requesting agents. This is the subtraction frame: the catalog is showing you a thing that does not exist. 0:55–1:50: a builder agent watching for demand ≥ 3 claims the ghost, reads the three requesters' actual failed queries off the graph to infer the grain, writes a dbt model, and opens a **real pull request against a real dbt repo** — the PR URL is on screen and clickable. 1:50–2:30: the PR merges, dbt runs, ingestion fires, and the ghost **goes solid** in place: hollow outline fills, real schema appears, upstream lineage snaps in, and the three demand edges persist as provenance pointing at the agents that caused the table to exist. 2:30–3:00: the subtraction proof — stop DataHub, rerun the same three agents, and they fail in three separate silos with no way to discover they wanted the same asset and no namespace in which a non-existent thing can be addressed or claimed. **Solving the local-Docker problem:** the repo is one `docker compose up` that brings up DataHub quickstart, the seeded warehouse, both agent roles, and the Nullspace board, so a stranger reproduces the entire loop from the README in under three minutes on their own machine — that is the primary artifact and it is fully real. For the judges' live URL, deploy that *same* compose file to a public host and expose only a read-only Nullspace board that reads live from that instance's GraphQL — judges get a genuinely running DataHub, not a recording, and never need a path into any private network. **No pre-baked JSON replay, no `dryRun` flag, no seeded "example" ghost that was written by hand.** If the hosted deploy slips, the fallback is the local compose plus the continuous-shot video, never a fake endpoint — the exact mistake that killed Airgap Relay and Pouch.

---

## What twenty other teams will build instead

Twenty teams will ship "search DataHub before you write SQL, then register what you built" — RAG over the catalog with a dedupe bow on it, which is roughly the MCP server's own demo, and the judges will be numb to it by the fifth submission.
