"""Unit tests for the Nullspace demand ingestion source (no GMS required)."""

from datahub.ingestion.api.common import PipelineContext

from nullspace.ingestion.demand import NullspaceDemandSource, NullspaceDemandSourceConfig


def test_demand_source_emits_ghost_mcps_from_events():
    cfg = NullspaceDemandSourceConfig.parse_obj(
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
    assert any("props" in i for i in ids)
    props_wu = next(wu for wu in wus if wu.id.endswith("-props"))
    aspect = props_wu.metadata.aspect
    assert aspect.customProperties["nullspace.demand"] == "2"
    assert aspect.customProperties["nullspace.state"] == "ghost"
    assert "nullspace.contracts" in aspect.customProperties
