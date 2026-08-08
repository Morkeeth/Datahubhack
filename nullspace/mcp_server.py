"""Nullspace MCP server — the surface that makes the consumer agents real.

The demo in `nullspace/cli.py` loops over three hardcoded strings:

    for agent in ("consumer-a", "consumer-b", "consumer-c"):

That fakes the one claim the whole pitch rests on — that *independent* agents
discover they wanted the same thing. This server removes the loop. Any MCP client
(Claude Desktop, Cursor, an LLM with tools) connects, searches for an asset that
isn't there, and **its own miss** becomes demand under its own identity.

Identity is not a parameter the caller can spoof at will: it is taken from the
MCP `clientInfo` the client sent at initialize. Every receipt states which
mechanism produced the identity, so a reader can tell a real client apart from a
fallback. Nothing here is silent.

Run:
    DATAHUB_GMS_URL=http://localhost:8080 python -m nullspace.mcp_server

LANE B (Claude). Calls Lane A's API; never edits it.
"""

from __future__ import annotations

import os
from typing import Any

from mcp.server.mcpserver import Context, MCPServer

from nullspace.builder import build_and_solidify
from nullspace.client import DataHubClient
from nullspace.config import settings
from nullspace.ghosts import Nullspace, consumer_search
from nullspace.persist import FileGhostStore
from nullspace.urns import corpuser_urn

server = MCPServer(
    name="nullspace",
    instructions=(
        "Demand-side metadata for a data catalog. Use `find_dataset` whenever you "
        "need a dataset and do not know whether it exists. If it does not exist, "
        "your miss is recorded as demand rather than vanishing, and when enough "
        "independent agents have asked for the same thing a builder agent can "
        "claim it and make it real."
    ),
)


# --------------------------------------------------------------------------- id


def _identify(ctx: Context) -> tuple[str, str]:
    """Return (agent_id, how_we_know).

    Order: the MCP client's own declared identity, then an explicit env override,
    then an honest 'unidentified'. The second element is reported in every
    receipt so nobody has to guess which one fired.
    """
    # SDK 2.x exposes it as session.client_params.client_info; 1.x used clientInfo.
    for path in (
        "session.client_params.client_info",
        "session.client_params.clientInfo",
        "session.client_info",
    ):
        obj: Any = ctx
        try:
            for part in path.split("."):
                obj = getattr(obj, part)
                if obj is None:
                    raise AttributeError(part)
            name = getattr(obj, "name", None)
            version = getattr(obj, "version", None)
            if name:
                ident = f"{name}-{version}" if version else str(name)
                return ident, f"mcp clientInfo ({path})"
        except AttributeError:
            continue

    env = os.getenv("NULLSPACE_AGENT_ID")
    if env:
        return env, "NULLSPACE_AGENT_ID env var"

    return "unidentified-client", "no clientInfo and no env override"


def _ns() -> Nullspace:
    cfg = settings()
    dh = DataHubClient(cfg)
    return Nullspace(
        FileGhostStore(),
        demand_threshold=cfg.demand_threshold,
        dh=dh if dh.healthy() else None,
    )


def _live() -> DataHubClient | None:
    dh = DataHubClient()
    return dh if dh.healthy() else None


# ------------------------------------------------------------------------ tools


@server.tool(
    description=(
        "Find a dataset by what you need it to contain, in plain language. "
        "If it exists you get its URN. If it does not, your miss is recorded as "
        "demand under your own agent identity and you get a ghost receipt back."
    )
)
def find_dataset(want: str, ctx: Context) -> dict[str, Any]:
    agent_id, how = _identify(ctx)
    ns = _ns()
    live = _live()

    receipt = consumer_search(ns, want=want, agent_id=agent_id, dh=live)
    receipt["identified_by"] = how
    receipt["datahub_reachable"] = live is not None
    if live is None:
        # Never let a degraded run look like a healthy one.
        receipt["warning"] = (
            "DataHub GMS was not reachable; demand was recorded locally only and "
            "is NOT in the catalog."
        )

    if receipt["status"] == "miss_ghosted":
        ghost = receipt["ghost"]
        remaining = max(0, ns.demand_threshold - ghost["demand"])
        receipt["threshold"] = ns.demand_threshold
        receipt["agents_still_needed"] = remaining
        receipt["next"] = (
            "buildable now — call claim_and_build"
            if remaining == 0
            else f"{remaining} more independent agent(s) must ask before this can be built"
        )
    return receipt


@server.tool(
    description=(
        "The shared demand board: every asset agents have asked for that does not "
        "exist yet, with how many independent agents wanted it."
    )
)
def open_demand() -> dict[str, Any]:
    ns = _ns()
    ghosts = [g.to_public() for g in ns.store.list_ghosts()]
    return {
        "threshold": ns.demand_threshold,
        "count": len(ghosts),
        "buildable": [g.want for g in ns.ready_to_build()],
        "ghosts": ghosts,
    }


@server.tool(
    description=(
        "Builder agent: claim a ghost whose demand has crossed the threshold, "
        "write the model, and make it real. Refuses — with a stated reason — if "
        "demand is short or the asset is already solid."
    )
)
def claim_and_build(want: str, ctx: Context) -> dict[str, Any]:
    builder_id, how = _identify(ctx)
    ns = _ns()

    ghost = ns.store.get(want)
    if ghost is None:
        return {
            "status": "refused",
            "reason": f"no ghost exists for {want!r} — nobody has asked for it yet",
            "builder_id": builder_id,
            "identified_by": how,
        }
    if ghost.state == "solid":
        return {
            "status": "refused",
            "reason": f"{want!r} is already solid",
            "builder_id": builder_id,
            "identified_by": how,
            "urn": ghost.urn,
        }
    if ghost.demand < ns.demand_threshold:
        return {
            "status": "refused",
            "reason": (
                f"demand is {ghost.demand}, threshold is {ns.demand_threshold} — "
                f"{ns.demand_threshold - ghost.demand} more independent agent(s) "
                "must ask first"
            ),
            "builder_id": builder_id,
            "identified_by": how,
            "requesters": list(ghost.requesters),
        }

    built = build_and_solidify(ns, want, builder_id=builder_id)
    out = built.to_public()
    out["status"] = "solidified"
    out["builder_id"] = builder_id
    out["identified_by"] = how
    out["builder_urn"] = corpuser_urn(builder_id)
    return out


def main() -> None:
    server.run(transport="stdio")


if __name__ == "__main__":
    main()
