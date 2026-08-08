"""Deterministic extraction of single-column equality join predicates.

By design this only accepts explicit ``JOIN ... ON a.col = b.col`` predicates in
a single dialect. Composite ON clauses (multiple ANDed equalities), implicit
WHERE joins, ``USING`` clauses, and non-equality predicates are ignored so the
verdict is reproducible and never over-claims.
"""

from __future__ import annotations

from typing import Dict, List, Optional

import sqlglot
from sqlglot import exp

from .config import SCHEMA, SQL_DIALECT, table_urn_by_short_name
from .model import ColumnRef, JoinPredicate


def _alias_map(tree: exp.Expression) -> Dict[str, str]:
    """Map every table alias/name in the statement to a ``schema.table`` key."""
    mapping: Dict[str, str] = {}
    for table in tree.find_all(exp.Table):
        real = table.name
        schema = table.db or SCHEMA
        qualified = f"{schema}.{real}"
        alias = table.alias_or_name  # alias if present else the table name
        mapping[alias] = qualified
        mapping[real] = qualified
        mapping[qualified] = qualified
    return mapping


def _resolve(column: exp.Column, aliases: Dict[str, str]) -> Optional[ColumnRef]:
    qualifier = column.table  # alias or table qualifier; '' if unqualified
    if not qualifier:
        return None
    qualified = aliases.get(qualifier)
    if not qualified:
        return None
    urn = table_urn_by_short_name().get(qualified)
    if not urn:
        return None
    return ColumnRef(dataset_urn=urn, field=column.name)


def _predicate_from_on(
    on_expr: exp.Expression, aliases: Dict[str, str]
) -> Optional[JoinPredicate]:
    # Reject composite ON clauses outright (no composite joins in scope).
    if not isinstance(on_expr, exp.EQ):
        return None
    left, right = on_expr.left, on_expr.right
    if not (isinstance(left, exp.Column) and isinstance(right, exp.Column)):
        return None
    lref = _resolve(left, aliases)
    rref = _resolve(right, aliases)
    if lref is None or rref is None:
        return None
    if lref.dataset_urn == rref.dataset_urn:
        return None  # self-join on the same dataset is not a treaty
    return JoinPredicate.canonical(lref, rref)


def extract_join_predicates(sql: str, dialect: str = SQL_DIALECT) -> List[JoinPredicate]:
    """Return the canonical single-column equality joins in one SQL statement."""
    try:
        tree = sqlglot.parse_one(sql, dialect=dialect)
    except Exception:
        return []
    if tree is None:
        return []

    aliases = _alias_map(tree)
    found: Dict[str, JoinPredicate] = {}
    for join in tree.find_all(exp.Join):
        on_expr = join.args.get("on")
        if on_expr is None:
            continue
        predicate = _predicate_from_on(on_expr, aliases)
        if predicate is not None:
            found[predicate.key()] = predicate
    return list(found.values())
