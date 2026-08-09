from nullspace.client import DataHubClient
from nullspace.sqlgen import build_sql_plan


def _warehouse_fixture() -> list[dict]:
    return [
        {
            "urn": "urn:li:dataset:(urn:li:dataPlatform:postgres,local-warehouse.warehouse.ecommerce.trials,DEV)",
            "fields": [
                {"name": "trial_id", "native_type": "BIGINT"},
                {"name": "cohort_id", "native_type": "TEXT"},
                {"name": "trial_started_at", "native_type": "TIMESTAMP"},
                {"name": "converted_at", "native_type": "TIMESTAMP"},
            ],
        },
        {
            "urn": "urn:li:dataset:(urn:li:dataPlatform:postgres,local-warehouse.warehouse.ecommerce.revenue_events,DEV)",
            "fields": [
                {"name": "event_id", "native_type": "BIGINT"},
                {"name": "month", "native_type": "TEXT"},
                {"name": "segment", "native_type": "TEXT"},
                {"name": "mrr", "native_type": "NUMERIC"},
                {"name": "churned_mrr", "native_type": "NUMERIC"},
            ],
        },
        {
            "urn": "urn:li:dataset:(urn:li:dataPlatform:postgres,local-warehouse.warehouse.ecommerce.customers,DEV)",
            "fields": [
                {"name": "customer_id", "native_type": "BIGINT"},
                {"name": "email", "native_type": "TEXT"},
                {"name": "country_code", "native_type": "CHAR"},
            ],
        },
        {
            "urn": "urn:li:dataset:(urn:li:dataPlatform:postgres,local-warehouse.warehouse.ecommerce.orders,DEV)",
            "fields": [
                {"name": "order_id", "native_type": "BIGINT"},
                {"name": "customer_id", "native_type": "BIGINT"},
                {"name": "status", "native_type": "TEXT"},
            ],
        },
        {
            "urn": "urn:li:dataset:(urn:li:dataPlatform:postgres,local-warehouse.warehouse.ecommerce.order_items,DEV)",
            "fields": [
                {"name": "order_id", "native_type": "BIGINT"},
                {"name": "product_id", "native_type": "BIGINT"},
                {"name": "quantity", "native_type": "INT"},
                {"name": "unit_price", "native_type": "NUMERIC"},
            ],
        },
    ]


def test_mrr_by_segment_has_group_by_and_sum():
    plan = build_sql_plan(
        want="monthly recurring revenue by segment",
        requesters=["a", "b", "c"],
        ghost_urn="urn:x",
        demanded_fields=["segment", "mrr", "month", "churned_mrr"],
        queries=[{"agent_id": "a", "sql": "select segment, sum(mrr) from t group by 1"}],
        warehouse_datasets=_warehouse_fixture(),
    )
    sql = plan.model_sql.lower()
    assert "group by" in sql
    assert "sum(" in sql
    assert "select\n    \"segment\"" in plan.model_sql or 'select\n    "segment"' in plan.model_sql
    assert len(plan.upstream_urns) == 1


def test_trial_to_paid_is_aggregated_not_passthrough():
    plan = build_sql_plan(
        want="trial-to-paid conversion by cohort",
        requesters=["a"],
        ghost_urn="urn:x",
        demanded_fields=["cohort_id", "trials", "conversions", "trial_to_paid_rate"],
        queries=[],
        warehouse_datasets=_warehouse_fixture(),
    )
    sql = plan.model_sql.lower()
    assert "group by" in sql
    assert "count(*)" in sql
    assert 'select\n    "cohort_id"' not in plan.model_sql or "count" in sql


def test_join_customer_order_has_two_upstreams():
    plan = build_sql_plan(
        want="orders and lifetime value by customer country",
        requesters=["a"],
        ghost_urn="urn:x",
        demanded_fields=["country_code", "order_count", "lifetime_value"],
        queries=[{"agent_id": "a", "sql": "select country_code, count(*) from ..."}],
        warehouse_datasets=_warehouse_fixture(),
    )
    assert len(plan.upstream_urns) >= 2
    assert "join" in plan.model_sql.lower()
    assert "group by" in plan.model_sql.lower()


def test_spanning_trials_and_revenue_without_key_declines():
    try:
        build_sql_plan(
            want="trial revenue by cohort and segment",
            requesters=["a"],
            ghost_urn="urn:x",
            demanded_fields=["cohort_id", "mrr", "segment"],
            queries=[],
            warehouse_datasets=_warehouse_fixture(),
        )
        raise AssertionError("expected decline")
    except ValueError as exc:
        assert "join key" in str(exc)


def test_hard_delete_refuses_warehouse_urn():
    dh = DataHubClient()
    try:
        dh.hard_delete_urn(
            "urn:li:dataset:(urn:li:dataPlatform:postgres,"
            "local-warehouse.warehouse.ecommerce.trials,DEV)"
        )
        raise AssertionError("expected refusal")
    except ValueError as exc:
        assert "non-nullspace" in str(exc)
