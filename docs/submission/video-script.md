# Demo video — 3:00 hard cap

Built backward from the aha (playbook #43). The reveal gets the time; the engine gets
mentioned. Record at 70% (playbook #18) — the moment the happy path runs, capture it and
keep building; re-record only if it improves.

**Rule for this shoot (playbook #46):** drive the entire path yourself, cold, before the
camera rolls — fresh clone, empty ghost store, stack from `docker compose up`. Every
previous failure came from filming a path nobody had walked in its degraded state.

---

## 0:00 — 0:12 · The silence

Terminal. An agent asks for a table.

> `find_dataset("monthly recurring revenue by segment")`
> → **no results**

**VO:** "An agent asked your catalog for something. It wasn't there. So the agent gave up,
and nobody found out."

*Hold the empty result for two full seconds. The silence is the product's enemy — show it.*

## 0:12 — 0:40 · Three rooms, one miss

Split screen, three terminals, three different client names.

**VO:** "This happens three times today, in three different contexts. Three agents want the
same table that doesn't exist. None of them will ever know about the others."

## 0:40 — 1:20 · The miss becomes demand

Run the real thing. Show `demand` climbing **1 → 2 → 3**, with the actual client
identities on screen.

**VO:** "Nullspace catches the miss. Every failed search materialises a ghost — a real
DataHub entity for an asset that doesn't exist — and each agent that asks is recorded on it."

**Cut to DataHub at `localhost:9002`.** Show the ghost entity in the real catalog.
**This is the sponsor-native beat: it is a real DataHub dataset, not our own database.**

## 1:20 — 1:55 · The thing nobody does

Each agent registers the query it *meant* to run.

```
revenue-copilot    SELECT segment, mrr FROM <does not exist>
finance-agent      SELECT month, SUM(mrr) ...
board-deck-writer  SELECT segment, mrr, churned_mrr ...

demanded schema : segment · mrr · month · churned_mrr
```

**VO:** "They write SQL against a table that doesn't exist. And the columns they ask for
become the schema the builder has to deliver. The spec isn't guessed — it's derived from
demand."

## 1:55 — 2:35 · Ghost goes solid

Builder agent claims it. Real dbt model. Ghost → **solid**.

**Cut to DataHub. Open the dataset. Show the Owners panel:**

> Owners: `revenue-copilot` · `finance-agent` · `board-deck-writer`

**VO:** "Three AI agents own this table, because they're the ones who asked for it."

*This is the goosebump shot. Hold it. It renders natively in DataHub — nothing custom.*

## 2:35 — 2:55 · Does my query run now?

```
contract_status("monthly recurring revenue by segment")
→ RUNS  revenue-copilot
  RUNS  finance-agent
  RUNS  board-deck-writer
  3 running, 0 blocked
```

**VO:** "And the agents that asked get told their query works now."

## 2:55 — 3:00 · Card

> **NULLSPACE**
> A catalog entry for data that doesn't exist yet.
> `github.com/Morkeeth/nullspace`

---

## Shot checklist before recording

- [ ] cold clone, `docker compose up` from scratch, ingestion reports *Pipeline finished successfully*
- [ ] ghost store and contract store deleted — demand must start at zero on camera
- [ ] `nullspace reset` (or fresh volumes) so demand climbs from zero on camera — no throughput noise
- [ ] `contract_status` returns **3 running / 0 blocked**
- [ ] Owners panel populated in DataHub (native Owners, not a custom UI)
- [ ] no terminal shows a `WARN: DataHub GMS not reachable` line
- [ ] any seeded/demo data named as such on screen (playbook #43 — mock the presentation, never the proof)
- [ ] this recording’s `pr_url` is `https://github.com/...` before VO says “pull request”
- [ ] solid materialisation method known (`dbt_run` vs `warehouse_ctas`) before VO says “dbt”

## Two claims that must NOT be in the video until they are true *on this recording*

1. **"opens a real pull request"** — only if this shoot shows an `https://github.com/` URL.
   `nullspace-dbt` #1 and #2 are already merged; a `file://` path on the demo host is still
   not a PR. See `docs/submission/REVIEW-NOTES.md`.
2. **"works with any agent"** — say *"any MCP client"* and show two real ones, or say
   nothing. Playbook #45: designed-to, never does.
