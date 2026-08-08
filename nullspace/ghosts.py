"""Ghost lifecycle: miss → demand → claim → solidify.

A ghost is a real DataHub dataset URN under platform `nullspace`, tagged `ghost`,
with custom properties:
  nullspace.demand       — int
  nullspace.want         — original demand phrase
  nullspace.state        — ghost | claimed | solid
  nullspace.requesters   — comma-separated agent ids
  nullspace.resolution   — JSON history (Scar Tissue steal: who asked / when / what failed)
  nullspace.pr_url       — set when builder opens a PR
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Protocol

from nullspace import DEMAND_THRESHOLD, GHOST_TAG, SOLID_TAG
from nullspace.client import DataHubClient, now_ms
from nullspace.urns import corpuser_urn, ghost_dataset_name, ghost_urn


@dataclass
class ResolutionEvent:
    agent_id: str
    at_ms: int
    event: str  # miss | claim | solidify
    detail: str = ""


@dataclass
class Ghost:
    want: str
    urn: str
    dataset_name: str
    demand: int = 0
    state: str = "ghost"  # ghost | claimed | solid
    requesters: list[str] = field(default_factory=list)
    resolution: list[ResolutionEvent] = field(default_factory=list)
    pr_url: str | None = None
    claimed_by: str | None = None
    schema_fields: list[dict[str, Any]] = field(default_factory=list)
    upstream_urns: list[str] = field(default_factory=list)

    def to_public(self) -> dict[str, Any]:
        return {
            "want": self.want,
            "urn": self.urn,
            "dataset_name": self.dataset_name,
            "demand": self.demand,
            "state": self.state,
            "requesters": list(self.requesters),
            "claimed_by": self.claimed_by,
            "pr_url": self.pr_url,
            "schema_fields": list(self.schema_fields),
            "upstream_urns": list(self.upstream_urns),
            "resolution": [
                {
                    "agent_id": e.agent_id,
                    "at_ms": e.at_ms,
                    "event": e.event,
                    "detail": e.detail,
                }
                for e in self.resolution
            ],
            "tags": [GHOST_TAG] if self.state != "solid" else [SOLID_TAG],
        }


class GhostStore(Protocol):
    def get(self, want: str) -> Ghost | None: ...
    def save(self, ghost: Ghost) -> None: ...
    def list_ghosts(self) -> list[Ghost]: ...


class MemoryGhostStore:
    """In-process store for unit tests and offline board rehearsal."""

    def __init__(self) -> None:
        self._by_want: dict[str, Ghost] = {}

    def get(self, want: str) -> Ghost | None:
        return self._by_want.get(_key(want))

    def save(self, ghost: Ghost) -> None:
        self._by_want[_key(ghost.want)] = ghost

    def list_ghosts(self) -> list[Ghost]:
        return list(self._by_want.values())


def _key(want: str) -> str:
    return want.strip().lower()


class Nullspace:
    def __init__(
        self,
        store: GhostStore,
        *,
        demand_threshold: int = DEMAND_THRESHOLD,
        dh: DataHubClient | None = None,
    ) -> None:
        self.store = store
        self.demand_threshold = demand_threshold
        self.dh = dh

    def on_miss(self, want: str, agent_id: str, *, detail: str = "search miss") -> Ghost:
        """A requester agent searched and found nothing — create or increment demand."""
        ghost = self.store.get(want)
        graph_ghost = self._from_datahub(want)
        if graph_ghost is not None and (
            ghost is None or graph_ghost.demand >= ghost.demand
        ):
            ghost = graph_ghost
        if ghost is None:
            ghost = Ghost(
                want=want,
                urn=ghost_urn(want),
                dataset_name=ghost_dataset_name(want),
            )
        if agent_id not in ghost.requesters:
            ghost.requesters.append(agent_id)
            ghost.demand = len(ghost.requesters)
        ghost.resolution.append(
            ResolutionEvent(
                agent_id=agent_id, at_ms=now_ms(), event="miss", detail=detail
            )
        )
        ghost.state = "ghost" if ghost.state == "ghost" else ghost.state
        self._mirror(ghost)
        self.store.save(ghost)
        return ghost

    def claim(self, want: str, builder_id: str) -> Ghost:
        ghost = self.store.get(want)
        if ghost is None:
            raise ValueError(f"no ghost for want={want!r}")
        if ghost.demand < self.demand_threshold:
            shortfall = self.demand_threshold - ghost.demand
            raise ValueError(
                "claim refused: "
                f"demand is {ghost.demand}, threshold is {self.demand_threshold}; "
                f"{shortfall} more requester agent"
                f"{'s' if shortfall != 1 else ''} must ask"
            )
        if ghost.state == "solid":
            raise ValueError("claim refused: ghost is already solid; shortfall is 0")
        ghost.state = "claimed"
        ghost.claimed_by = builder_id
        ghost.resolution.append(
            ResolutionEvent(
                agent_id=builder_id, at_ms=now_ms(), event="claim", detail="builder"
            )
        )
        self._mirror(ghost)
        self.store.save(ghost)
        return ghost

    def attach_pr(self, want: str, pr_url: str) -> Ghost:
        ghost = self.store.get(want)
        if ghost is None:
            raise ValueError(f"no ghost for want={want!r}")
        ghost.pr_url = pr_url
        self._mirror(ghost)
        self.store.save(ghost)
        return ghost

    def solidify(
        self,
        want: str,
        *,
        schema_fields: list[str | dict[str, Any]] | None = None,
        upstream_urns: list[str] | None = None,
    ) -> Ghost:
        ghost = self.store.get(want)
        if ghost is None:
            raise ValueError(f"solidify refused: no ghost exists for demand {want!r}")
        if ghost.state != "claimed":
            raise ValueError(
                f"solidify refused: state is {ghost.state!r}, not 'claimed'; "
                "a builder agent must claim the ghost first"
            )
        normalized_fields: list[dict[str, Any]] = []
        for field_spec in schema_fields or []:
            if isinstance(field_spec, str):
                normalized_fields.append(
                    {
                        "name": field_spec,
                        "native_type": (
                            "VARCHAR" if field_spec.endswith("_id") else "DOUBLE"
                        ),
                        "nullable": True,
                    }
                )
            else:
                normalized_fields.append(dict(field_spec))
        if not normalized_fields:
            raise ValueError(
                "solidify refused: schema has 0 fields; at least 1 real dbt field is required"
            )
        if not upstream_urns:
            from nullspace.config import settings

            upstream_urns = [settings().warehouse_source_urn]
        ghost.state = "solid"
        ghost.schema_fields = normalized_fields
        ghost.upstream_urns = list(dict.fromkeys(upstream_urns))
        ghost.resolution.append(
            ResolutionEvent(
                agent_id=ghost.claimed_by or "builder",
                at_ms=now_ms(),
                event="solidify",
                detail=json.dumps(
                    {
                        "fields": [field["name"] for field in normalized_fields],
                        "upstreams": ghost.upstream_urns,
                    }
                ),
            )
        )
        self._mirror(ghost)
        self.store.save(ghost)
        return ghost

    def ready_to_build(self) -> list[Ghost]:
        return [
            g
            for g in self.store.list_ghosts()
            if g.state == "ghost" and g.demand >= self.demand_threshold
        ]

    def _mirror(self, ghost: Ghost) -> dict[str, Any] | None:
        """Write to DataHub and verify by reading GMS back."""
        if self.dh is None:
            return None
        from nullspace.emit import emit_ghost

        witness = emit_ghost(self.dh, ghost)
        props = witness.get("properties") or {}
        if props.get("nullspace.state") != ghost.state:
            raise RuntimeError(
                "DataHub read-after-write failed: "
                f"state returned {props.get('nullspace.state')!r}, expected {ghost.state!r}"
            )
        if props.get("nullspace.demand") != str(ghost.demand):
            raise RuntimeError(
                "DataHub read-after-write failed: "
                f"demand returned {props.get('nullspace.demand')!r}, "
                f"expected {ghost.demand!r}"
            )
        return witness

    def _from_datahub(self, want: str) -> Ghost | None:
        """Hydrate deterministic ghost state so separate agent processes converge."""
        if self.dh is None:
            return None
        urn = ghost_urn(want)
        props = self.dh.dataset_custom_properties(urn)
        if not props or "nullspace.want" not in props:
            return None
        try:
            resolution = [
                ResolutionEvent(**event)
                for event in json.loads(props.get("nullspace.resolution", "[]"))
            ]
        except (TypeError, ValueError):
            resolution = []
        return Ghost(
            want=props.get("nullspace.want", want),
            urn=urn,
            dataset_name=ghost_dataset_name(want),
            demand=int(props.get("nullspace.demand", "0")),
            state=props.get("nullspace.state", "ghost"),
            requesters=[
                requester
                for requester in props.get("nullspace.requesters", "").split(",")
                if requester
            ],
            resolution=resolution,
            pr_url=props.get("nullspace.pr_url") or None,
            claimed_by=props.get("nullspace.claimed_by") or None,
        )


def consumer_search(
    ns: Nullspace,
    *,
    want: str,
    agent_id: str,
    dh: DataHubClient | None = None,
) -> dict[str, Any]:
    """Search DataHub; on miss, create or increment demand on one ghost."""
    hits: list[dict[str, Any]] = []
    if dh is not None:
        hits = dh.search_datasets(want)
        real_hits = []
        for hit in hits:
            urn = hit.get("urn", "")
            if ":nullspace," not in urn:
                real_hits.append(hit)
                continue
            props = dh.dataset_custom_properties(urn)
            if props.get("nullspace.state") == "solid":
                real_hits.append(hit)
        hits = real_hits
    if hits:
        return {
            "status": "found",
            "agent_id": agent_id,
            "want": want,
            "hits": [h["urn"] for h in hits],
            "agent_urn": corpuser_urn(agent_id),
        }
    ghost = ns.on_miss(want, agent_id, detail="no non-ghost dataset matched")
    return {
        "status": "miss_ghosted",
        "agent_id": agent_id,
        "want": want,
        "ghost": ghost.to_public(),
        "agent_urn": corpuser_urn(agent_id),
    }
