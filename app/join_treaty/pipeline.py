"""Orchestration: audit (discover + validate) and apply."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from .apply import apply_treaty, treaty_exists
from .datahub import DatasetFacts, DataHubClient
from .discover import discover
from .model import JoinCandidate, TreatyReceipt, Verdict
from .validate import validate_candidate


@dataclass
class AuditItem:
    candidate: JoinCandidate
    verdict: Verdict


@dataclass
class AuditResult:
    run_id: str
    items: List[AuditItem] = field(default_factory=list)
    facts: Dict[str, DatasetFacts] = field(default_factory=dict)

    def accepted(self) -> List[AuditItem]:
        return [i for i in self.items if i.verdict.accepted]

    def rejected(self) -> List[AuditItem]:
        return [i for i in self.items if not i.verdict.accepted]

    def find(self, candidate_id: str) -> Optional[AuditItem]:
        for item in self.items:
            if item.candidate.id == candidate_id:
                return item
        return None


def _new_run_id() -> str:
    return f"run-{int(time.time())}"


def audit(client: DataHubClient) -> AuditResult:
    candidates = discover(client)

    # Gather dataset facts once per involved dataset.
    urns = set()
    for c in candidates:
        urns.add(c.predicate.left.dataset_urn)
        urns.add(c.predicate.right.dataset_urn)
    facts: Dict[str, DatasetFacts] = {u: client.dataset_facts(u) for u in urns}

    result = AuditResult(run_id=_new_run_id(), facts=facts)
    for c in candidates:
        verdict = validate_candidate(c, facts, client.settings.min_query_occurrences)
        result.items.append(AuditItem(candidate=c, verdict=verdict))
    return result


def apply_candidate(
    client: DataHubClient, result: AuditResult, candidate_id: str
) -> Tuple[TreatyReceipt, bool]:
    """Apply one accepted candidate. Returns (receipt, was_new)."""
    item = result.find(candidate_id)
    if item is None:
        raise KeyError(f"unknown candidate id: {candidate_id}")
    if not item.verdict.accepted:
        raise ValueError(f"candidate {candidate_id} was rejected: {item.verdict.reason}")
    was_new = not treaty_exists(client, candidate_id)
    receipt = apply_treaty(client, item.candidate, item.verdict, result.run_id)
    return receipt, was_new
