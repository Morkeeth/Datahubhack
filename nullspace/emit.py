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
    InstitutionalMemoryClass,
    InstitutionalMemoryMetadataClass,
    NumberTypeClass,
    OtherSchemaClass,
    OwnerClass,
    OwnershipClass,
    OwnershipTypeClass,
    OwnershipTypeInfoClass,
    OwnershipTypeKeyClass,
    QueryLanguageClass,
    QueryPropertiesClass,
    QuerySourceClass,
    QueryStatementClass,
    QuerySubjectClass,
    QuerySubjectsClass,
    SchemaFieldClass,
    SchemaFieldDataTypeClass,
    SchemaMetadataClass,
    StringTypeClass,
    StructuredPropertiesClass,
    StructuredPropertyDefinitionClass,
    StructuredPropertyValueAssignmentClass,
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

_SP_DEMAND = "urn:li:structuredProperty:nullspace.demand"
_SP_STATE = "urn:li:structuredProperty:nullspace.state"
_SP_WANT = "urn:li:structuredProperty:nullspace.want"
_STRUCTURED_DEFS = (
    (_SP_DEMAND, "nullspace.demand", "urn:li:dataType:datahub.number", "Nullspace demand"),
    (_SP_STATE, "nullspace.state", "urn:li:dataType:datahub.string", "Nullspace state"),
    (_SP_WANT, "nullspace.want", "urn:li:dataType:datahub.string", "Nullspace want"),
)


def _audit() -> AuditStampClass:
    return AuditStampClass(time=now_ms(), actor=_ACTOR)


def ensure_structured_property_definitions(dh: DataHubClient) -> None:
    """Register nullspace.* structured properties on stock GMS (idempotent)."""
    audit = _audit()
    for urn, qname, value_type, display in _STRUCTURED_DEFS:
        dh.emit_aspect(
            urn,
            StructuredPropertyDefinitionClass(
                qualifiedName=qname,
                displayName=display,
                valueType=value_type,
                entityTypes=["urn:li:entityType:datahub.dataset"],
                cardinality="SINGLE",
                description=(
                    f"{display} — demand-side metadata for assets that do not "
                    "exist yet (Nullspace)"
                ),
                immutable=False,
                created=audit,
                lastModified=audit,
            ),
        )
        returned = dh.graph.get_aspect(urn, StructuredPropertyDefinitionClass)
        if returned is None or returned.qualifiedName != qname:
            raise RuntimeError(
                "DataHub structuredProperty definition read-after-write failed: "
                f"returned {returned!r}, expected {qname!r}"
            )


def emit_ghost(dh: DataHubClient, ghost: Ghost) -> dict[str, Any]:
    """Upsert native aspects, then return DataHub's read-back witness."""
    tag = SOLID_TAG if ghost.state == "solid" else GHOST_TAG
    description = (
        f"Nullspace {'SOLID' if ghost.state == 'solid' else 'GHOST'} for demand: {ghost.want}"
    )
    prior = dh.dataset_custom_properties(ghost.urn)
    custom = {
        "nullspace.demand": str(ghost.demand),
        "nullspace.want": ghost.want,
        "nullspace.state": ghost.state,
        "nullspace.requesters": ",".join(ghost.requesters),
        "nullspace.claimed_by": ghost.claimed_by or "",
        "nullspace.pr_url": ghost.pr_url or "",
        "nullspace.schema_source": ghost.schema_source or "",
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
    if prior.get("nullspace.contracts"):
        custom["nullspace.contracts"] = prior["nullspace.contracts"]
    if prior.get("nullspace.query_urns"):
        custom["nullspace.query_urns"] = prior["nullspace.query_urns"]
    if prior.get("nullspace.builder_plan"):
        custom["nullspace.builder_plan"] = prior["nullspace.builder_plan"]

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

    # First-class lifecycle (maintainer-visible). Dual-write customProperties so the
    # GraphQL board keeps working without a Lane B change this weekend.
    _emit_structured_lifecycle(dh, ghost)
    if ghost.requesters:
        _emit_requester_ownership(dh, ghost)
    if ghost.pr_url:
        _emit_pr_institutional_memory(dh, ghost)

    if ghost.state == "solid":
        if not ghost.schema_fields or not ghost.upstream_urns:
            raise RuntimeError(
                "solid emit refused: refusing to mirror a solid ghost with "
                f"{len(ghost.schema_fields)} schema fields and "
                f"{len(ghost.upstream_urns)} upstreams; shortfall is a hydrated "
                "builder schema + lineage (refusing empty overwrite)"
            )
        _emit_schema(dh, ghost)
        _emit_lineage(dh, ghost)

    witness = dh.solid_witness(ghost.urn)
    if not dh.wait_for_search_urn(ghost.want, ghost.urn):
        raise RuntimeError(
            "DataHub search-index read-after-write failed: "
            f"{ghost.urn!r} was not returned for {ghost.want!r}"
        )
    if ghost.state == "solid":
        _verify_solid_witness(ghost, witness)
        indexed_upstreams = dh.wait_for_indexed_upstreams(
            ghost.urn, set(ghost.upstream_urns)
        )
        witness["indexedLineage"] = {
            "upstreams": sorted(indexed_upstreams),
            "count": len(indexed_upstreams),
        }
        if not set(ghost.upstream_urns).issubset(indexed_upstreams):
            raise RuntimeError(
                "DataHub lineage index read-after-write failed: "
                f"returned {sorted(indexed_upstreams)}, "
                f"expected {sorted(ghost.upstream_urns)}"
            )
    return witness


def _emit_structured_lifecycle(dh: DataHubClient, ghost: Ghost) -> None:
    ensure_structured_property_definitions(dh)
    audit = _audit()
    dh.emit_aspect(
        ghost.urn,
        StructuredPropertiesClass(
            properties=[
                StructuredPropertyValueAssignmentClass(
                    propertyUrn=_SP_DEMAND,
                    values=[float(ghost.demand)],
                    created=audit,
                    lastModified=audit,
                ),
                StructuredPropertyValueAssignmentClass(
                    propertyUrn=_SP_STATE,
                    values=[ghost.state],
                    created=audit,
                    lastModified=audit,
                ),
                StructuredPropertyValueAssignmentClass(
                    propertyUrn=_SP_WANT,
                    values=[ghost.want],
                    created=audit,
                    lastModified=audit,
                ),
            ]
        ),
    )
    returned = dh.graph.get_aspect(ghost.urn, StructuredPropertiesClass)
    if returned is None:
        raise RuntimeError(
            "DataHub structuredProperties read-after-write failed: returned None"
        )
    by_urn = {p.propertyUrn: list(p.values) for p in returned.properties}
    if by_urn.get(_SP_STATE) != [ghost.state]:
        raise RuntimeError(
            "DataHub structuredProperties state mismatch: "
            f"returned {by_urn.get(_SP_STATE)!r}, expected {[ghost.state]!r}"
        )


def _emit_pr_institutional_memory(dh: DataHubClient, ghost: Ghost) -> None:
    """Surface the fulfillment PR on the dataset Links tab (stock aspect)."""
    assert ghost.pr_url
    memory = InstitutionalMemoryClass(
        elements=[
            InstitutionalMemoryMetadataClass(
                url=ghost.pr_url,
                description=(
                    "Nullspace builder change reference — merge solidifies this ghost"
                    if str(ghost.pr_url).startswith("https://github.com/")
                    else "Nullspace local change reference (not a GitHub PR)"
                ),
                createStamp=_audit(),
            )
        ]
    )
    dh.emit_aspect(ghost.urn, memory)


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
            )
            for urn in ghost.upstream_urns
        ]
    )
    dh.emit_aspect(ghost.urn, lineage)
    returned = dh.graph.get_aspect(ghost.urn, UpstreamLineageClass)
    returned_urns = {
        upstream.dataset for upstream in (returned.upstreams if returned else [])
    }
    if not set(ghost.upstream_urns).issubset(returned_urns):
        raise RuntimeError(
            "DataHub upstreamLineage read-after-write failed: "
            f"returned {sorted(returned_urns)}, expected {sorted(ghost.upstream_urns)}"
        )


def _emit_requester_ownership(dh: DataHubClient, ghost: Ghost) -> None:
    """Requesters are native Owners from the first miss — not only after solidify."""
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


def _contract_query_urn(agent_id: str, want: str, sql: str) -> str:
    digest = hashlib.sha1(
        f"{agent_id}|{want.strip().lower()}|{sql}".encode()
    ).hexdigest()[:20]
    return f"urn:li:query:nullspace_{digest}"


def emit_contracts(
    dh: DataHubClient, urn: str, contracts: list[dict[str, Any]]
) -> dict[str, Any]:
    """Write requester contracts as Query entities + dual-write JSON on the ghost.

    Queries are first-class (QueryProperties + QuerySubjects → ghost URN).
    ``nullspace.contracts`` JSON remains so the board/hydrate keep working.
    """
    props = dh.graph.get_aspect(urn, DatasetPropertiesClass)
    if props is None:
        raise RuntimeError(
            f"emit_contracts refused: no datasetProperties on {urn!r}; "
            "shortfall is 1 ghost already mirrored to DataHub"
        )
    query_urns: list[str] = []
    audit = _audit()
    for row in contracts:
        sql = str(row.get("sql") or "")
        agent_id = str(row.get("agent_id") or "unknown")
        want = str(row.get("want") or "")
        qurn = _contract_query_urn(agent_id, want, sql)
        fields = row.get("needs_fields") or []
        dh.emit_aspect(
            qurn,
            QueryPropertiesClass(
                statement=QueryStatementClass(
                    value=sql or f"-- fields: {', '.join(map(str, fields))}",
                    language=QueryLanguageClass.SQL,
                ),
                source=QuerySourceClass.MANUAL,
                created=audit,
                lastModified=audit,
                name=f"nullspace:{agent_id}",
                description=json.dumps(
                    {
                        "want": want,
                        "agent_id": agent_id,
                        "needs_fields": list(fields),
                    },
                    sort_keys=True,
                ),
            ),
        )
        dh.emit_aspect(
            qurn,
            QuerySubjectsClass(subjects=[QuerySubjectClass(entity=urn)]),
        )
        query_urns.append(qurn)

    custom = dict(props.customProperties or {})
    custom["nullspace.contracts"] = json.dumps(contracts)
    custom["nullspace.query_urns"] = ",".join(query_urns)
    updated = DatasetPropertiesClass(
        name=props.name,
        description=props.description,
        customProperties=custom,
    )
    dh.emit_aspect(urn, updated)
    read_back = dh.dataset_custom_properties(urn)
    if read_back.get("nullspace.contracts") != custom["nullspace.contracts"]:
        raise RuntimeError(
            "DataHub contracts read-after-write failed: "
            f"returned {read_back.get('nullspace.contracts')!r}"
        )
    return {
        "urn": urn,
        "properties": read_back,
        "query_urns": query_urns,
    }


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
