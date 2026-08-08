"""Three agents write SQL against a table that does not exist, and get told when it runs.

This is the reveal. Run it against a live stack:

    python scripts/moonshot_demo.py

LANE B (Claude).
"""

from __future__ import annotations

import asyncio
import json
import os
import sys

from mcp import ClientSession, Implementation, StdioServerParameters
from mcp.client.stdio import stdio_client

WANT = os.getenv("NULLSPACE_DEMO_WANT", "monthly recurring revenue by segment")

# Three independent agents, three different real questions, three column sets.
AGENTS = [
    (
        "revenue-copilot",
        "1.0.0",
        "SELECT segment, mrr FROM {} WHERE month = '2026-08'",
        ["segment", "mrr", "month"],
    ),
    (
        "finance-agent",
        "2.3.1",
        "SELECT month, SUM(mrr) FROM {} GROUP BY month",
        ["month", "mrr"],
    ),
    (
        "board-deck-writer",
        "0.9.0",
        "SELECT segment, mrr, churned_mrr FROM {} ORDER BY mrr DESC",
        ["segment", "mrr", "churned_mrr"],
    ),
]


def _text(result) -> str:
    return "\n".join(getattr(b, "text", "") for b in result.content)


async def call(name: str, version: str, tool: str, args: dict) -> dict:
    params = StdioServerParameters(
        command=sys.executable, args=["-m", "nullspace.mcp_server"], env={**os.environ}
    )
    async with stdio_client(params) as (read, write):
        async with ClientSession(
            read, write, client_info=Implementation(name=name, version=version)
        ) as s:
            await s.initialize()
            raw = _text(await s.call_tool(tool, args))
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"_raw": raw}


def rule(title: str) -> None:
    print(f"\n{'=' * 66}\n{title}\n{'=' * 66}")


async def main() -> int:
    rule(f"1. Three agents need {WANT!r}. It does not exist.")
    for name, ver, sql, fields in AGENTS:
        miss = await call(name, ver, "find_dataset", {"want": WANT})
        print(f"\n  {name} v{ver}")
        print(f"    search  -> {miss.get('status')}  (demand now {miss.get('ghost', {}).get('demand')})")
        reg = await call(
            name, ver, "register_query",
            {"want": WANT, "sql": sql.format("<the table that does not exist>"),
             "needs_fields": fields},
        )
        print(f"    query   -> {reg.get('status')}, needs {reg.get('needs_fields')}")

    rule("2. The demanded schema — derived from what agents asked for, not guessed")
    st = await call("observer", "1.0.0", "contract_status", {"want": WANT})
    print(f"\n  demanded schema : {st.get('demanded_schema')}")
    print(f"  queries waiting : {len(st.get('queries', []))}")
    print(f"  schema source   : {st.get('schema_source')}")

    rule("3. Builder agent claims it and makes it real")
    built = await call("nullspace-builder", "1.0.0", "claim_and_build", {"want": WANT})
    print(f"\n  status : {built.get('status')}")
    print(f"  urn    : {built.get('urn')}")

    rule("4. Does my query run now?")
    st = await call("observer", "1.0.0", "contract_status", {"want": WANT})
    print(f"\n  schema source : {st.get('schema_source')}")
    print(f"  actual fields : {st.get('actual_fields')}")
    for q in st.get("queries", []):
        mark = "RUNS   " if q["status"] == "runs" else "BLOCKED"
        missing = f"  missing {q['missing_fields']}" if q["missing_fields"] else ""
        print(f"    {mark} {q['agent_id']}{missing}")
    print(f"\n  {st.get('runs')} running, {st.get('blocked')} blocked")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
