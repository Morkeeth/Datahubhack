"""Typed run model for the Join Treaty pipeline.

These structures are plain dataclasses so they serialize cleanly into the
offline receipt and the web view, and so tests can construct them directly.
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class ColumnRef:
    """A single (dataset, field) coordinate."""

    dataset_urn: str
    field: str

    def key(self) -> str:
        return f"{self.dataset_urn}::{self.field}"


@dataclass(frozen=True)
class JoinPredicate:
    """One parsed single-column equality join predicate.

    `left` and `right` are stored in a canonical (sorted) order so that the same
    logical join from different queries collapses to the same predicate.
    """

    left: ColumnRef
    right: ColumnRef

    @staticmethod
    def canonical(a: ColumnRef, b: ColumnRef) -> "JoinPredicate":
        return JoinPredicate(*sorted((a, b), key=lambda c: c.key()))

    def key(self) -> str:
        return f"{self.left.key()}=={self.right.key()}"


@dataclass
class QueryEvidence:
    """A query that supports a join predicate."""

    query_urn: str
    statement: str


@dataclass
class JoinCandidate:
    """A repeated join predicate with its supporting query evidence."""

    predicate: JoinPredicate
    evidence: List[QueryEvidence] = field(default_factory=list)

    @property
    def occurrences(self) -> int:
        return len({e.query_urn for e in self.evidence})

    @property
    def id(self) -> str:
        """Stable, human-readable id derived from the datasets and fields."""

        def short(ref: ColumnRef) -> str:
            table = ref.dataset_urn.split(",")[1].split(".")[-1]
            return f"{table}.{ref.field}"

        return f"{short(self.predicate.left)}__{short(self.predicate.right)}".replace(
            ".", "_"
        )


@dataclass
class Gate:
    """A single validation gate outcome."""

    name: str
    passed: bool
    detail: str


@dataclass
class Verdict:
    """The full deterministic verdict for a candidate."""

    candidate_id: str
    accepted: bool
    gates: List[Gate] = field(default_factory=list)
    # Directional result, only set when accepted.
    source_urn: Optional[str] = None
    destination_urn: Optional[str] = None
    source_field: Optional[str] = None
    destination_field: Optional[str] = None
    cardinality: Optional[str] = None
    reason: str = ""

    def failed_gates(self) -> List[Gate]:
        return [g for g in self.gates if not g.passed]


@dataclass
class TreatyReceipt:
    """The offline artifact + native receipt payload for one applied treaty."""

    run_id: str
    candidate_id: str
    er_relationship_urn: str
    source_urn: str
    destination_urn: str
    source_field: str
    destination_field: str
    cardinality: str
    evidence_query_urns: List[str]
    evidence_count: int
    gates: List[Dict[str, Any]]
    read_after_write: Dict[str, Any] = field(default_factory=dict)
    created_at: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return dataclasses.asdict(self)
