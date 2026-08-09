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
import re
from collections.abc import Iterator
from contextlib import contextmanager
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
    schema_source: str | None = None

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
            "schema_source": self.schema_source,
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
    def transaction(self) -> Iterator[None]: ...
    def get(self, want: str) -> Ghost | None: ...
    def save(self, ghost: Ghost) -> None: ...
    def list_ghosts(self) -> list[Ghost]: ...
    def clear(self) -> None: ...


class MemoryGhostStore:
    """In-process store for unit tests and offline board rehearsal."""

    def __init__(self) -> None:
        self._by_want: dict[str, Ghost] = {}

    @contextmanager
    def transaction(self) -> Iterator[None]:
        yield

    def get(self, want: str) -> Ghost | None:
        return self._by_want.get(_key(want))

    def save(self, ghost: Ghost) -> None:
        self._by_want[_key(ghost.want)] = ghost

    def list_ghosts(self) -> list[Ghost]:
        return list(self._by_want.values())

    def clear(self) -> None:
        self._by_want.clear()


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
        with self.store.transaction():
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
        with self.store.transaction():
            ghost = self.store.get(want)
            if ghost is None:
                raise ValueError(f"claim refused: no ghost exists for demand {want!r}")
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
            if ghost.state == "claimed":
                if ghost.claimed_by == builder_id:
                    return ghost
                raise ValueError(
                    f"claim refused: ghost is already claimed by {ghost.claimed_by!r}; "
                    "0 additional claims are available"
                )
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

    def release_claim(
        self, want: str, *, builder_id: str, detail: str = "build failed"
    ) -> Ghost:
        """Return a claimed ghost to open demand so a failed build can be retried."""
        with self.store.transaction():
            ghost = self.store.get(want)
            if ghost is None:
                raise ValueError(
                    f"release_claim refused: no ghost exists for demand {want!r}"
                )
            if ghost.state != "claimed":
                raise ValueError(
                    f"release_claim refused: state is {ghost.state!r}, not 'claimed'"
                )
            if ghost.claimed_by and ghost.claimed_by != builder_id:
                raise ValueError(
                    "release_claim refused: "
                    f"claimed by {ghost.claimed_by!r}, not {builder_id!r}"
                )
            ghost.state = "ghost"
            ghost.claimed_by = None
            ghost.pr_url = None
            ghost.resolution.append(
                ResolutionEvent(
                    agent_id=builder_id,
                    at_ms=now_ms(),
                    event="release_claim",
                    detail=detail,
                )
            )
            self._mirror(ghost)
            self.store.save(ghost)
            return ghost

    def attach_pr(self, want: str, pr_url: str) -> Ghost:
        with self.store.transaction():
            ghost = self.store.get(want)
            if ghost is None:
                raise ValueError(
                    f"change-reference refused: no ghost exists for demand {want!r}"
                )
            ghost.pr_url = pr_url
            self._mirror(ghost)
            self.store.save(ghost)
            return ghost

    def record_resolution(
        self,
        want: str,
        *,
        agent_id: str,
        event: str,
        detail: str,
    ) -> Ghost:
        """Bind builder proof or refusal to the ghost and mirror it to DataHub."""
        with self.store.transaction():
            ghost = self.store.get(want)
            if ghost is None:
                raise ValueError(
                    f"resolution refused: no ghost exists for demand {want!r}"
                )
            ghost.resolution.append(
                ResolutionEvent(
                    agent_id=agent_id,
                    at_ms=now_ms(),
                    event=event,
                    detail=detail,
                )
            )
            self._mirror(ghost)
            self.store.save(ghost)
            return ghost

    def solidify(
        self,
        want: str,
        *,
        schema_fields: list[str | dict[str, Any]] | None = None,
        upstream_urns: list[str] | None = None,
        schema_source: str | None = None,
    ) -> Ghost:
        with self.store.transaction():
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
                    "solidify refused: schema has 0 fields; "
                    "at least 1 real dbt field is required"
                )
            if not upstream_urns:
                from nullspace.config import settings

                upstream_urns = [settings().warehouse_source_urn]
            ghost.state = "solid"
            ghost.schema_fields = normalized_fields
            ghost.upstream_urns = list(dict.fromkeys(upstream_urns))
            ghost.schema_source = schema_source or "builder supplied schema"
            ghost.resolution.append(
                ResolutionEvent(
                    agent_id=ghost.claimed_by or "builder",
                    at_ms=now_ms(),
                    event="solidify",
                    detail=json.dumps(
                        {
                            "fields": [field["name"] for field in normalized_fields],
                            "upstreams": ghost.upstream_urns,
                            "schema_source": ghost.schema_source,
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

    def reset(self) -> dict[str, Any]:
        """Wipe local ghosts and hard-delete every nullspace platform dataset."""
        deleted: list[str] = []
        with self.store.transaction():
            if self.dh is not None:
                for urn in self.dh.list_nullspace_urns():
                    self.dh.hard_delete_urn(urn)
                    deleted.append(urn)
                # Search index lags hard-delete; wait until platform search is hollow.
                if not self.dh.wait_for_nullspace_empty(timeout_seconds=30.0):
                    remaining = self.dh.list_nullspace_urns()
                    raise RuntimeError(
                        "nullspace reset refused: DataHub still returns "
                        f"{len(remaining)} nullspace asset(s) after hard-delete: "
                        f"{remaining[:5]}"
                    )
            self.store.clear()
        return {
            "status": "reset",
            "deleted": deleted,
            "deleted_count": len(deleted),
            "store_count": len(self.store.list_ghosts()),
            "datahub_nullspace_count": (
                0 if self.dh is None else len(self.dh.list_nullspace_urns())
            ),
        }

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
        schema_fields: list[dict[str, Any]] = []
        upstream_urns: list[str] = []
        state = props.get("nullspace.state", "ghost")
        if state == "solid":
            # Rehydrate native aspects so a later miss cannot mirror an empty
            # solid and wipe schema/lineage in DataHub (LENS 1 finding).
            witness = self.dh.solid_witness(urn)
            schema_fields = [
                {
                    "name": field["fieldPath"],
                    "native_type": field.get("nativeDataType") or "VARCHAR",
                    "nullable": field.get("nullable", True),
                }
                for field in (witness.get("schemaMetadata") or {}).get("fields", [])
            ]
            upstream_urns = [
                upstream["dataset"]
                for upstream in (witness.get("lineage") or {}).get("upstreams", [])
            ]
        return Ghost(
            want=props.get("nullspace.want", want),
            urn=urn,
            dataset_name=ghost_dataset_name(want),
            demand=int(props.get("nullspace.demand", "0")),
            state=state,
            requesters=[
                requester
                for requester in props.get("nullspace.requesters", "").split(",")
                if requester
            ],
            resolution=resolution,
            pr_url=props.get("nullspace.pr_url") or None,
            claimed_by=props.get("nullspace.claimed_by") or None,
            schema_fields=schema_fields,
            upstream_urns=upstream_urns,
            schema_source=props.get("nullspace.schema_source") or None,
        )


def _want_tokens(want: str) -> list[str]:
    return [token for token in re.split(r"[^a-z0-9]+", want.lower()) if len(token) >= 4]


def _catalog_hit_matches_want(want: str, urn: str) -> bool:
    """Reject fuzzy search noise: require meaningful want tokens in the URN/name."""
    tokens = _want_tokens(want)
    if not tokens:
        return True
    haystack = urn.lower()
    # Majority of significant tokens must appear (DataHub often returns loose hits).
    matched = sum(1 for token in tokens if token in haystack)
    need = max(1, (len(tokens) + 1) // 2)
    return matched >= need


def consumer_search(
    ns: Nullspace,
    *,
    want: str,
    agent_id: str,
    dh: DataHubClient | None = None,
    offline: bool = False,
) -> dict[str, Any]:
    """Search DataHub; on miss, create or increment demand on one ghost.

    ``dh=None`` without ``offline=True`` is a refusal (Law 2): callers that
    dropped the catalog because GMS was down must not silently ghost into a
    private JSON file. Pass ``offline=True`` only for unit tests that exercise
    the in-memory store without a catalog.
    """
    hits: list[dict[str, Any]] = []
    if dh is None:
        if not offline:
            return {
                "status": "refused",
                "agent_id": agent_id,
                "want": want,
                "reason": (
                    "DataHub GMS unreachable; there is no shared namespace in which "
                    "this demand can be named or seen by other agents. "
                    "shortfall is 1 healthy catalog"
                ),
                "agent_urn": corpuser_urn(agent_id),
            }
    else:
        if not dh.healthy():
            return {
                "status": "refused",
                "agent_id": agent_id,
                "want": want,
                "reason": (
                    "DataHub GMS unreachable; there is no shared namespace in which "
                    "this demand can be named or seen by other agents. "
                    "shortfall is 1 healthy catalog"
                ),
                "agent_urn": corpuser_urn(agent_id),
            }
        hits = dh.search_datasets(want)
        real_hits = []
        want_key = _key(want)
        for hit in hits:
            urn = hit.get("urn", "")
            if ":nullspace," not in urn:
                if _catalog_hit_matches_want(want, urn):
                    real_hits.append(hit)
                continue
            # DataHub search is fuzzy: other solid ghosts must not satisfy a
            # different demand phrase. Only the same want counts as found.
            props = dh.dataset_custom_properties(urn)
            if props.get("nullspace.state") != "solid":
                continue
            if _key(props.get("nullspace.want", "")) == want_key:
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
