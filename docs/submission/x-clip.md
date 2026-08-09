# X.com micro-demo — 45–90s

Built for a phone/timeline watch. Not the full Devpost video.  
**Rule:** never say “pull request” over `file://`. Prefer the already-merged PR.

**Best citation:** https://github.com/Morkeeth/nullspace-dbt/pull/5 (MERGED)

---

## Before record (2 min)

```bash
python3 -m nullspace.cli reset
# board empty / waiting
# Confirm you can open PR #5 in a browser tab (pre-loaded)
```

Optional off-camera (only if you want a fresh ghost in frame):

```bash
WANT="monthly recurring revenue by segment"
NULLSPACE_DEMO_WANT="$WANT" python3 scripts/moonshot_demo.py
# If pr_url is https:// → good. If file:// → abandon live path; use PR #5 only.
```

---

## Shot list (~88s)

| t | Screen | Say (≤2 sentences) |
|---|---|---|
| 0–8s | DataHub UI → search the want → **no results** | “An agent asked the catalog for a table. It wasn’t there. Normally that’s the end.” |
| 8–22s | `moonshot_demo` or three MCP misses → demand **1→2→3** | “Three agents want the same missing table. Nullspace keeps the miss as a ghost — a real DataHub entity.” |
| 22–32s | Order book / board — demand, requesters | “The catalog now maps what’s missing.” |
| 32–50s | `python3 -m nullspace.builder` — **skip** lines + **claim** | “A builder walks the backlog, refuses what it can’t build, claims what it can.” |
| 50–65s | Browser: **PR #5** → scroll `GROUP BY` diff → green **Merged** | “It opened a real dbt pull request. Here’s the merge.” |
| 65–78s | Board solid / DataHub Owners | “The ghost goes solid. The agents that asked are Owners.” |
| 78–88s | `python3 -m nullspace.console unblocked "…"` → rows | “The queries that couldn’t run, now run.” |

End card (2s): `github.com/Morkeeth/nullspace` · RFC `datahub#19022`

**Do not film** `scripts/demo.sh` (skips walk-the-book).

---

## Tweet (paste)

Use the long version in `SUBMISSION.md` §5, then add:

> Upstream: we proposed demand-side metadata to DataHub —  
> https://github.com/datahub-project/datahub/pull/19022  
>  
> Real PR the agent opened:  
> https://github.com/Morkeeth/nullspace-dbt/pull/5

### Alt hooks (pick one as first line)

1. Your agents already told you what to build next. Nobody was listening.  
2. Metadata should capture demand, not just inventory.  
3. The best demo isn’t a chatbot. It’s a merged PR.

---

## Zero-risk variant (if live build flakes)

Skip builder live. Show:
1. Board with solid MRR (or order-book built row)  
2. Click **the pull request** → #5 Merged  
3. `console unblocked` → rows  
4. One line: “Demand became a PR; the blocked agents aren’t blocked.”

Still attach RFC + repo in the tweet.
