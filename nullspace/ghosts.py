"""Ghost lifecycle: miss → materialize/increment → claim → solidify.

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
        """Consumer searched and found nothing — materialize or increment ghost."""
        ghost = self.store.get(want)
        if ghost is None:
            name = ghost_dataset_name(want)
            ghost = Ghost(want=want, urn=ghost_urn(want), dataset_name=name)
        if agent_id not in ghost.requesters:
            ghost.requesters.append(agent_id)
            ghost.demand = len(ghost.requesters)
        ghost.resolution.append(
            ResolutionEvent(
                agent_id=agent_id, at_ms=now_ms(), event="miss", detail=detail
            )
        )
        ghost.state = "ghost" if ghost.state == "ghost" else ghost.state
        self.store.save(ghost)
        self._mirror(ghost)
        return ghost

    def claim(self, want: str, builder_id: str) -> Ghost:
        ghost = self.store.get(want)
        if ghost is None:
            raise ValueError(f"no ghost for want={want!r}")
        if ghost.demand < self.demand_threshold:
            raise ValueError(
                f"demand {ghost.demand} < threshold {self.demand_threshold}"
            )
        if ghost.state == "solid":
            raise ValueError("already solid")
        ghost.state = "claimed"
        ghost.claimed_by = builder_id
        ghost.resolution.append(
            ResolutionEvent(
                agent_id=builder_id, at_ms=now_ms(), event="claim", detail="builder"
            )
        )
        self.store.save(ghost)
        self._mirror(ghost)
        return ghost

    def attach_pr(self, want: str, pr_url: str) -> Ghost:
        ghost = self.store.get(want)
        if ghost is None:
            raise ValueError(f"no ghost for want={want!r}")
        ghost.pr_url = pr_url
        self.store.save(ghost)
        self._mirror(ghost)
        return ghost

    def solidify(self, want: str, *, schema_fields: list[str] | None = None) -> Ghost:
        ghost = self.store.get(want)
        if ghost is None:
            raise ValueError(f"no ghost for want={want!r}")
        ghost.state = "solid"
        ghost.resolution.append(
            ResolutionEvent(
                agent_id=ghost.claimed_by or "builder",
                at_ms=now_ms(),
                event="solidify",
                detail=json.dumps({"fields": schema_fields or []}),
            )
        )
        self.store.save(ghost)
        self._mirror(ghost)
        return ghost

    def ready_to_build(self) -> list[Ghost]:
        return [
            g
            for g in self.store.list_ghosts()
            if g.state == "ghost" and g.demand >= self.demand_threshold
        ]

    def _mirror(self, ghost: Ghost) -> None:
        """Best-effort write to live DataHub. Memory store demos never require this."""
        if self.dh is None:
            return
        try:
            from nullspace.emit import emit_ghost

            emit_ghost(self.dh, ghost)
        except Exception as exc:  # noqa: BLE001 — mirror must not break the loop
            ghost.resolution.append(
                ResolutionEvent(
                    agent_id="system",
                    at_ms=now_ms(),
                    event="mirror_error",
                    detail=str(exc)[:300],
                )
            )
            self.store.save(ghost)


def consumer_search(
    ns: Nullspace,
    *,
    want: str,
    agent_id: str,
    dh: DataHubClient | None = None,
) -> dict[str, Any]:
    """Search DataHub; on miss, open/increment a ghost. Returns a receipt."""
    hits: list[dict[str, Any]] = []
    if dh is not None:
        hits = dh.search_datasets(want)
        # Ignore our own ghosts when deciding "does the real asset exist?"
        hits = [h for h in hits if ":nullspace," not in h.get("urn", "")]
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
