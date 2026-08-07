"""Deterministic configuration for the Join Treaty pipeline.

Everything that influences a verdict lives here so runs are reproducible and
auditable. No thresholds are hidden inside the logic modules.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Dict, List


# Warehouse coordinates as ingested by the substrate (`infra/datahub/postgres.yml`).
PLATFORM = "postgres"
PLATFORM_INSTANCE = "local-warehouse"
DATABASE = "warehouse"
SCHEMA = "ecommerce"
ENV = "DEV"

# Minimum number of *distinct* Query URNs a join must appear in to be considered.
MIN_QUERY_OCCURRENCES = 3

# SQL dialect for deterministic parsing (single dialect by design).
SQL_DIALECT = "postgres"

# Custom-property key prefix for the dataset receipts (visible in DataHub UI).
RECEIPT_PREFIX = "join_treaty"

# Normalized type buckets: two fields are join-compatible only within a bucket.
TYPE_BUCKETS: Dict[str, str] = {
    "SMALLINT": "integer",
    "INTEGER": "integer",
    "INT": "integer",
    "BIGINT": "integer",
    "SERIAL": "integer",
    "BIGSERIAL": "integer",
    "NUMERIC": "numeric",
    "DECIMAL": "numeric",
    "REAL": "numeric",
    "DOUBLE PRECISION": "numeric",
    "TEXT": "string",
    "VARCHAR": "string",
    "CHARACTER VARYING": "string",
    "CHAR": "string",
    "CHARACTER": "string",
    "UUID": "string",
    "BOOLEAN": "boolean",
    "BOOL": "boolean",
    "DATE": "temporal",
    "TIMESTAMP": "temporal",
    "TIMESTAMP WITHOUT TIME ZONE": "temporal",
    "TIMESTAMP WITH TIME ZONE": "temporal",
}


def gms_url() -> str:
    return os.environ.get("DATAHUB_GMS_URL", "http://localhost:8080")


def gms_token() -> str | None:
    return os.environ.get("DATAHUB_GMS_TOKEN") or None


def dataset_urn(table: str) -> str:
    """Dataset URN for a warehouse table, matching the ingested naming."""
    name = f"{PLATFORM_INSTANCE}.{DATABASE}.{SCHEMA}.{table}"
    return f"urn:li:dataset:(urn:li:dataPlatform:{PLATFORM},{name},{ENV})"


@dataclass(frozen=True)
class Table:
    name: str

    @property
    def urn(self) -> str:
        return dataset_urn(self.name)


# The four warehouse tables this MVP reasons about.
TABLES: List[Table] = [
    Table("customers"),
    Table("orders"),
    Table("order_items"),
    Table("products"),
]


def table_urn_by_short_name() -> Dict[str, str]:
    """Map both `table` and `schema.table` spellings to the dataset URN."""
    mapping: Dict[str, str] = {}
    for t in TABLES:
        mapping[t.name] = t.urn
        mapping[f"{SCHEMA}.{t.name}"] = t.urn
    return mapping


def normalize_type(native_type: str) -> str:
    """Return the coarse type bucket for a native SQL type, or 'unknown'."""
    key = (native_type or "").strip().upper()
    if key in TYPE_BUCKETS:
        return TYPE_BUCKETS[key]
    # Strip length/precision, e.g. CHAR(2) -> CHAR, NUMERIC(12,2) -> NUMERIC.
    base = key.split("(", 1)[0].strip()
    return TYPE_BUCKETS.get(base, "unknown")


@dataclass
class Settings:
    gms_url: str = field(default_factory=gms_url)
    gms_token: str | None = field(default_factory=gms_token)
    min_query_occurrences: int = MIN_QUERY_OCCURRENCES
    dialect: str = SQL_DIALECT
