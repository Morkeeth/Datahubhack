"""Emit ghost state into DataHub as dataset + tags + custom properties."""

from __future__ import annotations

import json
from typing import Any

from nullspace import GHOST_TAG, PLATFORM, SOLID_TAG
from nullspace.client import DataHubClient, now_ms
from nullspace.ghosts import Ghost


def emit_ghost(dh: DataHubClient, ghost: Ghost) -> None:
    """Upsert dataset properties + tags reflecting current ghost state."""
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

    # Prefer acryldata SDK emitter when installed
    try:
        _emit_via_sdk(ghost, description, custom, tag)
        return
    except Exception:
        pass

    _emit_via_rest(dh, ghost, description, custom, tag)


def _emit_via_sdk(
    ghost: Ghost,
    description: str,
    custom: dict[str, str],
    tag: str,
) -> None:
    from datahub.emitter.mce_builder import make_dataset_urn, make_tag_urn
    from datahub.emitter.mcp import MetadataChangeProposalWrapper
    from datahub.emitter.rest_emitter import DatahubRestEmitter
    from datahub.metadata.schema_classes import (
        DatasetPropertiesClass,
        GlobalTagsClass,
        TagAssociationClass,
    )

    from nullspace.config import settings

    cfg = settings()
    emitter = DatahubRestEmitter(gms_server=cfg.gms_url, token=cfg.token)
    urn = make_dataset_urn(PLATFORM, ghost.dataset_name, "PROD")

    props = DatasetPropertiesClass(
        name=ghost.dataset_name,
        description=description,
        customProperties=custom,
    )
    tags = GlobalTagsClass(tags=[TagAssociationClass(tag=make_tag_urn(tag))])

    for aspect in (props, tags):
        emitter.emit(
            MetadataChangeProposalWrapper(entityUrn=urn, aspect=aspect)
        )


def _emit_via_rest(
    dh: DataHubClient,
    ghost: Ghost,
    description: str,
    custom: dict[str, str],
    tag: str,
) -> None:
    """Raw MCP JSON — works on stock quickstart without SDK aspect codegen quirks."""
    ts = now_ms()
    dataset_props = {
        "entityType": "dataset",
        "entityUrn": ghost.urn,
        "changeType": "UPSERT",
        "aspectName": "datasetProperties",
        "aspect": {
            "contentType": "application/json",
            "value": json.dumps(
                {
                    "name": ghost.dataset_name,
                    "description": description,
                    "customProperties": custom,
                }
            ),
        },
        "systemMetadata": {"lastObserved": ts},
    }
    dh.emit_mcp(dataset_props)

    # Ensure tag entity exists, then associate
    tag_urn = f"urn:li:tag:{tag}"
    tag_prop = {
        "entityType": "tag",
        "entityUrn": tag_urn,
        "changeType": "UPSERT",
        "aspectName": "tagProperties",
        "aspect": {
            "contentType": "application/json",
            "value": json.dumps(
                {"name": tag, "description": f"Nullspace {tag} marker"}
            ),
        },
    }
    dh.emit_mcp(tag_prop)

    global_tags = {
        "entityType": "dataset",
        "entityUrn": ghost.urn,
        "changeType": "UPSERT",
        "aspectName": "globalTags",
        "aspect": {
            "contentType": "application/json",
            "value": json.dumps({"tags": [{"tag": tag_urn}]}),
        },
    }
    dh.emit_mcp(global_tags)


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
