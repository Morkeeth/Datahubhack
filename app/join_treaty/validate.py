"""Deterministic validation gates for a candidate join treaty.

The rules require *positive* evidence. When profiles do not support a
cardinality, the candidate is rejected (abstain) rather than guessed. We never
claim a verified foreign key — only an observed join treaty.
"""

from __future__ import annotations

from typing import Dict

from .config import MIN_QUERY_OCCURRENCES, normalize_type
from .datahub import DatasetFacts
from .model import Gate, JoinCandidate, Verdict

# ERModelRelationship cardinality values (mirror the SDK enum as strings).
CARD_ONE_ONE = "ONE_ONE"
CARD_N_ONE = "N_ONE"

_UNIQUE_TOLERANCE = 0.999


def _is_unique(facts: DatasetFacts, field: str) -> bool | None:
    fp = facts.profiles.get(field)
    if fp is None or fp.unique_proportion is None:
        return None
    return fp.unique_proportion >= _UNIQUE_TOLERANCE


def validate_candidate(
    candidate: JoinCandidate,
    facts_by_urn: Dict[str, DatasetFacts],
    min_occurrences: int = MIN_QUERY_OCCURRENCES,
) -> Verdict:
    pred = candidate.predicate
    left, right = pred.left, pred.right
    verdict = Verdict(candidate_id=candidate.id, accepted=False)

    # Gate 1: repeated independent evidence.
    occ = candidate.occurrences
    g1 = Gate(
        name="repeated_evidence",
        passed=occ >= min_occurrences,
        detail=f"{occ} distinct query URNs (need >= {min_occurrences})",
    )
    verdict.gates.append(g1)

    lf = facts_by_urn.get(left.dataset_urn)
    rf = facts_by_urn.get(right.dataset_urn)

    # Gate 2: field existence.
    left_exists = bool(lf and left.field in lf.fields)
    right_exists = bool(rf and right.field in rf.fields)
    g2 = Gate(
        name="fields_exist",
        passed=left_exists and right_exists,
        detail=(
            f"{left.field}@{_short(left.dataset_urn)}={left_exists}, "
            f"{right.field}@{_short(right.dataset_urn)}={right_exists}"
        ),
    )
    verdict.gates.append(g2)

    # Gate 3: type compatibility (only meaningful if fields exist).
    if left_exists and right_exists:
        lt = normalize_type(lf.fields[left.field])
        rt = normalize_type(rf.fields[right.field])
        compatible = lt != "unknown" and lt == rt
        g3 = Gate(
            name="type_compatible",
            passed=compatible,
            detail=f"{lf.fields[left.field]}({lt}) vs {rf.fields[right.field]}({rt})",
        )
    else:
        g3 = Gate(name="type_compatible", passed=False, detail="fields missing")
    verdict.gates.append(g3)

    # Gate 4: profile-supported cardinality (positive evidence required).
    cardinality = None
    source_urn = destination_urn = source_field = destination_field = None
    if left_exists and right_exists:
        left_unique = _is_unique(lf, left.field)
        right_unique = _is_unique(rf, right.field)
        if left_unique is None or right_unique is None:
            g4 = Gate(
                name="cardinality_supported",
                passed=False,
                detail="missing column profile on one or both fields",
            )
        elif left_unique and right_unique:
            cardinality = CARD_ONE_ONE
            source_urn, source_field = left.dataset_urn, left.field
            destination_urn, destination_field = right.dataset_urn, right.field
            g4 = Gate(
                name="cardinality_supported",
                passed=True,
                detail="both sides unique -> ONE_ONE",
            )
        elif left_unique != right_unique:
            # unique side is the "one" (destination); other is the "many" (source)
            if left_unique:
                destination_urn, destination_field = left.dataset_urn, left.field
                source_urn, source_field = right.dataset_urn, right.field
            else:
                destination_urn, destination_field = right.dataset_urn, right.field
                source_urn, source_field = left.dataset_urn, left.field
            cardinality = CARD_N_ONE
            g4 = Gate(
                name="cardinality_supported",
                passed=True,
                detail=(
                    f"{_short(source_urn)}.{source_field} duplicated -> "
                    f"N:1 to {_short(destination_urn)}.{destination_field}"
                ),
            )
        else:
            g4 = Gate(
                name="cardinality_supported",
                passed=False,
                detail="neither side unique; abstain (no referential claim)",
            )
    else:
        g4 = Gate(
            name="cardinality_supported", passed=False, detail="fields missing"
        )
    verdict.gates.append(g4)

    verdict.accepted = all(g.passed for g in verdict.gates)
    if verdict.accepted:
        verdict.source_urn = source_urn
        verdict.destination_urn = destination_urn
        verdict.source_field = source_field
        verdict.destination_field = destination_field
        verdict.cardinality = cardinality
        verdict.reason = "observed join treaty with positive profile evidence"
    else:
        failed = ", ".join(g.name for g in verdict.failed_gates())
        verdict.reason = f"rejected: {failed}"
    return verdict


def _short(urn: str) -> str:
    try:
        return urn.split(",")[1].split(".")[-1]
    except Exception:
        return urn
