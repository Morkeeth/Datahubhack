"""Read-only Nullspace board — the live URL judges hit.

**This board reads DataHub, not our own file store.**

It used to read `FileGhostStore`, and the red team killed it 3/3: *"the board
judges look at is a JSON file with a DataHub costume."* That is fatal to the one
law the whole pitch rests on. If the board survives DataHub being switched off,
then DataHub was never load-bearing and Nullspace is a wrapper with a badge.

So every field on this page is a read-back from the catalog: the ghosts come from
a search on platform `nullspace`, the demand and the resolution history come from
that dataset's `datasetProperties`, the fields come from `schemaMetadata`, the
requesters come from `ownership`, and the upstream comes from `lineage`. Kill GMS
and this endpoint reports the catalog as unreachable and shows nothing — which is
Law 2, demonstrated rather than asserted.

LANE B (Claude).
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import httpx
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse

from nullspace.config import settings

app = FastAPI(title="Nullspace Board", version="1.0.0")

# One query, everything the page renders. Kept here rather than in Lane A's client
# because the board's shape is a Lane B concern and Lane A must not have to care
# what the page shows.
_QUERY = """
query {
  search(input: {
    type: DATASET,
    query: "*",
    orFilters: [{ and: [{ field: "platform", values: ["urn:li:dataPlatform:nullspace"] }] }],
    start: 0, count: 100
  }) {
    searchResults {
      entity {
        urn
        ... on Dataset {
          name
          properties { customProperties { key value } }
          tags { tags { tag { urn } } }
          schemaMetadata { fields { fieldPath type nativeDataType } }
          ownership { owners { owner { ... on CorpUser { urn } } } }
          lineage: lineage(input: {direction: UPSTREAM, start: 0, count: 10}) {
            total
            relationships { entity { urn } }
          }
        }
      }
    }
  }
}
"""


def _props(entity: dict[str, Any]) -> dict[str, str]:
    raw = ((entity.get("properties") or {}).get("customProperties")) or []
    return {p["key"]: p["value"] for p in raw}


def _split(value: str) -> list[str]:
    return [part for part in (value or "").split(",") if part]


def _ghost_from_entity(entity: dict[str, Any]) -> dict[str, Any]:
    p = _props(entity)
    tags = [
        t["tag"]["urn"].split(":")[-1]
        for t in ((entity.get("tags") or {}).get("tags") or [])
    ]
    schema = (entity.get("schemaMetadata") or {}).get("fields") or []
    owners = (entity.get("ownership") or {}).get("owners") or []
    lineage = entity.get("lineage") or {}

    try:
        resolution = json.loads(p.get("nullspace.resolution") or "[]")
    except json.JSONDecodeError:
        resolution = []

    # Requesters: prefer native Owners, because that is the claim we make on the
    # solid asset. Fall back to the recorded property while a ghost is still
    # hollow and has no ownership aspect yet.
    owner_ids = [
        (o.get("owner") or {}).get("urn", "").split(":")[-1]
        for o in owners
        if (o.get("owner") or {}).get("urn")
    ]

    return {
        "want": p.get("nullspace.want") or entity.get("name") or entity["urn"],
        "urn": entity["urn"],
        "dataset_name": entity.get("name"),
        "demand": int(p.get("nullspace.demand") or 0),
        "state": p.get("nullspace.state") or ("solid" if "solid" in tags else "ghost"),
        "requesters": owner_ids or _split(p.get("nullspace.requesters", "")),
        "requesters_are_owners": bool(owner_ids),
        "claimed_by": p.get("nullspace.claimed_by") or None,
        "pr_url": p.get("nullspace.pr_url") or None,
        "schema_fields": [
            {"name": f.get("fieldPath"), "native_type": f.get("nativeDataType")}
            for f in schema
        ],
        "upstream_urns": [
            r["entity"]["urn"] for r in (lineage.get("relationships") or [])
        ],
        "upstream_total": lineage.get("total", 0),
        "schema_source": p.get("nullspace.schema_source") or None,
        "resolution": resolution,
        "tags": tags,
    }


def read_catalog() -> dict[str, Any]:
    """Ask DataHub what exists. Never invent a fallback."""
    cfg = settings()
    headers = {"Content-Type": "application/json"}
    if cfg.token:
        headers["Authorization"] = f"Bearer {cfg.token}"
    try:
        response = httpx.post(
            f"{cfg.gms_url}/api/graphql",
            headers=headers,
            json={"query": _QUERY},
            timeout=10.0,
        )
        response.raise_for_status()
        payload = response.json()
    except Exception as exc:  # noqa: BLE001 — any failure is the same story
        return {
            "product": "nullspace",
            "catalog": "unreachable",
            "source": cfg.gms_url,
            "reason": (
                "DataHub is not answering, so this board has nothing to show. "
                "It has no copy of its own: every ghost on it is a dataset in the "
                "catalog. Delete the catalog and the product is gone, which is the "
                "point."
            ),
            "detail": f"{type(exc).__name__}: {exc}",
            "ghosts": [],
            "counts": {"ghost": 0, "claimed": 0, "solid": 0},
        }

    if payload.get("errors"):
        return {
            "product": "nullspace",
            "catalog": "error",
            "source": cfg.gms_url,
            "reason": "DataHub answered with an error.",
            "detail": json.dumps(payload["errors"])[:400],
            "ghosts": [],
            "counts": {"ghost": 0, "claimed": 0, "solid": 0},
        }

    results = ((payload.get("data") or {}).get("search") or {}).get(
        "searchResults"
    ) or []
    ghosts = [_ghost_from_entity(r["entity"]) for r in results if r.get("entity")]
    ghosts.sort(key=lambda g: (g["state"] != "solid", -g["demand"], g["want"]))

    return {
        "product": "nullspace",
        "catalog": "live",
        "source": cfg.gms_url,
        "ghosts": ghosts,
        "counts": {
            "ghost": sum(1 for g in ghosts if g["state"] == "ghost"),
            "claimed": sum(1 for g in ghosts if g["state"] == "claimed"),
            "solid": sum(1 for g in ghosts if g["state"] == "solid"),
        },
        "public_instance": os.getenv("NULLSPACE_PUBLIC", "").lower()
        in {"1", "true", "yes"},
    }


@app.get("/api/board")
def api_board() -> JSONResponse:
    return JSONResponse(read_catalog())


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    return (Path(__file__).parent / "static" / "board.html").read_text(encoding="utf-8")
