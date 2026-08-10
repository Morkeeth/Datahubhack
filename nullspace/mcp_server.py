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

from nullspace.agents.contracts import ContractStore, RegisteredQuery, infer_fields
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


def public_mode() -> bool:
    """True when this process is reachable by strangers.

    A judge pointing their own agent at us is the whole moonshot, and it means
    the endpoint is open. `claim_and_build` is the one tool that must never be
    open: it writes files into a dbt checkout, pushes a branch, and opens a pull
    request using whatever GitHub credentials the host is logged in with. A
    demand counter is a safe thing to hand a stranger; somebody else's `gh` auth
    is not.
    """
    return os.getenv("NULLSPACE_PUBLIC", "").lower() in {"1", "true", "yes"}


# Cheap per-identity ceiling. Not a security control — the security control is
# that the dangerous tool is off. This exists so one loop cannot fill the board
# with noise while a judge is looking at it.
_CALLS: dict[str, int] = {}
_CALL_CEILING = int(os.getenv("NULLSPACE_PUBLIC_CALL_CEILING", "40"))


def _within_ceiling(agent_id: str) -> tuple[bool, str]:
    if not public_mode():
        return True, ""
    _CALLS[agent_id] = _CALLS.get(agent_id, 0) + 1
    if _CALLS[agent_id] > _CALL_CEILING:
        return False, (
            f"{agent_id} has made {_CALLS[agent_id]} calls to this public demo "
            f"instance; the ceiling is {_CALL_CEILING}. Clone the repo and run "
            "your own — it is one `docker compose up`."
        )
    return True, ""


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
    ok, why = _within_ceiling(agent_id)
    if not ok:
        return {"status": "refused", "reason": why, "agent_id": agent_id, "identified_by": how}
    if len(want) > 120:
        return {
            "status": "refused",
            "reason": f"want is {len(want)} characters; the ceiling is 120. "
            "A ghost is a table somebody meant to query, not a paragraph.",
            "agent_id": agent_id,
            "identified_by": how,
        }
    # One client for search + write. A second DataHubClient here used to search on
    # `live` while emit_ghost buffered on `ns.dh` — and only flushed at atexit —
    # so long-lived MCP sessions returned miss_ghosted while the board stayed empty.
    ns = _ns()
    live = ns.dh

    try:
        receipt = consumer_search(ns, want=want, agent_id=agent_id, dh=live)
        receipt["identified_by"] = how
        receipt["datahub_reachable"] = live is not None
        if live is None:
            # Never let a degraded run look like a healthy one. This used to say the
            # miss had been "recorded locally" — which stopped being true when Lane A
            # made consumer_search refuse outright with GMS down (D24). A warning
            # that describes behaviour the code no longer has is worse than none: it
            # tells a reader demand was captured when nothing was.
            receipt["warning"] = (
                "DataHub GMS was not reachable, so nothing was recorded anywhere. "
                "Demand that the catalog never sees is not demand, and Nullspace "
                "refuses rather than keeping a private copy."
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
    finally:
        if ns.dh is not None:
            ns.dh.flush_ghost_emits()


@server.tool(
    description=(
        "The shared demand board: every asset agents have asked for that does not "
        "exist yet, with how many independent agents wanted it."
    )
)
def open_demand() -> dict[str, Any]:
    ns = _ns()
    # Catalog is SoT — hydrate before ranking so the builder walks DataHub, not a
    # stale file cache from a previous process.
    if ns.dh is not None:
        try:
            ns.hydrate(replace=False)
        except Exception:
            pass
        ns.dh.flush_ghost_emits()
    ghosts = [g.to_public() for g in ns.store.list_ghosts()]
    return {
        "threshold": ns.demand_threshold,
        "count": len(ghosts),
        "buildable": [g.want for g in ns.ready_to_build()],
        "ghosts": ghosts,
        "catalog": "live" if ns.dh is not None else "unreachable",
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
    if public_mode():
        # Stated, not silent — non-negotiable #3. A judge who calls this should
        # learn exactly why it declined and how to see it work for real.
        return {
            "status": "refused",
            "reason": (
                "this is a public demo instance and building is disabled on it: "
                "claiming a ghost writes a dbt model, pushes a branch and opens a "
                "real pull request with the host's GitHub credentials. Demand is "
                "open to everyone; spending someone else's write access is not. "
                "Run `docker compose up` on your own machine and the same call "
                "goes all the way through to a pull request."
            ),
            "builder_id": builder_id,
            "identified_by": how,
            "public_instance": True,
        }
    ns = _ns()
    if ns.dh is not None:
        try:
            ns.hydrate(replace=False)
        except Exception:
            pass

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


@server.tool(
    description=(
        "Register the query you meant to run against an asset that does not exist "
        "yet, and the columns it needs. You will be told when it runs. The columns "
        "real agents ask for become the schema the builder agent has to deliver."
    )
)
def register_query(
    want: str, sql: str, ctx: Context, needs_fields: list[str] | None = None
) -> dict[str, Any]:
    agent_id, how = _identify(ctx)
    ns = _ns()

    ghost = ns.store.get(want)
    if ghost is None:
        return {
            "status": "refused",
            "reason": (
                f"no ghost exists for {want!r} — call find_dataset first so the "
                "demand is recorded"
            ),
            "agent_id": agent_id,
            "identified_by": how,
        }

    if needs_fields:
        fields, how_fields = list(needs_fields), "declared by the agent"
    else:
        fields, how_fields = infer_fields(sql)

    store = ContractStore()
    store.register(
        RegisteredQuery(agent_id=agent_id, want=want, sql=sql, needs_fields=fields)
    )
    demanded = store.demanded_schema(want)
    return {
        "status": "registered",
        "agent_id": agent_id,
        "identified_by": how,
        "want": want,
        "urn": ghost.urn,
        "needs_fields": fields,
        "fields_determined_by": how_fields,
        "demanded_schema": demanded,
        "note": (
            "This is the union of columns every requesting agent asked for. It is "
            "the contract the builder agent has to satisfy."
        ),
        "queries_registered": len(store.queries(want)),
    }


@server.tool(
    description=(
        "Has my query started working? Compares every registered query against the "
        "schema DataHub actually returns for the asset, and names the missing "
        "columns for any that cannot run yet."
    )
)
def contract_status(want: str) -> dict[str, Any]:
    ns = _ns()
    store = ContractStore()
    ghost = ns.store.get(want)
    if ghost is None:
        return {
            "status": "unknown",
            "reason": f"no ghost for {want!r}",
            "demanded_schema": store.demanded_schema(want),
        }

    actual: list[str] = []
    live = _live()
    schema_source = "DataHub returned no schemaMetadata for this asset yet"
    if live is not None:
        aspect = live.get_aspect(ghost.urn, "schemaMetadata") or {}
        for f in aspect.get("fields", []) or []:
            path = f.get("fieldPath") if isinstance(f, dict) else None
            if path:
                actual.append(path)
        if actual:
            schema_source = "read back from DataHub schemaMetadata"

    settled = store.settle(want, actual)
    settled.update(
        {
            "urn": ghost.urn,
            "ghost_state": ghost.state,
            "demanded_schema": store.demanded_schema(want),
            "schema_source": schema_source,
        }
    )
    return settled


def main() -> None:
    """Serve over stdio by default, or over HTTP when asked.

    stdio is a pipe between two processes on one machine. It is enough to prove
    the requesters are independent agents rather than a for-loop, and it is what
    Claude Desktop and Cursor speak locally — but a judge cannot reach a pipe.
    `streamable-http` is the same server on a socket, so an agent on someone
    else's machine can miss, and their own miss becomes demand on a board they
    are watching. That is the difference between a video of our agents and a
    thing their agent did.
    """
    transport = os.getenv("NULLSPACE_MCP_TRANSPORT", "stdio")
    if transport == "stdio":
        server.run(transport="stdio")
        return
    host = os.getenv("NULLSPACE_MCP_HOST", "127.0.0.1")
    port = int(os.getenv("NULLSPACE_MCP_PORT", "8788"))

    # The SDK refuses a Host header it does not recognise — DNS-rebinding
    # protection, and it is right to. Behind a tunnel the browser-visible host
    # is the tunnel's, not ours, so it must be named explicitly. We name the
    # hosts we are actually served under; we do not turn the check off.
    from mcp.server.transport_security import TransportSecuritySettings

    extra = [h.strip() for h in os.getenv("NULLSPACE_ALLOWED_HOSTS", "").split(",") if h.strip()]
    allowed_hosts = [f"{host}:{port}", f"localhost:{port}", f"127.0.0.1:{port}", *extra]
    allowed_origins = [f"https://{h}" for h in extra] + [f"http://{h}" for h in allowed_hosts]
    security = TransportSecuritySettings(
        allowed_hosts=allowed_hosts, allowed_origins=allowed_origins
    )
    if extra:
        print(f"nullspace: also serving under {', '.join(extra)}", flush=True)
    server.run(transport=transport, host=host, port=port, transport_security=security)


if __name__ == "__main__":
    main()
