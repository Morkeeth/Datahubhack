"""Builder plan is bound to the ghost URN — /tmp is only a cache."""

from nullspace.builder import BuildPlan, _load_agent_plan, save_agent_plan


def test_save_and_load_plan_roundtrip_via_file_cache(tmp_path, monkeypatch):
    plan_path = tmp_path / "plans.json"
    monkeypatch.setenv("NULLSPACE_BUILDER_PLANS", str(plan_path))
    # Re-import path constants would need module reload; exercise JSON shape via
    # save with dh=None (file cache only).
    import nullspace.builder as builder

    monkeypatch.setattr(builder, "_PLAN_STORE", plan_path)
    plan = BuildPlan(
        fields=[{"name": "segment", "native_type": "VARCHAR"}],
        model_sql="select 1",
        upstream_urn="urn:li:dataset:(urn:li:dataPlatform:postgres,t,DEV)",
        schema_source="test",
        source_schema="ecommerce",
        source_table="revenue_events",
        decision_reason="unit",
        generation_tier="deterministic",
        grain_reason="test grain",
    )
    save_agent_plan("monthly recurring revenue by segment", plan, dh=None)
    loaded = _load_agent_plan("monthly recurring revenue by segment", dh=None)
    assert loaded is not None
    assert loaded.model_sql == "select 1"
    assert loaded.grain_reason == "test grain"
