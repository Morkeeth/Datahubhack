# Claude Opus (`claude-opus-5-thinking-high`) — stand-in for Gemini

> Gemini is not available as a Cursor subagent model in this runtime. This is the third independent prior.

NAME — Nullspace
CATEGORY IT CREATES — Demand-side metadata: want-ads for data that doesn't exist yet.
THE 3-MINUTE AHA — Three consumer agents search for "trial-to-paid conversion," all fail. A ghost node materializes in DataHub with demand=3 and the three requesters attached. A builder agent claims the ghost, emits a dbt model as a real PR, and on merge the ghost turns solid — lineage snaps into place on camera.
WHAT IT WRITES BACK — Ghost dataset entities, demand counters, requester links, fulfillment claims, then real schema + lineage + dbt provenance.
SPONSOR-NATIVE PROOF — DataHub is the only shared namespace where a non-existent asset can be addressed, counted, and claimed by another agent. Delete it and three agents fail silently in three separate contexts, forever.
WHY IT'S 2 DAYS — A ghost is just a dataset entity with a tag and an aspect. Fulfillment reuses stock dbt codegen. No new infra.

NAME — Callus
CATEGORY IT CREATES — Agent scar tissue: a write-back learning layer where failures become catalog metadata.
THE 3-MINUTE AHA — Two identical fresh agents, same question, split screen. Left: 14 tool calls, answers in cents, wrong. Callus writes the lesson to the column. Right: 2 calls, correct. Token counter collapses live.
WHAT IT WRITES BACK — Column-level lesson aspects, corrected semantics, failed-assumption tags, glossary terms, each linked to the agent and prompt that got burned.
SPONSOR-NATIVE PROOF — Without DataHub the lesson has no durable, addressable home keyed to the exact column, so it degrades into per-agent vector sludge no other agent can find.
WHY IT'S 2 DAYS — Thin MCP proxy: intercept tool calls, diff outcome against assumption, emit aspect.

NAME — Pouch
CATEGORY IT CREATES — Cross-org agent context exchange: signed, redacted subgraph passports.
THE 3-MINUTE AHA — A stranger's agent, with zero network path to your DataHub, correctly answers "what breaks if we drop this column?" from a 40KB pouch you emailed it. Same trick makes the judges' inaccessible-instance problem disappear on stage.
WHAT IT WRITES BACK — Export manifests, per-entity redaction and consent annotations, and inbound pouches ingested as external-domain nodes carrying trust levels.
SPONSOR-NATIVE PROOF — It is a serializer and deserializer for DataHub's graph model. Remove DataHub and there is literally nothing to pack.
WHY IT'S 2 DAYS — Export and import ride existing GraphQL reads plus the emitter API.

NAME — Actuary
CATEGORY IT CREATES — Underwriting for data pipelines: machine-readable risk premiums agents can shop on.
THE 3-MINUTE AHA — An agent about to launch an expensive backfill requests a quote and gets a high premium. It reroutes to a lower-risk upstream, requotes, and the premium visibly collapses — then the risky path breaks and a claim gets filed.
WHAT IT WRITES BACK — Per-asset risk scores as assertions, quote timestamps, and claim records when assets actually fail, which retrain the model.
SPONSOR-NATIVE PROOF — The actuarial features are lineage depth, freshness history, owner responsiveness, incident record. No graph, no rating table.
WHY IT'S 2 DAYS — Scoring function over graph queries plus one quote endpoint.

NAME — Requisition
CATEGORY IT CREATES — Package manager for data assets: dependency resolution for agent-built tables.
THE 3-MINUTE AHA — Five agents independently request "monthly active users." One wins a build lock and ships it; four receive a handle to the same canonical asset. The graph ends with one table instead of five near-duplicates.
WHAT IT WRITES BACK — Canonical claims, build locks, resolved-by provenance edges, duplicate deprecations, version tags.
SPONSOR-NATIVE PROOF — Without a global catalog there is no namespace to claim, no registry to resolve against, and every agent rebuilds from scratch.
WHY IT'S 2 DAYS — Resolver is catalog search plus semantic match plus a lock aspect.

RANKING — who's still remembered Monday morning
1. Nullspace — a node that exists before the data does. Nobody has seen that.
2. Callus — the token counter collapsing is the most visceral single frame in the set.
3. Pouch — smart, infrastructural, but judges remember the trick more than the product.
4. Actuary — great line, softer payoff; "premium" may read as gimmick under scrutiny.
5. Requisition — correct, useful, forgettable.

DEFENDING RANK 1 — Nullspace inverts the catalog's founding assumption, that a catalog describes assets that exist, and that inversion is the whole category, so the name and the idea are the same object in a judge's memory. It is unambiguously agent-to-agent infrastructure: consumer agents post demand, a producer agent fulfills it, and DataHub is the only place that handshake can happen. It hits READ and WRITE hard, hits tracks 1 and 2 simultaneously, produces a genuinely mergeable dbt PR, and the ghost-turns-solid moment is one continuous shot with no narration required.

MOST LIKELY DUPLICATED — Requisition, bluntly. "Search DataHub before you write SQL, then register what you built" is roughly the MCP server's own demo with a dedupe bow on it. Expect it from a dozen teams under a dozen names, and expect judges to be numb to it by the fifth submission.
