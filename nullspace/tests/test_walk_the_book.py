"""Builder walks the book — skip unsatisfiable wants in demand order."""

from nullspace.builder import (
    _format_claim,
    _format_skip,
    _rank_open_ghosts,
    _warehouse_column_shortfall,
)


def test_rank_open_ghosts_by_demand_then_age():
    board = {
        "threshold": 3,
        "ghosts": [
            {
                "want": "low",
                "state": "ghost",
                "demand": 5,
                "resolution": [{"event": "miss", "at_ms": 1}],
            },
            {
                "want": "high",
                "state": "ghost",
                "demand": 19,
                "resolution": [{"event": "miss", "at_ms": 9}],
            },
            {
                "want": "solid-already",
                "state": "solid",
                "demand": 99,
                "resolution": [],
            },
        ],
    }
    ranked = _rank_open_ghosts(board)
    assert [g["want"] for g in ranked] == ["high", "low"]


def test_skip_and_claim_lines():
    skip = _format_skip("churn by cohort", 19, "no warehouse column for cohort")
    assert skip.startswith("skipped")
    assert "churn by cohort" in skip
    assert "demand 19" in skip
    claim = _format_claim(
        "pipeline coverage by rep", 13, "all 4 fields resolve to pipeline_performance"
    )
    assert claim.startswith("claiming")
    assert "pipeline coverage by rep" in claim


def test_warehouse_shortfall_when_no_source(monkeypatch):
    class Fake:
        def find_source_covering_fields(self, fields):
            return None

        def healthy(self):
            return True

        def list_warehouse_datasets(self):
            return [
                {"fields": [{"name": "rep_id"}, {"name": "pipeline_value"}]},
            ]

    missing = _warehouse_column_shortfall(
        ["rep_id", "cohort", "churn_rate"], Fake()  # type: ignore[arg-type]
    )
    assert missing == ["cohort", "churn_rate"]
