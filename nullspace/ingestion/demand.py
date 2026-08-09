"""Nullspace demand as a stock DataHub ingestion source.

Run with the same CLI a maintainer already knows:

    datahub ingest -c infra/datahub/nullspace_demand.yml

Emits Dataset MCPs under platform ``nullspace`` with:
  - datasetProperties (dual-write for board compatibility)
  - structuredProperties (nullspace.demand / state / want)
  - ownership (requesters as nullspace_requester from the first miss)
  - globalTags (ghost, or solid when soft-merging an existing solid URN)
  - Query entities for registered SQL contracts

When the recipe has a DataHub graph and the URN is already ``claimed`` /
``solid``, lifecycle fields (state, PR, plan, receipt, assertion, resolution)
are preserved — re-ingest grows demand without clobbering fulfillment.

LANE A (Cursor). Calls Lane B's harvest parser for log lines; does not edit it.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Iterable, Iterator

from datahub.configuration.common import ConfigModel
from datahub.emitter.mcp import MetadataChangeProposalWrapper
from datahub.ingestion.api.common import PipelineContext
from datahub.ingestion.api.decorators import (
    SupportStatus,
    config_class,
    platform_name,
    support_status,
)
from datahub.ingestion.api.source import Source, SourceReport
from datahub.ingestion.api.workunit import MetadataWorkUnit
from datahub.metadata.schema_classes import (
    AuditStampClass,
    CorpUserInfoClass,
    DatasetPropertiesClass,
    GlobalTagsClass,
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
    StatusClass,
    StructuredPropertiesClass,
    StructuredPropertyDefinitionClass,
    StructuredPropertyValueAssignmentClass,
    TagAssociationClass,
    TagPropertiesClass,
)
from pydantic import Field

from nullspace import GHOST_TAG, SOLID_TAG
from nullspace.client import now_ms
from nullspace.urns import corpuser_urn, ghost_dataset_name, ghost_urn

_ACTOR = "urn:li:corpuser:datahub"
_REQUESTER_TYPE_URN = "urn:li:ownershipType:nullspace_requester"
_SP_DEMAND = "urn:li:structuredProperty:nullspace.demand"
_SP_STATE = "urn:li:structuredProperty:nullspace.state"
_SP_WANT = "urn:li:structuredProperty:nullspace.want"

_LIFECYCLE_KEYS = (
    "nullspace.state",
    "nullspace.claimed_by",
    "nullspace.pr_url",
    "nullspace.builder_plan",
    "nullspace.builder_receipt",
    "nullspace.assertion_urn",
    "nullspace.schema_source",
    "nullspace.resolution",
)


def merge_demand_custom(
    incoming: dict[str, str], prior: dict[str, str]
) -> dict[str, str]:
    """Upsert demand/contracts without clobbering claimed/solid lifecycle."""
    out = dict(incoming)
    prior_state = (prior.get("nullspace.state") or "").strip()
    if prior_state not in {"claimed", "solid"}:
        return out
    out["nullspace.state"] = prior_state
    for key in _LIFECYCLE_KEYS:
        if key == "nullspace.state":
            continue
        if key in prior:
            out[key] = prior[key]
    # Union requesters so re-ingest can grow demand without dropping owners.
    prior_agents = [
        a.strip()
        for a in (prior.get("nullspace.requesters") or "").split(",")
        if a.strip()
    ]
    incoming_agents = [
        a.strip()
        for a in (incoming.get("nullspace.requesters") or "").split(",")
        if a.strip()
    ]
    agents = list(dict.fromkeys([*prior_agents, *incoming_agents]))
    out["nullspace.requesters"] = ",".join(agents)
    out["nullspace.demand"] = str(len(agents))
    return out


def read_prior_custom(ctx: PipelineContext, urn: str) -> dict[str, str]:
    """Best-effort read of existing datasetProperties when the recipe has a graph."""
    graph = getattr(ctx, "graph", None)
    if graph is None:
        return {}
    try:
        props = graph.get_aspect(urn, DatasetPropertiesClass)
    except Exception:  # noqa: BLE001
        return {}
    if props is None or not props.customProperties:
        return {}
    return dict(props.customProperties)


class DemandEvent(ConfigModel):
    want: str
    agent_id: str
    sql: str | None = None
    needs_fields: list[str] = Field(default_factory=list)
    detail: str = "ingestion source"


class NullspaceDemandSourceConfig(ConfigModel):
    postgres_log: str | None = Field(
        default=None,
        description="Path to a Postgres log file containing relation-does-not-exist errors.",
    )
    events: list[DemandEvent] = Field(default_factory=list)
    events_path: str | None = Field(
        default=None,
        description="JSONL file of {want, agent_id, sql?, needs_fields?} objects.",
    )


def _audit() -> AuditStampClass:
    return AuditStampClass(time=now_ms(), actor=_ACTOR)


def _query_urn(agent_id: str, want: str, sql: str) -> str:
    digest = hashlib.sha1(
        f"{agent_id}|{want.strip().lower()}|{sql}".encode()
    ).hexdigest()[:20]
    return f"urn:li:query:nullspace_{digest}"


@platform_name("Nullspace Demand", id="nullspace-demand")
@support_status(SupportStatus.INCUBATING)
@config_class(NullspaceDemandSourceConfig)
class NullspaceDemandSource(Source):
    """Emit unmet demand as nullspace Dataset entities via the ingestion framework."""

    def __init__(self, config: NullspaceDemandSourceConfig, ctx: PipelineContext):
        super().__init__(ctx)
        self.config = config
        self.report = SourceReport()

    @classmethod
    def create(cls, config_dict: dict, ctx: PipelineContext) -> "NullspaceDemandSource":
        return cls(NullspaceDemandSourceConfig.model_validate(config_dict), ctx)

    def get_workunits_internal(self) -> Iterable[MetadataWorkUnit]:
        events = list(self._collect_events())
        if not events:
            self.report.report_warning(
                "nullspace-demand",
                "no demand events found (empty log / events / events_path)",
            )
            return

        by_want: dict[str, dict] = {}
        for event in events:
            want = event["want"].strip()
            key = want.lower()
            row = by_want.setdefault(
                key,
                {"want": want, "agents": [], "contracts": [], "resolution": []},
            )
            agent = event["agent_id"]
            if agent not in row["agents"]:
                row["agents"].append(agent)
                row["resolution"].append(
                    {
                        "agent_id": agent,
                        "at_ms": now_ms(),
                        "event": "miss",
                        "detail": event.get("detail") or "ingestion source",
                    }
                )
            if event.get("sql") or event.get("needs_fields"):
                contracts = [c for c in row["contracts"] if c.get("agent_id") != agent]
                contracts.append(
                    {
                        "agent_id": agent,
                        "want": want,
                        "sql": event.get("sql") or "",
                        "needs_fields": list(event.get("needs_fields") or []),
                        "at_ms": now_ms(),
                    }
                )
                row["contracts"] = contracts

        audit = _audit()
        # Structured property definitions (once).
        for urn, qname, vtype, display in (
            (_SP_DEMAND, "nullspace.demand", "urn:li:dataType:datahub.number", "Nullspace demand"),
            (_SP_STATE, "nullspace.state", "urn:li:dataType:datahub.string", "Nullspace state"),
            (_SP_WANT, "nullspace.want", "urn:li:dataType:datahub.string", "Nullspace want"),
        ):
            yield MetadataWorkUnit(
                id=f"sp-def-{qname}",
                mcp=MetadataChangeProposalWrapper(
                    entityUrn=urn,
                    aspect=StructuredPropertyDefinitionClass(
                        qualifiedName=qname,
                        displayName=display,
                        valueType=vtype,
                        entityTypes=["urn:li:entityType:datahub.dataset"],
                        cardinality="SINGLE",
                        description=display,
                        immutable=False,
                        created=audit,
                        lastModified=audit,
                    ),
                ),
            )

        tag_urn = f"urn:li:tag:{GHOST_TAG}"
        yield MetadataWorkUnit(
            id=f"tag-{GHOST_TAG}",
            mcp=MetadataChangeProposalWrapper(
                entityUrn=tag_urn,
                aspect=TagPropertiesClass(
                    name=GHOST_TAG,
                    description="Nullspace ghost — demand for data that does not exist yet",
                ),
            ),
        )
        yield MetadataWorkUnit(
            id="ownership-type-nullspace-requester-key",
            mcp=MetadataChangeProposalWrapper(
                entityUrn=_REQUESTER_TYPE_URN,
                aspect=OwnershipTypeKeyClass(id="nullspace_requester"),
            ),
        )
        yield MetadataWorkUnit(
            id="ownership-type-nullspace-requester-info",
            mcp=MetadataChangeProposalWrapper(
                entityUrn=_REQUESTER_TYPE_URN,
                aspect=OwnershipTypeInfoClass(
                    name="Nullspace requester",
                    description="AI agent whose catalog miss created demand",
                    created=audit,
                    lastModified=audit,
                ),
            ),
        )

        for row in by_want.values():
            want = row["want"]
            urn = ghost_urn(want)
            name = ghost_dataset_name(want)
            query_urns: list[str] = []
            for contract in row["contracts"]:
                qurn = _query_urn(
                    contract["agent_id"], want, contract.get("sql") or ""
                )
                query_urns.append(qurn)
                yield MetadataWorkUnit(
                    id=f"query-props-{qurn}",
                    mcp=MetadataChangeProposalWrapper(
                        entityUrn=qurn,
                        aspect=QueryPropertiesClass(
                            statement=QueryStatementClass(
                                value=contract.get("sql")
                                or f"-- fields: {contract.get('needs_fields')}",
                                language=QueryLanguageClass.SQL,
                            ),
                            source=QuerySourceClass.MANUAL,
                            created=audit,
                            lastModified=audit,
                            name=f"nullspace:{contract['agent_id']}",
                            description=json.dumps(
                                {
                                    "want": want,
                                    "agent_id": contract["agent_id"],
                                    "needs_fields": contract.get("needs_fields") or [],
                                },
                                sort_keys=True,
                            ),
                        ),
                    ),
                )
                yield MetadataWorkUnit(
                    id=f"query-subjects-{qurn}",
                    mcp=MetadataChangeProposalWrapper(
                        entityUrn=qurn,
                        aspect=QuerySubjectsClass(
                            subjects=[QuerySubjectClass(entity=urn)]
                        ),
                    ),
                )

            custom = merge_demand_custom(
                {
                    "nullspace.demand": str(len(row["agents"])),
                    "nullspace.want": want,
                    "nullspace.state": "ghost",
                    "nullspace.requesters": ",".join(row["agents"]),
                    "nullspace.claimed_by": "",
                    "nullspace.pr_url": "",
                    "nullspace.schema_source": "nullspace.ingestion.demand",
                    "nullspace.resolution": json.dumps(row["resolution"]),
                    "nullspace.contracts": json.dumps(row["contracts"]),
                    "nullspace.query_urns": ",".join(query_urns),
                },
                read_prior_custom(self.ctx, urn),
            )
            state = custom.get("nullspace.state") or "ghost"
            tag_name = SOLID_TAG if state == "solid" else GHOST_TAG
            entity_tag_urn = f"urn:li:tag:{tag_name}"
            if tag_name == SOLID_TAG:
                yield MetadataWorkUnit(
                    id=f"tag-{SOLID_TAG}",
                    mcp=MetadataChangeProposalWrapper(
                        entityUrn=entity_tag_urn,
                        aspect=TagPropertiesClass(
                            name=SOLID_TAG,
                            description="Nullspace solid — demand fulfilled",
                        ),
                    ),
                )
            label = state.upper()
            yield MetadataWorkUnit(
                id=f"nullspace-demand-{name}-status",
                mcp=MetadataChangeProposalWrapper(
                    entityUrn=urn, aspect=StatusClass(removed=False)
                ),
            )
            yield MetadataWorkUnit(
                id=f"nullspace-demand-{name}-props",
                mcp=MetadataChangeProposalWrapper(
                    entityUrn=urn,
                    aspect=DatasetPropertiesClass(
                        name=name,
                        description=(
                            f"Nullspace {label} (ingestion source) for demand: {want}"
                        ),
                        customProperties=custom,
                    ),
                ),
            )
            yield MetadataWorkUnit(
                id=f"nullspace-demand-{name}-sp",
                mcp=MetadataChangeProposalWrapper(
                    entityUrn=urn,
                    aspect=StructuredPropertiesClass(
                        properties=[
                            StructuredPropertyValueAssignmentClass(
                                propertyUrn=_SP_DEMAND,
                                values=[float(custom["nullspace.demand"])],
                                created=audit,
                                lastModified=audit,
                            ),
                            StructuredPropertyValueAssignmentClass(
                                propertyUrn=_SP_STATE,
                                values=[state],
                                created=audit,
                                lastModified=audit,
                            ),
                            StructuredPropertyValueAssignmentClass(
                                propertyUrn=_SP_WANT,
                                values=[want],
                                created=audit,
                                lastModified=audit,
                            ),
                        ]
                    ),
                ),
            )
            yield MetadataWorkUnit(
                id=f"nullspace-demand-{name}-tags",
                mcp=MetadataChangeProposalWrapper(
                    entityUrn=urn,
                    aspect=GlobalTagsClass(
                        tags=[TagAssociationClass(tag=entity_tag_urn)]
                    ),
                ),
            )
            owners = []
            for agent in row["agents"]:
                owner_urn = corpuser_urn(agent)
                yield MetadataWorkUnit(
                    id=f"corpuser-{agent}",
                    mcp=MetadataChangeProposalWrapper(
                        entityUrn=owner_urn,
                        aspect=CorpUserInfoClass(
                            active=True,
                            displayName=agent,
                            title="AI requester agent",
                            system=True,
                            customProperties={
                                "nullspace.role": "requester",
                                "nullspace.asset": urn,
                            },
                        ),
                    ),
                )
                owners.append(
                    OwnerClass(
                        owner=owner_urn,
                        type=OwnershipTypeClass.CUSTOM,
                        typeUrn=_REQUESTER_TYPE_URN,
                    )
                )
            yield MetadataWorkUnit(
                id=f"nullspace-demand-{name}-ownership",
                mcp=MetadataChangeProposalWrapper(
                    entityUrn=urn,
                    aspect=OwnershipClass(owners=owners, lastModified=audit),
                ),
            )

    def get_report(self) -> SourceReport:
        return self.report

    def _collect_events(self) -> Iterator[dict]:
        for event in self.config.events:
            yield {
                "want": event.want,
                "agent_id": event.agent_id,
                "sql": event.sql,
                "needs_fields": list(event.needs_fields),
                "detail": event.detail,
            }
        if self.config.events_path:
            path = Path(self.config.events_path)
            if path.exists():
                for line in path.read_text(encoding="utf-8").splitlines():
                    line = line.strip()
                    if not line:
                        continue
                    raw = json.loads(line)
                    yield {
                        "want": raw["want"],
                        "agent_id": raw["agent_id"],
                        "sql": raw.get("sql"),
                        "needs_fields": list(raw.get("needs_fields") or []),
                        "detail": raw.get("detail") or "events_path",
                    }
        if self.config.postgres_log:
            from nullspace.agents.harvest import parse

            path = Path(self.config.postgres_log)
            lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
            for miss in parse(lines):
                fields: list[str] = []
                if miss.sql:
                    from nullspace.agents.contracts import infer_fields

                    fields, _ = infer_fields(miss.sql)
                yield {
                    "want": miss.want,
                    "agent_id": miss.agent_id,
                    "sql": miss.sql,
                    "needs_fields": fields,
                    "detail": f"postgres-log:{miss.relation}",
                }
