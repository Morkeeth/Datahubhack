"""Tests for evidence aggregation across query statements."""

from join_treaty.discover import discover_from_statements


ORDERS_CUSTOMERS = [
    "SELECT * FROM ecommerce.orders o JOIN ecommerce.customers c ON o.customer_id = c.customer_id",
    "SELECT o.order_id FROM ecommerce.orders o JOIN ecommerce.customers c ON o.customer_id = c.customer_id WHERE o.status='paid'",
    "SELECT * FROM ecommerce.customers c JOIN ecommerce.orders o ON c.customer_id = o.customer_id",
]


def test_repeated_join_aggregates_occurrences():
    statements = {f"urn:li:query:q{i}": sql for i, sql in enumerate(ORDERS_CUSTOMERS)}
    candidates = discover_from_statements(statements)
    assert len(candidates) == 1
    assert candidates[0].occurrences == 3


def test_same_query_counts_once():
    statements = {
        "urn:li:query:dup": ORDERS_CUSTOMERS[0],
    }
    candidates = discover_from_statements(statements)
    assert candidates[0].occurrences == 1


def test_distinct_joins_are_separate_candidates():
    statements = {
        "urn:li:query:a": ORDERS_CUSTOMERS[0],
        "urn:li:query:b": "SELECT * FROM ecommerce.order_items oi JOIN ecommerce.products p ON oi.product_id = p.product_id",
    }
    candidates = discover_from_statements(statements)
    assert len(candidates) == 2
