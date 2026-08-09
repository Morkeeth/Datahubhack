-- Nullspace builder-agent output for demand: timing probe 1786311050
-- Requesters: revenue-copilot-1.0.0, finance-agent-2.3.1, board-deck-writer-0.9.0
-- Ghost URN: urn:li:dataset:(urn:li:dataPlatform:nullspace,ghost_timing_probe_1786311050_40cf3939,PROD)
-- Generation tier: claude-cli
-- deterministic grain over revenue_events

select
    "segment",
    "month",
    sum("mrr") as mrr,
    sum("churned_mrr") as churned_mrr
from {{ source('warehouse_source', 'revenue_events') }}
group by segment, month
