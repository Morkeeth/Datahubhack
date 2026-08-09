"""Nullspace demand as a stock DataHub ingestion source.

Run with the same CLI a maintainer already knows:

    datahub ingest -c infra/datahub/nullspace_demand.yml

The source turns unmet demand (postgres \"relation does not exist\" log lines,
or explicit sample events) into Dataset MCPs under platform ``nullspace`` —
searchable, ownable, lineage-ready ghosts. This is the connector behind
``docs/design/why-a-dataset-urn.md``: the RFC is not a paragraph, it is a recipe.

LANE A (Cursor). Calls Lane B's harvest parser for log lines; does not edit it.
"""

from __future__ import annotations

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
    DatasetPropertiesClass,
    GlobalTagsClass,
    StatusClass,
    TagAssociationClass,
    TagPropertiesClass,
)
from pydantic import Field

from nullspace import GHOST_TAG, PLATFORM
from nullspace.client import now_ms
from nullspace.urns import ghost_dataset_name, ghost_urn

_PLATFORM_URN = f"urn:li:dataPlatform:{PLATFORM}"


class DemandEvent(ConfigModel):
    want: str
    agent_id: str
    sql: str | None = None
    needs_fields: list[str] = Field(default_factory=list)
    detail: str = "ingestion source"


class NullspaceDemandSourceConfig(ConfigModel):
    """Inputs for demand ingestion."""

    postgres_log: str | None = Field(
        default=None,
        description="Path to a Postgres log file containing relation-does-not-exist errors.",
    )
    events: list[DemandEvent] = Field(
        default_factory=list,
        description="Explicit demand events (tests / demos without a log file).",
    )
    events_path: str | None = Field(
        default=None,
        description="JSONL file of {want, agent_id, sql?, needs_fields?} objects.",
    )


@platform_name("Nullspace Demand")
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
        return cls(NullspaceDemandSourceConfig.parse_obj(config_dict), ctx)

    def get_workunits_internal(self) -> Iterable[MetadataWorkUnit]:
        events = list(self._collect_events())
        if not events:
            self.report.report_warning(
                "nullspace-demand",
                "no demand events found (empty log / events / events_path)",
            )
            return

        # Aggregate: one ghost URN per want, demand = unique agents, contracts merged.
        by_want: dict[str, dict] = {}
        for event in events:
            want = event["want"].strip()
            key = want.lower()
            row = by_want.setdefault(
                key,
                {
                    "want": want,
                    "agents": [],
                    "contracts": [],
                    "resolution": [],
                },
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
                contracts = [
                    c for c in row["contracts"] if c.get("agent_id") != agent
                ]
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

        # Ensure the ghost tag exists once.
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

        for row in by_want.values():
            want = row["want"]
            urn = ghost_urn(want)
            name = ghost_dataset_name(want)
            custom = {
                "nullspace.demand": str(len(row["agents"])),
                "nullspace.want": want,
                "nullspace.state": "ghost",
                "nullspace.requesters": ",".join(row["agents"]),
                "nullspace.claimed_by": "",
                "nullspace.pr_url": "",
                "nullspace.schema_source": "nullspace.ingestion.demand",
                "nullspace.resolution": json.dumps(row["resolution"]),
                "nullspace.contracts": json.dumps(row["contracts"]),
            }
            props = DatasetPropertiesClass(
                name=name,
                description=f"Nullspace GHOST (ingestion source) for demand: {want}",
                customProperties=custom,
            )
            yield MetadataWorkUnit(
                id=f"nullspace-demand-{name}-status",
                mcp=MetadataChangeProposalWrapper(
                    entityUrn=urn, aspect=StatusClass(removed=False)
                ),
            )
            yield MetadataWorkUnit(
                id=f"nullspace-demand-{name}-props",
                mcp=MetadataChangeProposalWrapper(entityUrn=urn, aspect=props),
            )
            yield MetadataWorkUnit(
                id=f"nullspace-demand-{name}-tags",
                mcp=MetadataChangeProposalWrapper(
                    entityUrn=urn,
                    aspect=GlobalTagsClass(
                        tags=[TagAssociationClass(tag=tag_urn)]
                    ),
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
