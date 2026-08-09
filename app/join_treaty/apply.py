"""Persist an accepted treaty as a native ERModelRelationship + dataset receipts."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import List

from .config import RECEIPT_PREFIX
from .datahub import DataHubClient
from .model import JoinCandidate, TreatyReceipt, Verdict


def _short(urn: str) -> str:
    return urn.split(",")[1].split(".")[-1]


def treaty_exists(client: DataHubClient, candidate_id: str) -> bool:
    return client.er_relationship(candidate_id) is not None


def apply_treaty(
    client: DataHubClient,
    candidate: JoinCandidate,
    verdict: Verdict,
    run_id: str,
) -> TreatyReceipt:
    if not verdict.accepted:
        raise ValueError(f"candidate {candidate.id} is not accepted; refusing to write")

    rel_id = candidate.id
    src_table = _short(verdict.source_urn)
    dst_table = _short(verdict.destination_urn)
    name = (
        f"{src_table}.{verdict.source_field} -> "
        f"{dst_table}.{verdict.destination_field}"
    )
    query_urns: List[str] = sorted({e.query_urn for e in candidate.evidence})
    evidence_count = len(query_urns)

    custom_properties = {
        "treaty_version": "1",
        "kind": "observed_join_treaty",
        "run_id": run_id,
        "cardinality": verdict.cardinality,
        "source_field": verdict.source_field,
        "destination_field": verdict.destination_field,
        "evidence_count": str(evidence_count),
        "evidence_query_urns": ",".join(query_urns),
    }

    er_urn = client.emit_er_relationship(
        rel_id=rel_id,
        name=name,
        source_urn=verdict.source_urn,
        destination_urn=verdict.destination_urn,
        source_field=verdict.source_field,
        destination_field=verdict.destination_field,
        cardinality=verdict.cardinality,
        custom_properties=custom_properties,
    )

    receipt_key = f"{RECEIPT_PREFIX}:{rel_id}"
    receipt_value = json.dumps(
        {
            "relationship": er_urn,
            "join": name,
            "cardinality": verdict.cardinality,
            "evidence_count": evidence_count,
            "run_id": run_id,
        },
        separators=(",", ":"),
    )
    client.patch_dataset_receipt(verdict.source_urn, receipt_key, receipt_value)
    client.patch_dataset_receipt(verdict.destination_urn, receipt_key, receipt_value)

    # Read-after-write verification (native reads from GMS).
    er_props = client.er_relationship(rel_id)
    src_props = client.dataset_custom_properties(verdict.source_urn)
    dst_props = client.dataset_custom_properties(verdict.destination_urn)
    read_after_write = {
        "er_relationship_present": er_props is not None,
        "er_relationship_cardinality": getattr(er_props, "cardinality", None),
        "er_relationship_name": getattr(er_props, "name", None),
        "source_receipt_present": receipt_key in src_props,
        "destination_receipt_present": receipt_key in dst_props,
    }

    return TreatyReceipt(
        run_id=run_id,
        candidate_id=rel_id,
        er_relationship_urn=er_urn,
        source_urn=verdict.source_urn,
        destination_urn=verdict.destination_urn,
        source_field=verdict.source_field,
        destination_field=verdict.destination_field,
        cardinality=verdict.cardinality,
        evidence_query_urns=query_urns,
        evidence_count=evidence_count,
        gates=[{"name": g.name, "passed": g.passed, "detail": g.detail} for g in verdict.gates],
        read_after_write=read_after_write,
        created_at=datetime.now(timezone.utc).isoformat(),
    )
