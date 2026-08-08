"""DataHub writer and witness reader for Nullspace.

Writes use the official DataHub SDK. Every product claim is read back from GMS;
the return value from an emit call is never treated as proof.
"""

from __future__ import annotations

import json
import time
from typing import Any

import httpx
from datahub.emitter.mcp import MetadataChangeProposalWrapper
from datahub.ingestion.graph.client import DataHubGraph, DataHubGraphConfig
from datahub.metadata.schema_classes import (
    DatasetPropertiesClass,
    GlobalTagsClass,
    OwnershipClass,
    SchemaMetadataClass,
    UpstreamLineageClass,
)

from nullspace.config import Settings, settings


class DataHubClient:
    def __init__(self, cfg: Settings | None = None) -> None:
        self.cfg = cfg or settings()
        self._graph: DataHubGraph | None = None
        self._headers = {"Content-Type": "application/json"}
        if self.cfg.token:
            self._headers["Authorization"] = f"Bearer {self.cfg.token}"

    @property
    def gms(self) -> str:
        return self.cfg.gms_url.rstrip("/")

    def healthy(self) -> bool:
        try:
            r = httpx.get(f"{self.gms}/health", timeout=5.0)
            return r.status_code < 500
        except httpx.HTTPError:
            return False

    @property
    def graph(self) -> DataHubGraph:
        if self._graph is None:
            self._graph = DataHubGraph(
                DataHubGraphConfig(server=self.gms, token=self.cfg.token)
            )
        return self._graph

    def search_datasets(self, query: str) -> list[dict[str, Any]]:
        """Return search hits. Empty list = miss (the Nullspace trigger)."""
        payload = {
            "query": query,
            "entity": "dataset",
            "start": 0,
            "count": 10,
        }
        # DataHub open search API
        r = httpx.post(
            f"{self.gms}/entities?action=search",
            headers=self._headers,
            json=payload,
            timeout=30.0,
        )
        if r.status_code >= 400:
            # Fallback GraphQL searchAcrossEntities
            return self._graphql_search(query)
        body = r.json()
        value = body.get("value") or body
        entities = value.get("entities") or value.get("searchResults") or []
        out: list[dict[str, Any]] = []
        for e in entities:
            entity = e.get("entity") or e
            urn = entity.get("urn") or e.get("urn")
            if urn:
                out.append({"urn": urn, "raw": e})
        return out

    def _graphql_search(self, query: str) -> list[dict[str, Any]]:
        gql = {
            "query": """
            query($q: String!) {
              search(input: { type: DATASET, query: $q, start: 0, count: 10 }) {
                searchResults { entity { urn } }
              }
            }
            """,
            "variables": {"q": query},
        }
        r = httpx.post(
            f"{self.gms}/api/graphql",
            headers=self._headers,
            json=gql,
            timeout=30.0,
        )
        r.raise_for_status()
        data = r.json()
        results = (
            ((data.get("data") or {}).get("search") or {}).get("searchResults") or []
        )
        return [{"urn": x["entity"]["urn"], "raw": x} for x in results if x.get("entity")]

    def emit_mcp(self, proposal: dict[str, Any]) -> None:
        """Emit a MetadataChangeProposal via REST."""
        r = httpx.post(
            f"{self.gms}/aspects?action=ingestProposal",
            headers=self._headers,
            json={"proposal": proposal},
            timeout=30.0,
        )
        if r.status_code >= 400:
            # Older quickstart path
            r2 = httpx.post(
                f"{self.gms}/entities?action=ingest",
                headers=self._headers,
                content=json.dumps(proposal),
                timeout=30.0,
            )
            r2.raise_for_status()
            return
        r.raise_for_status()

    def emit_aspect(self, urn: str, aspect: Any) -> None:
        """Write one native aspect through the official SDK."""
        self.graph.emit(MetadataChangeProposalWrapper(entityUrn=urn, aspect=aspect))

    def dataset_custom_properties(self, urn: str) -> dict[str, str]:
        props = self.graph.get_aspect(urn, DatasetPropertiesClass)
        if props and props.customProperties:
            return dict(props.customProperties)
        return {}

    def solid_witness(self, urn: str) -> dict[str, Any]:
        """Return exactly what GMS currently stores for the solid-asset claims."""
        props = self.graph.get_aspect(urn, DatasetPropertiesClass)
        tags_aspect = self.graph.get_aspect(urn, GlobalTagsClass)
        schema = self.graph.get_aspect(urn, SchemaMetadataClass)
        lineage = self.graph.get_aspect(urn, UpstreamLineageClass)
        ownership = self.graph.get_aspect(urn, OwnershipClass)

        fields = None
        if schema is not None:
            fields = [
                {
                    "fieldPath": field.fieldPath,
                    "nativeDataType": field.nativeDataType,
                    "nullable": field.nullable,
                }
                for field in schema.fields
            ]

        upstreams = []
        if lineage is not None:
            upstreams = [
                {"dataset": upstream.dataset, "type": str(upstream.type)}
                for upstream in lineage.upstreams
            ]

        owners = []
        if ownership is not None:
            owners = [
                {
                    "owner": owner.owner,
                    "type": str(owner.type),
                    "typeUrn": owner.typeUrn,
                }
                for owner in ownership.owners
            ]

        return {
            "urn": urn,
            "properties": dict(props.customProperties or {}) if props else None,
            "tags": [
                tag.tag for tag in (tags_aspect.tags if tags_aspect is not None else [])
            ],
            "schemaMetadata": None if fields is None else {"fields": fields},
            "lineage": {"upstreams": upstreams, "count": len(upstreams)},
            "ownership": {"owners": owners, "count": len(owners)},
        }

    def entity_exists(self, urn: str) -> bool:
        r = httpx.post(
            f"{self.gms}/api/graphql",
            headers=self._headers,
            json={
                "query": "query($urn: String!) { entityExists(urn: $urn) }",
                "variables": {"urn": urn},
            },
            timeout=30.0,
        )
        if r.status_code >= 400:
            return False
        return bool((r.json().get("data") or {}).get("entityExists"))


def now_ms() -> int:
    return int(time.time() * 1000)
