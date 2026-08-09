-- Nullspace builder-agent output for demand: warmup 1786309545
-- Requesters: revenue-copilot-1.0.0, finance-agent-2.3.1, board-deck-writer-0.9.0
-- Ghost URN: urn:li:dataset:(urn:li:dataPlatform:nullspace,ghost_warmup_1786309545_fa9982cc,PROD)
-- Generation tier: claude-cli
-- deterministic grain over revenue_events

select
    "segment",
    "month",
    sum("mrr") as mrr,
    sum("churned_mrr") as churned_mrr
from {{ source('warehouse_source', 'revenue_events') }}
group by segment, month
