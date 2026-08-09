-- Seed staging model so the generated model can ref something real in CI/demo.
select
    '2026-q1'::varchar as cohort_id,
    '2026-01-01'::timestamp as trial_started_at,
    '2026-01-20'::timestamp as converted_at
union all
select
    '2026-q1',
    '2026-01-03'::timestamp,
    null::timestamp
