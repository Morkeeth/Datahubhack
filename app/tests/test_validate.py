"""Tests for the deterministic validation gates."""

from join_treaty.config import dataset_urn
from join_treaty.datahub import DatasetFacts, FieldProfile
from join_treaty.model import ColumnRef, JoinCandidate, JoinPredicate, QueryEvidence
from join_treaty.validate import validate_candidate


def _facts(table, fields, profiles):
    return DatasetFacts(
        urn=dataset_urn(table),
        fields=fields,
        row_count=3,
        profiles={
            f: FieldProfile(field=f, unique_count=None, null_count=0, unique_proportion=p)
            for f, p in profiles.items()
        },
    )


def _candidate(a_table, a_field, b_table, b_field, n):
    pred = JoinPredicate.canonical(
        ColumnRef(dataset_urn(a_table), a_field),
        ColumnRef(dataset_urn(b_table), b_field),
    )
    ev = [QueryEvidence(f"urn:li:query:q{i}", "SELECT 1") for i in range(n)]
    return JoinCandidate(predicate=pred, evidence=ev)


CUSTOMERS = _facts("customers", {"customer_id": "BIGINT", "email": "TEXT"}, {"customer_id": 1.0, "email": 1.0})
ORDERS = _facts("orders", {"customer_id": "BIGINT", "status": "TEXT"}, {"customer_id": 0.66, "status": 1.0})


def _facts_map(*facts):
    return {f.urn: f for f in facts}


def test_accepts_and_infers_n_to_one():
    cand = _candidate("orders", "customer_id", "customers", "customer_id", 3)
    v = validate_candidate(cand, _facts_map(CUSTOMERS, ORDERS))
    assert v.accepted is True
    assert v.cardinality == "N_ONE"
    # many side (source) is orders, one side (destination) is customers
    assert v.source_urn == dataset_urn("orders")
    assert v.destination_urn == dataset_urn("customers")


def test_rejects_below_threshold():
    cand = _candidate("orders", "customer_id", "customers", "customer_id", 2)
    v = validate_candidate(cand, _facts_map(CUSTOMERS, ORDERS))
    assert v.accepted is False
    assert any(g.name == "repeated_evidence" and not g.passed for g in v.gates)


def test_rejects_type_incompatible():
    cand = _candidate("orders", "status", "customers", "customer_id", 3)
    v = validate_candidate(cand, _facts_map(CUSTOMERS, ORDERS))
    assert v.accepted is False
    assert any(g.name == "type_compatible" and not g.passed for g in v.gates)


def test_abstains_without_unique_side():
    both_dup_a = _facts("orders", {"customer_id": "BIGINT"}, {"customer_id": 0.5})
    both_dup_b = _facts("order_items", {"order_id": "BIGINT"}, {"order_id": 0.5})
    pred = JoinPredicate.canonical(
        ColumnRef(dataset_urn("orders"), "customer_id"),
        ColumnRef(dataset_urn("order_items"), "order_id"),
    )
    cand = JoinCandidate(
        predicate=pred,
        evidence=[QueryEvidence(f"urn:li:query:q{i}", "x") for i in range(3)],
    )
    v = validate_candidate(cand, _facts_map(both_dup_a, both_dup_b))
    assert v.accepted is False
    assert any(g.name == "cardinality_supported" and not g.passed for g in v.gates)


def test_missing_profile_abstains():
    no_prof = _facts("customers", {"customer_id": "BIGINT"}, {})
    orders = _facts("orders", {"customer_id": "BIGINT"}, {"customer_id": 0.66})
    cand = _candidate("orders", "customer_id", "customers", "customer_id", 3)
    v = validate_candidate(cand, _facts_map(no_prof, orders))
    assert v.accepted is False
    assert any(g.name == "cardinality_supported" and not g.passed for g in v.gates)
