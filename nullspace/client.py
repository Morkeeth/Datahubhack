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
        # Throughput: cache one-time aspects + last-written props; queue MCP batches.
        self._oneshot_urns: set[str] = set()
        self._props_cache: dict[str, dict[str, str]] = {}
        self._open_demand_cache: set[str] = set()
        self._mcp_queue: list[MetadataChangeProposalWrapper] = []
        self._batch_depth = 0
        self._ghost_buffer: list[MetadataChangeProposalWrapper] = []
        self._ghost_buffer_meta: list[tuple[str, dict[str, str]]] = []
        self._ghost_batch_size = int(
            __import__("os").getenv("NULLSPACE_GHOST_EMIT_BATCH", "40")
        )
        self._structured_props_ok: bool | None = None  # None=unknown, True/False cached
        import atexit

        atexit.register(self.flush_ghost_emits)

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

    def emit_aspect(
        self,
        urn: str,
        aspect: Any,
        *,
        emit_mode: Any | None = None,
    ) -> None:
        """Write one native aspect through the official SDK (or queue if batching)."""
        from datahub.emitter.rest_emitter import EmitMode

        mcp = MetadataChangeProposalWrapper(entityUrn=urn, aspect=aspect)
        if self._batch_depth > 0:
            self._mcp_queue.append(mcp)
            return
        mode = emit_mode if emit_mode is not None else EmitMode.SYNC_PRIMARY
        self.graph.emit(mcp, emit_mode=mode)

    def emit_mcps(
        self,
        mcps: list[Any],
        *,
        emit_mode: Any | None = None,
    ) -> None:
        """Batch-write native aspects — orders of magnitude faster than serial emit."""
        from datahub.emitter.rest_emitter import EmitMode

        if not mcps:
            return
        mode = emit_mode if emit_mode is not None else EmitMode.ASYNC
        self.graph.emit_mcps(mcps, emit_mode=mode)

    def queue_aspect(self, urn: str, aspect: Any) -> None:
        """Append an MCP to the current batch (or emit immediately if not batching)."""
        mcp = MetadataChangeProposalWrapper(entityUrn=urn, aspect=aspect)
        if self._batch_depth > 0:
            self._mcp_queue.append(mcp)
        else:
            self.emit_mcps([mcp])

    def begin_batch(self) -> None:
        self._batch_depth += 1

    def flush_batch(self, *, emit_mode: Any | None = None) -> int:
        """Emit all queued MCPs in one round-trip. Returns count flushed."""
        from datahub.emitter.rest_emitter import EmitMode

        pending = self._mcp_queue
        self._mcp_queue = []
        if not pending:
            return 0
        mode = emit_mode if emit_mode is not None else EmitMode.ASYNC
        self.graph.emit_mcps(pending, emit_mode=mode)
        return len(pending)

    def end_batch(self, *, emit_mode: Any | None = None) -> int:
        if self._batch_depth > 0:
            self._batch_depth -= 1
        if self._batch_depth == 0:
            return self.flush_batch(emit_mode=emit_mode)
        return 0

    def oneshot_done(self, urn: str) -> bool:
        return urn in self._oneshot_urns

    def mark_oneshot(self, urn: str) -> None:
        self._oneshot_urns.add(urn)

    def cached_properties(self, urn: str) -> dict[str, str] | None:
        return self._props_cache.get(urn)

    def remember_properties(self, urn: str, props: dict[str, str]) -> None:
        self._props_cache[urn] = dict(props)

    def mark_open_demand(self, want_key: str) -> None:
        self._open_demand_cache.add(want_key)

    def clear_open_demand(self, want_key: str) -> None:
        self._open_demand_cache.discard(want_key)

    def is_open_demand(self, want_key: str) -> bool:
        return want_key in self._open_demand_cache

    def buffer_ghost_emits(
        self, mcps: list[Any], *, urn: str, custom: dict[str, str]
    ) -> None:
        """Accumulate ghost MCPs across misses; flush every NULLSPACE_GHOST_EMIT_BATCH."""
        self._ghost_buffer.extend(mcps)
        self._ghost_buffer_meta.append((urn, dict(custom)))
        # Optimistic cache so the next miss on this URN skips GMS prior-read.
        self.remember_properties(urn, custom)
        if len(self._ghost_buffer_meta) >= self._ghost_batch_size:
            self.flush_ghost_emits()

    def flush_ghost_emits(self) -> int:
        """Emit all buffered ghost MCPs in one round-trip."""
        from datahub.emitter.rest_emitter import EmitMode

        if not self._ghost_buffer:
            return 0
        pending = self._ghost_buffer
        meta = self._ghost_buffer_meta
        self._ghost_buffer = []
        self._ghost_buffer_meta = []
        self.graph.emit_mcps(pending, emit_mode=EmitMode.SYNC_PRIMARY)
        for urn, custom in meta:
            self.remember_properties(urn, custom)
        return len(pending)

    def dataset_custom_properties(self, urn: str) -> dict[str, str]:
        for buffered_urn, custom in self._ghost_buffer_meta:
            if buffered_urn == urn:
                return dict(custom)
        cached = self._props_cache.get(urn)
        if cached is not None:
            return dict(cached)
        props = self.graph.get_aspect(urn, DatasetPropertiesClass)
        if props and props.customProperties:
            result = dict(props.customProperties)
            self._props_cache[urn] = result
            return result
        return {}

    def get_aspect(self, urn: str, aspect: str) -> dict[str, Any] | None:
        """Lane B compatibility: return a JSON-shaped native aspect read from GMS."""
        witness = self.solid_witness(urn)
        mapping: dict[str, Any] = {
            "schemaMetadata": witness["schemaMetadata"],
            "upstreamLineage": witness["lineage"],
            "ownership": witness["ownership"],
            "datasetProperties": witness["properties"],
            "globalTags": {"tags": witness["tags"]},
        }
        value = mapping.get(aspect)
        return value if isinstance(value, dict) else None

    def solid_witness(self, urn: str) -> dict[str, Any]:
        """Return exactly what GMS currently stores for the solid-asset claims."""
        from datahub.metadata.schema_classes import (
            AssertionInfoClass,
            InstitutionalMemoryClass,
            QueryPropertiesClass,
            StructuredPropertiesClass,
        )

        props = self.graph.get_aspect(urn, DatasetPropertiesClass)
        tags_aspect = self.graph.get_aspect(urn, GlobalTagsClass)
        schema = self.graph.get_aspect(urn, SchemaMetadataClass)
        lineage = self.graph.get_aspect(urn, UpstreamLineageClass)
        ownership = self.graph.get_aspect(urn, OwnershipClass)
        structured = self.graph.get_aspect(urn, StructuredPropertiesClass)
        memory = self.graph.get_aspect(urn, InstitutionalMemoryClass)

        custom = dict(props.customProperties or {}) if props else {}

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

        structured_props = []
        if structured is not None:
            structured_props = [
                {"propertyUrn": p.propertyUrn, "values": list(p.values)}
                for p in structured.properties
            ]

        links = []
        if memory is not None:
            links = [
                {"url": el.url, "description": el.description}
                for el in memory.elements
            ]

        assertion = None
        assertion_urn = custom.get("nullspace.assertion_urn") or ""
        if assertion_urn:
            info = self.graph.get_aspect(assertion_urn, AssertionInfoClass)
            if info is not None:
                schema_fields = []
                if info.schemaAssertion and info.schemaAssertion.schema:
                    schema_fields = [
                        f.fieldPath for f in info.schemaAssertion.schema.fields
                    ]
                assertion = {
                    "urn": assertion_urn,
                    "type": str(info.type),
                    "description": info.description,
                    "compatibility": (
                        str(info.schemaAssertion.compatibility)
                        if info.schemaAssertion
                        else None
                    ),
                    "fields": schema_fields,
                }

        queries: list[dict[str, Any]] = []
        raw_query_urns = custom.get("nullspace.query_urns") or ""
        for qurn in [u.strip() for u in raw_query_urns.split(",") if u.strip()]:
            qprops = self.graph.get_aspect(qurn, QueryPropertiesClass)
            if qprops is None:
                queries.append({"urn": qurn, "statement": None})
                continue
            statement = None
            if qprops.statement is not None:
                statement = qprops.statement.value
            queries.append(
                {
                    "urn": qurn,
                    "name": qprops.name,
                    "statement": statement,
                    "description": qprops.description,
                }
            )

        return {
            "urn": urn,
            "properties": custom if props else None,
            "tags": [
                tag.tag for tag in (tags_aspect.tags if tags_aspect is not None else [])
            ],
            "schemaMetadata": None if fields is None else {"fields": fields},
            "lineage": {"upstreams": upstreams, "count": len(upstreams)},
            "ownership": {"owners": owners, "count": len(owners)},
            "structuredProperties": structured_props,
            "institutionalMemory": links,
            "assertion": assertion,
            "queries": queries,
        }

    def wait_for_indexed_upstreams(
        self,
        urn: str,
        expected: set[str],
        *,
        timeout_seconds: float = 20.0,
    ) -> set[str]:
        """Wait for DataHub's lineage index—the UI's witness—to catch the aspect."""
        query = """
        query($urn: String!) {
          dataset(urn: $urn) {
            lineage(input: {
              direction: UPSTREAM,
              start: 0,
              count: 100,
              includeGhostEntities: true
            }) {
              relationships { entity { urn } }
            }
          }
        }
        """
        deadline = time.monotonic() + timeout_seconds
        returned: set[str] = set()
        while time.monotonic() < deadline:
            response = httpx.post(
                f"{self.gms}/api/graphql",
                headers=self._headers,
                json={"query": query, "variables": {"urn": urn}},
                timeout=10.0,
            )
            response.raise_for_status()
            dataset = ((response.json().get("data") or {}).get("dataset") or {})
            relationships = (
                (dataset.get("lineage") or {}).get("relationships") or []
            )
            returned = {
                relationship["entity"]["urn"]
                for relationship in relationships
                if relationship.get("entity", {}).get("urn")
            }
            if expected.issubset(returned):
                return returned
            time.sleep(0.5)
        return returned

    def wait_for_search_urn(
        self,
        query: str,
        urn: str,
        *,
        timeout_seconds: float = 15.0,
    ) -> bool:
        """Wait until DataHub's search index exposes a just-written ghost."""
        deadline = time.monotonic() + timeout_seconds
        while time.monotonic() < deadline:
            if any(hit["urn"] == urn for hit in self._graphql_search(query)):
                return True
            time.sleep(0.25)
        return False

    def find_source_covering_fields(
        self, required_fields: list[str]
    ) -> dict[str, Any] | None:
        """Find a real non-Nullspace dataset whose returned schema covers all fields."""
        query = """
        query {
          scrollAcrossEntities(input: {
            types: [DATASET],
            query: "*",
            count: 500
          }) {
            searchResults {
              entity {
                urn
                ... on Dataset {
                  platform { name }
                  schemaMetadata {
                    fields { fieldPath nativeDataType nullable }
                  }
                }
              }
            }
          }
        }
        """
        response = httpx.post(
            f"{self.gms}/api/graphql",
            headers=self._headers,
            json={"query": query},
            timeout=30.0,
        )
        response.raise_for_status()
        block = (
            (response.json().get("data") or {}).get("scrollAcrossEntities") or {}
        )
        required = {field.lower() for field in required_fields}
        candidates = []
        for result in block.get("searchResults") or []:
            entity = result.get("entity") or {}
            urn = entity.get("urn", "")
            if ":nullspace," in urn:
                continue
            fields = (entity.get("schemaMetadata") or {}).get("fields") or []
            by_name = {
                str(field["fieldPath"]).lower(): {
                    "name": field["fieldPath"],
                    "native_type": field.get("nativeDataType") or "VARCHAR",
                    "nullable": field.get("nullable", True),
                }
                for field in fields
            }
            if required.issubset(by_name):
                candidates.append(
                    {
                        "urn": urn,
                        "platform": (entity.get("platform") or {}).get("name"),
                        "fields": [by_name[field] for field in required_fields],
                        "extra_field_count": len(by_name) - len(required),
                    }
                )
        if not candidates:
            return None
        return min(candidates, key=lambda item: (item["extra_field_count"], item["urn"]))

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

    def list_nullspace_urns(self) -> list[str]:
        """Return every dataset URN on platform nullspace currently in search."""
        query = """
        query {
          search(input: {
            type: DATASET,
            query: "*",
            orFilters: [{
              and: [{ field: "platform", values: ["urn:li:dataPlatform:nullspace"] }]
            }],
            start: 0,
            count: 100
          }) {
            searchResults { entity { urn } }
          }
        }
        """
        response = httpx.post(
            f"{self.gms}/api/graphql",
            headers=self._headers,
            json={"query": query},
            timeout=30.0,
        )
        response.raise_for_status()
        results = (
            ((response.json().get("data") or {}).get("search") or {}).get(
                "searchResults"
            )
            or []
        )
        urns: list[str] = []
        for result in results:
            urn = (result.get("entity") or {}).get("urn")
            if urn:
                urns.append(urn)
        return urns

    def hard_delete_urn(self, urn: str) -> None:
        """Hard-delete one nullspace dataset. Refuses any other platform."""
        if "urn:li:dataPlatform:nullspace," not in urn:
            raise ValueError(
                "reset refused: refusing to delete non-nullspace URN "
                f"{urn!r}; only urn:li:dataPlatform:nullspace datasets may be wiped"
            )
        self.graph.delete_entity(urn, hard=True)

    def list_warehouse_datasets(self) -> list[dict[str, Any]]:
        """Return non-nullspace datasets with schema fields for the SQL planner."""
        query = """
        query {
          scrollAcrossEntities(input: {
            types: [DATASET],
            query: "*",
            count: 500
          }) {
            searchResults {
              entity {
                urn
                ... on Dataset {
                  platform { name }
                  schemaMetadata {
                    fields { fieldPath nativeDataType nullable }
                  }
                }
              }
            }
          }
        }
        """
        response = httpx.post(
            f"{self.gms}/api/graphql",
            headers=self._headers,
            json={"query": query},
            timeout=30.0,
        )
        response.raise_for_status()
        block = (
            (response.json().get("data") or {}).get("scrollAcrossEntities") or {}
        )
        out: list[dict[str, Any]] = []
        for result in block.get("searchResults") or []:
            entity = result.get("entity") or {}
            urn = entity.get("urn", "")
            if ":nullspace," in urn:
                continue
            fields = (entity.get("schemaMetadata") or {}).get("fields") or []
            out.append(
                {
                    "urn": urn,
                    "platform": (entity.get("platform") or {}).get("name"),
                    "fields": [
                        {
                            "name": field["fieldPath"],
                            "native_type": field.get("nativeDataType") or "VARCHAR",
                            "nullable": field.get("nullable", True),
                        }
                        for field in fields
                    ],
                }
            )
        return out

    def wait_for_nullspace_empty(self, *, timeout_seconds: float = 30.0) -> bool:
        deadline = time.monotonic() + timeout_seconds
        while time.monotonic() < deadline:
            if not self.list_nullspace_urns():
                return True
            time.sleep(0.5)
        return not self.list_nullspace_urns()


def now_ms() -> int:
    return int(time.time() * 1000)
