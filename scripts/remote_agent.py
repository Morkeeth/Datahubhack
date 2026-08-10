"""Ask a Nullspace instance over the network for a table that does not exist.

This is the file a judge runs. It clones nothing, starts no Docker, and needs no
DataHub of its own — it is an MCP client pointed at somebody else's Nullspace,
exactly like the agent on your laptop would be.

    python scripts/remote_agent.py --url https://<host>/mcp \
        --want "monthly recurring revenue by segment" \
        --agent your-name --query "SELECT segment, SUM(mrr) FROM {} GROUP BY segment"

Your identity comes from the MCP `clientInfo` handshake, not from a field you can
type, so the demand the board shows really is yours. Watch it land on the board.

LANE B (Claude). Calls Lane A's API through the MCP surface; never edits it.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys

from mcp import ClientSession, Implementation
from mcp.client.streamable_http import streamable_http_client


def _text(result) -> str:
    return "\n".join(getattr(b, "text", "") for b in result.content)


def _json(result) -> dict:
    raw = _text(result)
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"_raw": raw}


async def run(url: str, want: str, agent: str, version: str, query: str | None) -> int:
    async with streamable_http_client(url) as (read, write):
        async with ClientSession(
            read, write, client_info=Implementation(name=agent, version=version)
        ) as session:
            await session.initialize()

            tools = [t.name for t in (await session.list_tools()).tools]
            print(f"connected to {url}")
            print(f"tools: {', '.join(tools)}\n")

            miss = _json(await session.call_tool("find_dataset", {"want": want}))
            ghost = miss.get("ghost") or {}
            print(f"searched for {want!r}")
            print(f"  outcome  : {miss.get('status', miss.get('_raw'))}")
            print(f"  you are  : {ghost.get('requesters', ['?'])[-1]}")
            print(f"  identity : {miss.get('identified_by')}")
            print(f"  in DataHub: {miss.get('datahub_reachable')}")
            if miss.get("warning"):
                print(f"  WARNING  : {miss['warning']}")
            print(f"  demand   : {ghost.get('demand')}  ({miss.get('next', '')})")
            print(f"  urn      : {ghost.get('urn')}\n")

            if query:
                reg = _json(
                    await session.call_tool(
                        "register_query", {"want": want, "sql": query}
                    )
                )
                print("registered the query you meant to run")
                print(f"  status : {reg.get('status', reg.get('_raw'))}")
                needs = (
                    reg.get("needs_fields")
                    or reg.get("needs")
                    or reg.get("fields")
                    or reg.get("columns")
                )
                print(f"  needs  : {needs}\n")

            print("Now watch the board. When enough agents have asked, a builder")
            print("agent claims it, writes the model, and opens a real pull request.")
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--url", required=True, help="Nullspace MCP endpoint, e.g. https://host/mcp")
    p.add_argument("--want", required=True, help="the asset you wish existed, in plain English")
    p.add_argument("--agent", default="visiting-agent", help="your agent's name")
    p.add_argument("--version", default="1.0.0")
    p.add_argument("--query", default=None, help="the SQL you meant to run, {} for the table")
    a = p.parse_args()
    return asyncio.run(run(a.url, a.want, a.agent, a.version, a.query))


if __name__ == "__main__":
    sys.exit(main())
