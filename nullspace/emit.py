"""Emit and verify the native DataHub aspects behind Nullspace's claims."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from datahub.metadata.schema_classes import (
    AuditStampClass,
    CorpUserInfoClass,
    DatasetLineageTypeClass,
    DatasetPropertiesClass,
    GlobalTagsClass,
    NumberTypeClass,
    OtherSchemaClass,
    OwnerClass,
    OwnershipClass,
    OwnershipTypeClass,
    OwnershipTypeInfoClass,
    OwnershipTypeKeyClass,
    SchemaFieldClass,
    SchemaFieldDataTypeClass,
    SchemaMetadataClass,
    StringTypeClass,
    TagAssociationClass,
    TagPropertiesClass,
    UpstreamClass,
    UpstreamLineageClass,
)

from nullspace import GHOST_TAG, PLATFORM, SOLID_TAG
from nullspace.client import DataHubClient, now_ms
from nullspace.ghosts import Ghost
from nullspace.urns import corpuser_urn

_ACTOR = "urn:li:corpuser:datahub"
_PLATFORM_URN = f"urn:li:dataPlatform:{PLATFORM}"
_REQUESTER_TYPE_ID = "nullspace_requester"
_REQUESTER_TYPE_URN = f"urn:li:ownershipType:{_REQUESTER_TYPE_ID}"


def _audit() -> AuditStampClass:
    return AuditStampClass(time=now_ms(), actor=_ACTOR)


def emit_ghost(dh: DataHubClient, ghost: Ghost) -> dict[str, Any]:
    """Upsert native aspects, then return DataHub's read-back witness."""
    tag = SOLID_TAG if ghost.state == "solid" else GHOST_TAG
    description = (
        f"Nullspace {'SOLID' if ghost.state == 'solid' else 'GHOST'} for demand: {ghost.want}"
    )
    custom = {
        "nullspace.demand": str(ghost.demand),
        "nullspace.want": ghost.want,
        "nullspace.state": ghost.state,
        "nullspace.requesters": ",".join(ghost.requesters),
        "nullspace.claimed_by": ghost.claimed_by or "",
        "nullspace.pr_url": ghost.pr_url or "",
        "nullspace.resolution": json.dumps(
            [
                {
                    "agent_id": e.agent_id,
                    "at_ms": e.at_ms,
                    "event": e.event,
                    "detail": e.detail,
                }
                for e in ghost.resolution
            ]
        ),
    }

    props = DatasetPropertiesClass(
        name=ghost.dataset_name,
        description=description,
        customProperties=custom,
    )
    tag_urn = f"urn:li:tag:{tag}"
    dh.emit_aspect(
        tag_urn,
        TagPropertiesClass(name=tag, description=f"Nullspace {tag} marker"),
    )
    returned_tag = dh.graph.get_aspect(tag_urn, TagPropertiesClass)
    if returned_tag is None or returned_tag.name != tag:
        raise RuntimeError(
            f"DataHub tag read-after-write failed: returned {returned_tag!r}, expected {tag!r}"
        )
    dh.emit_aspect(ghost.urn, props)
    dh.emit_aspect(
        ghost.urn,
        GlobalTagsClass(tags=[TagAssociationClass(tag=tag_urn)]),
    )

    if ghost.state == "solid":
        _emit_schema(dh, ghost)
        _emit_lineage(dh, ghost)
        _emit_requester_ownership(dh, ghost)

    witness = dh.solid_witness(ghost.urn)
    if ghost.state == "solid":
        _verify_solid_witness(ghost, witness)
    return witness


def _field_type(native_type: str) -> SchemaFieldDataTypeClass:
    normalized = native_type.upper()
    primitive = (
        NumberTypeClass()
        if any(token in normalized for token in ("INT", "NUMERIC", "DECIMAL", "FLOAT", "DOUBLE"))
        else StringTypeClass()
    )
    return SchemaFieldDataTypeClass(type=primitive)


def _emit_schema(dh: DataHubClient, ghost: Ghost) -> None:
    raw_schema = json.dumps(ghost.schema_fields, sort_keys=True)
    fields = [
        SchemaFieldClass(
            fieldPath=str(field["name"]),
            type=_field_type(str(field.get("native_type", "VARCHAR"))),
            nativeDataType=str(field.get("native_type", "VARCHAR")),
            nullable=bool(field.get("nullable", True)),
            description=f"Nullspace solid field for demand: {ghost.want}",
        )
        for field in ghost.schema_fields
    ]
    schema = SchemaMetadataClass(
        schemaName=ghost.dataset_name,
        platform=_PLATFORM_URN,
        version=0,
        hash=hashlib.sha256(raw_schema.encode()).hexdigest(),
        platformSchema=OtherSchemaClass(rawSchema=raw_schema),
        fields=fields,
        created=_audit(),
        lastModified=_audit(),
        dataset=ghost.urn,
    )
    dh.emit_aspect(ghost.urn, schema)


def _emit_lineage(dh: DataHubClient, ghost: Ghost) -> None:
    lineage = UpstreamLineageClass(
        upstreams=[
            UpstreamClass(
                dataset=urn,
                type=DatasetLineageTypeClass.TRANSFORMED,
                auditStamp=_audit(),
                properties={"nullspace": "dbt source read during solidify"},
            )
            for urn in ghost.upstream_urns
        ]
    )
    dh.emit_aspect(ghost.urn, lineage)


def _emit_requester_ownership(dh: DataHubClient, ghost: Ghost) -> None:
    dh.emit_aspect(
        _REQUESTER_TYPE_URN,
        OwnershipTypeKeyClass(id=_REQUESTER_TYPE_ID),
    )
    dh.emit_aspect(
        _REQUESTER_TYPE_URN,
        OwnershipTypeInfoClass(
            name="Nullspace requester",
            description="AI agent whose catalog miss created demand for this asset",
            created=_audit(),
            lastModified=_audit(),
        ),
    )
    returned_type = dh.graph.get_aspect(_REQUESTER_TYPE_URN, OwnershipTypeInfoClass)
    if returned_type is None or returned_type.name != "Nullspace requester":
        raise RuntimeError(
            "DataHub ownership-type read-after-write failed: "
            f"returned {returned_type!r}"
        )

    owners = []
    for requester in ghost.requesters:
        owner_urn = corpuser_urn(requester)
        dh.emit_aspect(
            owner_urn,
            CorpUserInfoClass(
                active=True,
                displayName=requester,
                title="AI requester agent",
                system=True,
                customProperties={
                    "nullspace.role": "requester",
                    "nullspace.asset": ghost.urn,
                },
            ),
        )
        returned_requester = dh.graph.get_aspect(owner_urn, CorpUserInfoClass)
        if (
            returned_requester is None
            or returned_requester.displayName != requester
        ):
            raise RuntimeError(
                "DataHub requester read-after-write failed: "
                f"returned {returned_requester!r}, expected {requester!r}"
            )
        owners.append(
            OwnerClass(
                owner=owner_urn,
                type=OwnershipTypeClass.CUSTOM,
                typeUrn=_REQUESTER_TYPE_URN,
            )
        )
    dh.emit_aspect(
        ghost.urn,
        OwnershipClass(owners=owners, lastModified=_audit()),
    )


def _verify_solid_witness(ghost: Ghost, witness: dict[str, Any]) -> None:
    returned_fields = {
        field["fieldPath"]
        for field in (witness.get("schemaMetadata") or {}).get("fields", [])
    }
    expected_fields = {str(field["name"]) for field in ghost.schema_fields}
    returned_upstreams = {
        upstream["dataset"]
        for upstream in witness.get("lineage", {}).get("upstreams", [])
    }
    returned_owners = {
        owner["owner"]
        for owner in witness.get("ownership", {}).get("owners", [])
        if owner.get("typeUrn") == _REQUESTER_TYPE_URN
    }
    expected_owners = {corpuser_urn(requester) for requester in ghost.requesters}

    failures = []
    if not expected_fields.issubset(returned_fields):
        failures.append(
            f"schema fields returned {sorted(returned_fields)}, expected {sorted(expected_fields)}"
        )
    if not set(ghost.upstream_urns).issubset(returned_upstreams):
        failures.append(
            f"lineage returned {sorted(returned_upstreams)}, "
            f"expected {sorted(ghost.upstream_urns)}"
        )
    if not expected_owners.issubset(returned_owners):
        failures.append(
            f"ownership returned {sorted(returned_owners)}, "
            f"expected {sorted(expected_owners)}"
        )
    expected_tag = f"urn:li:tag:{SOLID_TAG}"
    if expected_tag not in witness.get("tags", []):
        failures.append(
            f"tags returned {witness.get('tags', [])}, expected {expected_tag!r}"
        )
    if failures:
        raise RuntimeError(
            "DataHub solid read-after-write failed: "
            + "; ".join(failures)
            + f"; witness={json.dumps(witness, sort_keys=True)}"
        )


def board_snapshot(ghosts: list[Ghost]) -> dict[str, Any]:
    return {
        "product": "nullspace",
        "ghosts": [g.to_public() for g in ghosts],
        "counts": {
            "ghost": sum(1 for g in ghosts if g.state == "ghost"),
            "claimed": sum(1 for g in ghosts if g.state == "claimed"),
            "solid": sum(1 for g in ghosts if g.state == "solid"),
        },
    }
