"""Drive the Nullspace MCP server with three genuinely separate MCP clients.

Each client announces a different `clientInfo`, so the demand recorded in DataHub
comes from three independent identities negotiated over the protocol — not from a
for-loop over three strings. That distinction is the whole point of the lane.

    python scripts/mcp_smoke.py

LANE B (Claude).
"""

from __future__ import annotations

import asyncio
import json
import os
import sys

from mcp import ClientSession, Implementation, StdioServerParameters
from mcp.client.stdio import stdio_client

WANT = os.getenv("NULLSPACE_SMOKE_WANT", "weekly active teams by plan tier")
CLIENTS = [
    ("analytics-copilot", "1.0.0"),
    ("dbt-assistant", "0.4.2"),
    ("exec-dashboard-agent", "2.1.0"),
]


def _text(result) -> str:
    parts = []
    for block in result.content:
        parts.append(getattr(block, "text", ""))
    return "\n".join(p for p in parts if p)


async def call(client_name: str, version: str, tool: str, args: dict) -> str:
    params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "nullspace.mcp_server"],
        env={**os.environ},
    )
    async with stdio_client(params) as (read, write):
        async with ClientSession(
            read,
            write,
            client_info=Implementation(name=client_name, version=version),
        ) as session:
            await session.initialize()
            result = await session.call_tool(tool, args)
            return _text(result)


async def main() -> int:
    print(f"want: {WANT!r}\n")

    for name, version in CLIENTS:
        print(f"--- {name} v{version} asks for it ---")
        out = await call(name, version, "find_dataset", {"want": WANT})
        print(out)
        try:
            data = json.loads(out)
            who = data.get("agent_id")
            how = data.get("identified_by")
            print(f"    -> recorded as {who!r} via {how}")
        except json.JSONDecodeError:
            pass
        print()

    print("--- the shared demand board ---")
    print(await call("board-reader", "1.0.0", "open_demand", {}))
    print()

    print("--- builder agent claims it ---")
    print(await call("nullspace-builder", "1.0.0", "claim_and_build", {"want": WANT}))
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
