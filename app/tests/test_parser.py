"""Deterministic tests for the SQLGlot join-predicate parser."""

from join_treaty.config import dataset_urn
from join_treaty.parser import extract_join_predicates


def _keys(sql):
    return sorted(p.key() for p in extract_join_predicates(sql))


def test_simple_alias_join():
    sql = (
        "SELECT * FROM ecommerce.orders o "
        "JOIN ecommerce.customers c ON o.customer_id = c.customer_id"
    )
    preds = extract_join_predicates(sql)
    assert len(preds) == 1
    p = preds[0]
    assert {p.left.dataset_urn, p.right.dataset_urn} == {
        dataset_urn("orders"),
        dataset_urn("customers"),
    }
    assert {p.left.field, p.right.field} == {"customer_id"}


def test_canonical_order_is_direction_independent():
    a = "SELECT * FROM ecommerce.orders o JOIN ecommerce.customers c ON o.customer_id = c.customer_id"
    b = "SELECT * FROM ecommerce.customers c JOIN ecommerce.orders o ON c.customer_id = o.customer_id"
    assert _keys(a) == _keys(b)


def test_composite_join_is_ignored():
    sql = (
        "SELECT * FROM ecommerce.order_items oi JOIN ecommerce.orders o "
        "ON oi.order_id = o.order_id AND oi.product_id = o.customer_id"
    )
    # Composite ON clause -> no single-column predicate accepted.
    assert extract_join_predicates(sql) == []


def test_non_equality_join_is_ignored():
    sql = (
        "SELECT * FROM ecommerce.orders o JOIN ecommerce.customers c "
        "ON o.customer_id > c.customer_id"
    )
    assert extract_join_predicates(sql) == []


def test_literal_filter_is_not_a_join_predicate():
    sql = (
        "SELECT * FROM ecommerce.orders o JOIN ecommerce.customers c "
        "ON o.customer_id = c.customer_id WHERE o.status = 'paid'"
    )
    assert len(extract_join_predicates(sql)) == 1


def test_unknown_table_is_skipped():
    sql = "SELECT * FROM ecommerce.orders o JOIN public.widgets w ON o.customer_id = w.id"
    assert extract_join_predicates(sql) == []


def test_multiple_joins_in_one_statement():
    sql = (
        "SELECT * FROM ecommerce.order_items oi "
        "JOIN ecommerce.orders o ON oi.order_id = o.order_id "
        "JOIN ecommerce.products p ON oi.product_id = p.product_id"
    )
    assert len(extract_join_predicates(sql)) == 2
