# Grok (`cursor-grok-4.5-high-fast`)

**1. Baton**
CATEGORY IT CREATES — Agent handoff protocol
THE 3-MINUTE AHA — Agent A stamps a passport on a table; Agent B freezes until it appears, then writes a receipt—both stamps animate on-screen.
WHAT IT WRITES BACK — Passport aspects (schema hash, grain, stats, TTL) + consume receipts on the asset URN.
SPONSOR-NATIVE PROOF — Delete DataHub → B never sees a passport; the chain cannot proceed.
WHY IT'S 2 DAYS — Two agents + MCP aspect writes + docker-compose with seeded tables; UI only renders stamps.

**2. Leasehold**
CATEGORY IT CREATES — Catalog mutex for agents
THE 3-MINUTE AHA — Two agents race one model; a red lease badge locks the asset; the loser aborts with “held by Agent-2 until 14:02.”
WHAT IT WRITES BACK — Exclusive lease aspects (owner agent ID, TTL) + release events.
SPONSOR-NATIVE PROOF — No graph → no lock board; both agents corrupt the same asset.
WHY IT'S 2 DAYS — Race script + one custom aspect via MCP; no real distributed lock infra.

**3. Twinwire**
CATEGORY IT CREATES — Privacy shadow graph
THE 3-MINUTE AHA — Agent reaches for `email`; auto-reroutes to `shadow_email`; dashed lineage edge Agent→shadow draws live.
WHAT IT WRITES BACK — Shadow dataset entities, clone lineage, `routes-to-shadow` relationships.
SPONSOR-NATIVE PROOF — Shadow map lives only in DataHub; remove it and agents hit real PII.
WHY IT'S 2 DAYS — Tag PII in seed catalog, mint shadows once, thin MCP rewrite layer.

**4. Scribe**
CATEGORY IT CREATES — Agent-emitted lineage
THE 3-MINUTE AHA — No chat theater—after each agent query a lineage edge grows Agent→column; a second agent reads it and skips a bad join.
WHAT IT WRITES BACK — Query-level lineage edges + `agent-touched` tags with run URNs.
SPONSOR-NATIVE PROOF — Footprints have nowhere to land; the next agent starts blind.
WHY IT'S 2 DAYS — SQL/MCP wrapper emits edges; sample datapack is enough.

**5. Verdict**
CATEGORY IT CREATES — Lineage-gated model promotion
THE 3-MINUTE AHA — Promote stays dead until training-set URN, metrics aspect, and upstream freshness are green on the model—then the agent flips status.
WHAT IT WRITES BACK — Training lineage, metrics aspects, promotion decision + veto reasons on the model URN.
SPONSOR-NATIVE PROOF — Gates read only DataHub aspects; no graph = blind promote or permanent stuck.
WHY IT'S 2 DAYS — One sklearn train on sample features + custom aspects + thin promoter agent.

---

**RANK (Monday-morning recall)**
1. Baton → 2. Leasehold → 3. Twinwire → 4. Scribe → 5. Verdict

**Why #1:** Judges remember the freeze—Agent B visibly blocked until a passport materializes on the catalog asset, then the receipt stamp. That single subtraction (no passport → no progress) makes DataHub the runtime, not a sidebar. It names a category other teams won’t accidentally rebuild as “chat over lineage.”

**Crowded play:** Verdict — twenty other teams will ship some lineage-gated ML promote/monitor bot for Track 3.
