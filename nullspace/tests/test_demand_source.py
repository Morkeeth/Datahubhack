"""Unit tests for the Nullspace demand ingestion source (no GMS required)."""

from datahub.ingestion.api.common import PipelineContext

from nullspace.ingestion.demand import (
    NullspaceDemandSource,
    NullspaceDemandSourceConfig,
    merge_demand_custom,
)


def test_demand_source_emits_ghost_mcps_from_events():
    cfg = NullspaceDemandSourceConfig.model_validate(
        {
            "events": [
                {
                    "want": "churn by cohort",
                    "agent_id": "a",
                    "sql": "SELECT cohort FROM ecommerce.churn_by_cohort",
                    "needs_fields": ["cohort"],
                },
                {
                    "want": "churn by cohort",
                    "agent_id": "b",
                    "needs_fields": ["cohort", "churn_rate"],
                },
            ]
        }
    )
    source = NullspaceDemandSource(cfg, PipelineContext(run_id="test"))
    wus = list(source.get_workunits_internal())
    ids = [wu.id for wu in wus]
    assert any(i.startswith("tag-") for i in ids)
    assert any(i.endswith("-props") for i in ids)
    assert any(i.endswith("-sp") for i in ids)
    assert any(i.endswith("-ownership") for i in ids)
    assert any(i.startswith("query-props-") for i in ids)
    props_wu = next(wu for wu in wus if wu.id.endswith("-props"))
    aspect = props_wu.metadata.aspect
    assert aspect.customProperties["nullspace.demand"] == "2"
    assert aspect.customProperties["nullspace.state"] == "ghost"
    assert "nullspace.contracts" in aspect.customProperties
    assert "nullspace.query_urns" in aspect.customProperties


def test_merge_demand_custom_preserves_solid_lifecycle():
    incoming = {
        "nullspace.demand": "2",
        "nullspace.want": "mrr",
        "nullspace.state": "ghost",
        "nullspace.requesters": "a,b",
        "nullspace.claimed_by": "",
        "nullspace.pr_url": "",
        "nullspace.schema_source": "nullspace.ingestion.demand",
        "nullspace.resolution": "[]",
        "nullspace.contracts": "[]",
        "nullspace.query_urns": "",
    }
    prior = {
        "nullspace.state": "solid",
        "nullspace.claimed_by": "builder-1",
        "nullspace.pr_url": "https://github.com/Morkeeth/nullspace-dbt/pull/1",
        "nullspace.builder_plan": '{"model_sql":"select 1"}',
        "nullspace.builder_receipt": '{"outcome":"solidified"}',
        "nullspace.assertion_urn": "urn:li:assertion:x",
        "nullspace.schema_source": "builder",
        "nullspace.resolution": '[{"event":"solidify"}]',
        "nullspace.requesters": "a",
    }
    merged = merge_demand_custom(incoming, prior)
    assert merged["nullspace.state"] == "solid"
    assert merged["nullspace.pr_url"].startswith("https://github.com/")
    assert merged["nullspace.assertion_urn"] == "urn:li:assertion:x"
    assert merged["nullspace.builder_plan"]
    assert merged["nullspace.requesters"] == "a,b"
    assert merged["nullspace.demand"] == "2"
