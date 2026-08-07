"""Seed real DataHub Query entities against the ingested warehouse datasets.

The warehouse has schemas and profiles but no query history, so we explicitly
enrich DataHub with `Query` entities. These are real entities (QueryProperties +
QuerySubjects) written to GMS, not mocked evidence. Query URNs are derived from
the statement text so re-seeding is idempotent.

The set contains three genuine repeated joins plus two negatives: one that is
type-incompatible (passes the occurrence gate, fails type) and one that appears
only once (fails the occurrence gate).
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import List

from .config import SCHEMA
from .datahub import DataHubClient


@dataclass(frozen=True)
class SeedQuery:
    name: str
    statement: str
    subjects: List[str]  # short table names

    @property
    def urn(self) -> str:
        digest = hashlib.md5(self.statement.strip().encode("utf-8")).hexdigest()[:16]
        return f"urn:li:query:jointreaty-{digest}"


def _t(table: str) -> str:
    return f"{SCHEMA}.{table}"


# --- three genuine repeated joins (each appears in 3 independent queries) ----
_ORDERS_CUSTOMERS = [
    "SELECT c.email, count(*) AS orders "
    f"FROM {_t('orders')} o JOIN {_t('customers')} c "
    "ON o.customer_id = c.customer_id GROUP BY c.email",
    f"SELECT o.order_id, c.country_code FROM {_t('orders')} AS o "
    f"JOIN {_t('customers')} AS c ON o.customer_id = c.customer_id "
    "WHERE o.status = 'paid'",
    f"SELECT c.customer_id, max(o.ordered_at) FROM {_t('customers')} c "
    f"JOIN {_t('orders')} o ON c.customer_id = o.customer_id "
    "GROUP BY c.customer_id",
]

_ITEMS_ORDERS = [
    f"SELECT o.order_id, sum(oi.quantity) FROM {_t('order_items')} oi "
    f"JOIN {_t('orders')} o ON oi.order_id = o.order_id GROUP BY o.order_id",
    f"SELECT * FROM {_t('orders')} o JOIN {_t('order_items')} oi "
    "ON o.order_id = oi.order_id WHERE o.status = 'shipped'",
    f"SELECT oi.product_id, o.customer_id FROM {_t('order_items')} AS oi "
    f"JOIN {_t('orders')} AS o ON oi.order_id = o.order_id",
]

_ITEMS_PRODUCTS = [
    f"SELECT p.name, sum(oi.quantity) FROM {_t('order_items')} oi "
    f"JOIN {_t('products')} p ON oi.product_id = p.product_id GROUP BY p.name",
    f"SELECT oi.order_id, p.sku FROM {_t('products')} p "
    f"JOIN {_t('order_items')} oi ON p.product_id = oi.product_id",
    f"SELECT * FROM {_t('order_items')} AS oi JOIN {_t('products')} AS p "
    "ON oi.product_id = p.product_id WHERE p.unit_price > 10",
]

# --- negative 1: type-incompatible join, repeated 3x (fails the type gate) ----
_TYPE_MISMATCH = [
    f"SELECT * FROM {_t('orders')} o JOIN {_t('customers')} c "
    "ON o.status = c.customer_id",
    f"SELECT o.order_id FROM {_t('orders')} o JOIN {_t('customers')} c "
    "ON o.status = c.customer_id WHERE c.country_code = 'US'",
    f"SELECT c.email FROM {_t('customers')} c JOIN {_t('orders')} o "
    "ON c.customer_id = o.status",
]

# --- negative 2: plausible key types but only a single occurrence -------------
_UNDER_THRESHOLD = [
    f"SELECT * FROM {_t('order_items')} oi JOIN {_t('products')} p "
    "ON oi.quantity = p.product_id",
]


def build_seed_queries() -> List[SeedQuery]:
    queries: List[SeedQuery] = []
    for i, sql in enumerate(_ORDERS_CUSTOMERS, 1):
        queries.append(SeedQuery(f"orders_customers_{i}", sql, ["orders", "customers"]))
    for i, sql in enumerate(_ITEMS_ORDERS, 1):
        queries.append(SeedQuery(f"items_orders_{i}", sql, ["order_items", "orders"]))
    for i, sql in enumerate(_ITEMS_PRODUCTS, 1):
        queries.append(
            SeedQuery(f"items_products_{i}", sql, ["order_items", "products"])
        )
    for i, sql in enumerate(_TYPE_MISMATCH, 1):
        queries.append(
            SeedQuery(f"type_mismatch_{i}", sql, ["orders", "customers"])
        )
    for i, sql in enumerate(_UNDER_THRESHOLD, 1):
        queries.append(
            SeedQuery(f"under_threshold_{i}", sql, ["order_items", "products"])
        )
    return queries


def seed(client: DataHubClient) -> List[str]:
    from .config import dataset_urn

    emitted: List[str] = []
    for q in build_seed_queries():
        subject_urns = [dataset_urn(t) for t in q.subjects]
        client.emit_query_entity(
            query_urn=q.urn,
            statement=q.statement,
            subject_urns=subject_urns,
            name=q.name,
        )
        emitted.append(q.urn)
    return emitted
