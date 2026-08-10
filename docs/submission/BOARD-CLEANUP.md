# What was removed from the demand board, and why

**Ruled and executed 2026-08-10 ~22:20, delegated by Oscar ("evaluate this yourself").**

Six entries were hard-deleted from the live catalog. This file exists so the deletion is
auditable, because a board that quietly gets tidier is the same failure this project is
about.

## What went

| State | Demand | Want | Why it was not real demand |
| --- | --- | --- | --- |
| claimed | 4 | weekly active accounts by plan tier | created by `verify_agent_a/b/c` while I was testing the builder's fallback path on 10 Aug |
| ghost | 3 | average order value by product category | created by `stranger_analytics_bot`, `stranger_pricing_bot`, `stranger_merch_bot` while testing the documented remote-agent path |
| claimed | 3 | timing probe 1786311050 | build-time instrumentation |
| claimed | 3 | warmup 1786309545 | build-time instrumentation |
| ghost | 1 | no such table probe | build-time instrumentation |
| ghost | 1 | support ticket volume by plan tier | created by `permanent_url_check` while proving the permanent public URL served a working MCP endpoint |

## The reasoning

The constraint was: **do not make the board look better than it is.**

Deleting these makes it look **worse**, and that is why it is the right call. Every one of
them was an agent I ran to test the machinery, not a consumer that wanted a table. Leaving
them in inflates the single number the whole product rests on — how many independent agents
asked for something that does not exist.

The counts moved in the honest direction:

|  | before | after |
| --- | --- | --- |
| entries | 54 | 48 |
| total asks | 1251 | 1236 |
| solid | 1 | 1 |

Nothing that a real requester created was touched. The one solid asset, its four typed
fields, and its physical table in the warehouse are unchanged.

## What was deliberately not done

The board was **not reset**. A reset would have wiped the 48 genuine entries as well, and
the accumulated demand behind them is the only thing on the board that took time to
produce. Six targeted hard-deletes by URN, listed above, is the whole change.
