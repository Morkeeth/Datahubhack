"""Discover candidate join treaties from DataHub Query entities."""

from __future__ import annotations

from typing import Dict, List

from .datahub import DataHubClient
from .model import JoinCandidate, JoinPredicate, QueryEvidence
from .parser import extract_join_predicates


def discover_from_statements(
    statements: Dict[str, str], dialect: str = "postgres"
) -> List[JoinCandidate]:
    """Pure function: map of {query_urn: sql} -> candidates. Easy to unit test."""
    by_key: Dict[str, JoinCandidate] = {}
    predicates: Dict[str, JoinPredicate] = {}
    for query_urn, sql in statements.items():
        for predicate in extract_join_predicates(sql, dialect=dialect):
            key = predicate.key()
            predicates[key] = predicate
            candidate = by_key.get(key)
            if candidate is None:
                candidate = JoinCandidate(predicate=predicate, evidence=[])
                by_key[key] = candidate
            if all(e.query_urn != query_urn for e in candidate.evidence):
                candidate.evidence.append(
                    QueryEvidence(query_urn=query_urn, statement=sql)
                )
    return sorted(by_key.values(), key=lambda c: (-c.occurrences, c.id))


def discover(client: DataHubClient) -> List[JoinCandidate]:
    statements: Dict[str, str] = {}
    for urn in client.query_urns():
        stmt = client.query_statement(urn)
        if stmt:
            statements[urn] = stmt
    return discover_from_statements(statements, dialect=client.settings.dialect)
