"""Thin DataHub REST emitter + GraphQL reader.

Uses the open REST `/entities?action=ingest` path via acryldata SDK when available,
falling back to raw HTTP so a stranger with only httpx can still run the demo.
"""

from __future__ import annotations

import json
import time
from typing import Any

import httpx

from nullspace.config import Settings, settings


class DataHubClient:
    def __init__(self, cfg: Settings | None = None) -> None:
        self.cfg = cfg or settings()
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

    def get_aspect(self, urn: str, aspect: str) -> dict[str, Any] | None:
        r = httpx.get(
            f"{self.gms}/aspects/{httpx.URL(urn).raw_path}",
            # use aspect get API
            params={"aspect": aspect, "version": 0},
            headers=self._headers,
            timeout=30.0,
        )
        # Prefer GraphQL entity fetch — more stable across versions
        return self._graphql_entity_properties(urn)

    def _graphql_entity_properties(self, urn: str) -> dict[str, Any] | None:
        gql = {
            "query": """
            query($urn: String!) {
              dataset(urn: $urn) {
                urn
                name
                properties { name description }
                tags { tags { tag { name urn } } }
                customProperties: properties { customProperties { key value } }
              }
            }
            """,
            "variables": {"urn": urn},
        }
        # Dataset properties shape varies; also try entityExists
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
            return None
        data = r.json()
        exists = (data.get("data") or {}).get("entityExists")
        if not exists:
            return None
        # Fetch via get with aspects
        r2 = httpx.get(
            f"{self.gms}/entities/{urn}",
            headers=self._headers,
            timeout=30.0,
        )
        if r2.status_code >= 400:
            return {"urn": urn, "exists": True}
        return r2.json()

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
