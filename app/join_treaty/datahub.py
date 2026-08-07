"""Thin, typed wrapper over the DataHub SDK for the Join Treaty pipeline.

All reads and writes go through the real GMS. Nothing here mocks metadata; the
pipeline fails loudly if the graph is unreachable.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Dict, List, Optional

from datahub.emitter.mcp import MetadataChangeProposalWrapper
from datahub.ingestion.graph.client import DataHubGraph, DataHubGraphConfig
from datahub.metadata.schema_classes import (
    AuditStampClass,
    DatasetProfileClass,
    DatasetPropertiesClass,
    ERModelRelationshipKeyClass,
    ERModelRelationshipPropertiesClass,
    QueryLanguageClass,
    QueryPropertiesClass,
    QuerySourceClass,
    QueryStatementClass,
    QuerySubjectClass,
    QuerySubjectsClass,
    RelationshipFieldMappingClass,
    SchemaMetadataClass,
)
from datahub.specific.dataset import DatasetPatchBuilder

from .config import Settings

_ACTOR = "urn:li:corpuser:datahub"


def _now_ms() -> int:
    return int(time.time() * 1000)


def _audit() -> AuditStampClass:
    return AuditStampClass(time=_now_ms(), actor=_ACTOR)


@dataclass
class FieldProfile:
    field: str
    unique_count: Optional[int]
    null_count: Optional[int]
    unique_proportion: Optional[float]


@dataclass
class DatasetFacts:
    urn: str
    fields: Dict[str, str]  # field -> native type
    row_count: Optional[int]
    profiles: Dict[str, FieldProfile]


def er_relationship_urn(rel_id: str) -> str:
    return f"urn:li:erModelRelationship:{rel_id}"


class DataHubClient:
    def __init__(self, settings: Optional[Settings] = None) -> None:
        self.settings = settings or Settings()
        self.graph = DataHubGraph(
            DataHubGraphConfig(
                server=self.settings.gms_url,
                token=self.settings.gms_token,
            )
        )

    # ---- reads -----------------------------------------------------------
    def dataset_facts(self, urn: str) -> DatasetFacts:
        schema = self.graph.get_aspect(urn, SchemaMetadataClass)
        fields: Dict[str, str] = {}
        if schema:
            for f in schema.fields:
                fields[f.fieldPath] = f.nativeDataType or ""

        profiles: Dict[str, FieldProfile] = {}
        row_count: Optional[int] = None
        profile = self.graph.get_latest_timeseries_value(
            urn, DatasetProfileClass, filter_criteria_map={}
        )
        if profile:
            row_count = profile.rowCount
            for fp in profile.fieldProfiles or []:
                profiles[fp.fieldPath] = FieldProfile(
                    field=fp.fieldPath,
                    unique_count=fp.uniqueCount,
                    null_count=fp.nullCount,
                    unique_proportion=fp.uniqueProportion,
                )
        return DatasetFacts(
            urn=urn, fields=fields, row_count=row_count, profiles=profiles
        )

    def query_urns(self) -> List[str]:
        """Enumerate all Query entity URNs known to the graph."""
        try:
            return list(self.graph.get_urns_by_filter(entity_types=["query"]))
        except Exception:
            return self._query_urns_via_graphql()

    def _query_urns_via_graphql(self) -> List[str]:
        gql = """
        query listQueries($input: ScrollAcrossEntitiesInput!) {
          scrollAcrossEntities(input: $input) {
            nextScrollId
            searchResults { entity { urn } }
          }
        }
        """
        urns: List[str] = []
        scroll_id: Optional[str] = None
        while True:
            variables = {
                "input": {
                    "types": ["QUERY"],
                    "query": "*",
                    "count": 100,
                    "scrollId": scroll_id,
                }
            }
            res = self.graph.execute_graphql(gql, variables=variables)
            block = res["scrollAcrossEntities"]
            urns.extend(r["entity"]["urn"] for r in block["searchResults"])
            scroll_id = block.get("nextScrollId")
            if not scroll_id or not block["searchResults"]:
                break
        return urns

    def query_statement(self, query_urn: str) -> Optional[str]:
        props = self.graph.get_aspect(query_urn, QueryPropertiesClass)
        if props and props.statement:
            return props.statement.value
        return None

    def er_relationship(
        self, rel_id: str
    ) -> Optional[ERModelRelationshipPropertiesClass]:
        return self.graph.get_aspect(
            er_relationship_urn(rel_id), ERModelRelationshipPropertiesClass
        )

    def dataset_custom_properties(self, urn: str) -> Dict[str, str]:
        props = self.graph.get_aspect(urn, DatasetPropertiesClass)
        if props and props.customProperties:
            return dict(props.customProperties)
        return {}

    # ---- writes ----------------------------------------------------------
    def emit_query_entity(
        self,
        query_urn: str,
        statement: str,
        subject_urns: List[str],
        name: str,
    ) -> None:
        props = QueryPropertiesClass(
            statement=QueryStatementClass(
                value=statement, language=QueryLanguageClass.SQL
            ),
            source=QuerySourceClass.MANUAL,
            created=_audit(),
            lastModified=_audit(),
            name=name,
        )
        subjects = QuerySubjectsClass(
            subjects=[QuerySubjectClass(entity=u) for u in subject_urns]
        )
        for aspect in (props, subjects):
            self.graph.emit(
                MetadataChangeProposalWrapper(entityUrn=query_urn, aspect=aspect)
            )

    def emit_er_relationship(
        self,
        rel_id: str,
        name: str,
        source_urn: str,
        destination_urn: str,
        source_field: str,
        destination_field: str,
        cardinality: str,
        custom_properties: Dict[str, str],
    ) -> str:
        urn = er_relationship_urn(rel_id)
        key = ERModelRelationshipKeyClass(id=rel_id)
        props = ERModelRelationshipPropertiesClass(
            name=name,
            source=source_urn,
            destination=destination_urn,
            relationshipFieldMappings=[
                RelationshipFieldMappingClass(
                    sourceField=source_field, destinationField=destination_field
                )
            ],
            cardinality=cardinality,
            created=_audit(),
            lastModified=_audit(),
            customProperties=custom_properties,
        )
        for aspect in (key, props):
            self.graph.emit(
                MetadataChangeProposalWrapper(entityUrn=urn, aspect=aspect)
            )
        return urn

    def patch_dataset_receipt(self, urn: str, key: str, value: str) -> None:
        patch = DatasetPatchBuilder(urn).add_custom_property(key, value)
        for mcp in patch.build():
            self.graph.emit(mcp)
