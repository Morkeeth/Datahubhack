-- Nullspace builder-agent output for demand: monthly recurring revenue by segment 232121
-- Requesters: revenue-copilot-1.0.0, finance-agent-2.3.1, board-deck-writer-0.9.0
-- Ghost URN: urn:li:dataset:(urn:li:dataPlatform:nullspace,ghost_monthly_recurring_revenue_by_segment_232121_807b9616,PROD)
-- Generation tier: claude-cli
-- deterministic grain over revenue_events

select
    "segment",
    "month",
    sum("mrr") as mrr,
    sum("churned_mrr") as churned_mrr
from {{ source('warehouse_source', 'revenue_events') }}
group by segment, month
