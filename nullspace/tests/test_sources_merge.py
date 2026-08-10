"""sources.yml must union tables across claims, not overwrite."""

from pathlib import Path

from nullspace.builder import BuildPlan, _merge_source_tables, write_dbt_model
from nullspace.ghosts import Ghost


def test_merge_source_tables_unions_existing(tmp_path: Path):
    sources = tmp_path / "sources.yml"
    sources.write_text(
        "version: 2\n"
        "sources:\n"
        "  - name: warehouse_source\n"
        "    schema: ecommerce\n"
        "    tables:\n"
        "      - name: trials\n",
        encoding="utf-8",
    )
    _merge_source_tables(sources, "ecommerce", ["revenue_events"])
    text = sources.read_text(encoding="utf-8")
    assert "trials" in text
    assert "revenue_events" in text


def _plan(table: str, sql: str) -> BuildPlan:
    return BuildPlan(
        fields=[{"name": "x", "native_type": "VARCHAR", "nullable": False}],
        model_sql=sql,
        upstream_urn=f"urn:li:dataset:(urn:li:dataPlatform:postgres,{table},DEV)",
        schema_source="test",
        source_schema="ecommerce",
        source_table=table,
        decision_reason="test",
    )


def test_write_dbt_model_keeps_prior_sources(tmp_path: Path):
    ghost_a = Ghost(
        want="a",
        urn="urn:li:dataset:(urn:li:dataPlatform:nullspace,ghost_a,PROD)",
        dataset_name="ghost_a",
        demand=3,
        state="claimed",
        requesters=["x"],
    )
    ghost_b = Ghost(
        want="b",
        urn="urn:li:dataset:(urn:li:dataPlatform:nullspace,ghost_b,PROD)",
        dataset_name="ghost_b",
        demand=3,
        state="claimed",
        requesters=["y"],
    )
    write_dbt_model(
        ghost_a,
        tmp_path,
        _plan("trials", "select 1 as x from {{ source('warehouse_source', 'trials') }}"),
    )
    write_dbt_model(
        ghost_b,
        tmp_path,
        _plan(
            "revenue_events",
            "select 1 as x from {{ source('warehouse_source', 'revenue_events') }}",
        ),
    )
    text = (tmp_path / "models" / "sources.yml").read_text(encoding="utf-8")
    assert "trials" in text
    assert "revenue_events" in text
    assert (tmp_path / "models" / "ghost_a.sql").exists()
    assert (tmp_path / "models" / "ghost_b.sql").exists()
