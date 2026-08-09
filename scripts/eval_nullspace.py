"""Nullspace acceptance eval — DataHub is the witness, never our own logs.

Drives the real MCP surface with genuinely separate client sessions, then asks
DataHub what it actually holds. Written BEFORE the features it checks, so the
red lines below are the specification for Lane A.

    python scripts/eval_nullspace.py           # assumes the stack is up
    python scripts/eval_nullspace.py --cold    # wipes the local ghost store first

Exit 0 only if every REQUIRED check passes. Checks marked PENDING are known gaps
and are reported but do not fail the run until their owner lands them.

LANE B (Claude).
"""

from __future__ import annotations

import asyncio
import json
import os
import subprocess
import sys
import time
import urllib.parse
import urllib.request

from mcp import ClientSession, Implementation, StdioServerParameters
from mcp.client.stdio import stdio_client

GMS = os.getenv("DATAHUB_GMS_URL", "http://localhost:8080")
WANT = os.getenv("NULLSPACE_EVAL_WANT", "monthly recurring revenue by segment")
STORE = os.getenv("NULLSPACE_STORE", "/tmp/nullspace-eval.json")

REQUESTERS = [
    ("revenue-copilot", "1.0.0"),
    ("finance-agent", "2.3.1"),
    ("board-deck-writer", "0.9.0"),
]
FOURTH = ("cfo-assistant", "1.1.0")

PASS, FAIL, PEND = [], [], []


def ok(msg: str) -> None:
    print(f"  PASS  {msg}")
    PASS.append(msg)


def bad(msg: str) -> None:
    print(f"  FAIL  {msg}")
    FAIL.append(msg)


def pending(msg: str, owner: str) -> None:
    print(f"  PEND  {msg}  [{owner}]")
    PEND.append(msg)


def head(msg: str) -> None:
    print(f"\n== {msg}")


# ------------------------------------------------------------------ datahub


def gql(query: str) -> dict:
    req = urllib.request.Request(
        f"{GMS}/api/graphql",
        data=json.dumps({"query": query}).encode(),
        headers={"Content-Type": "application/json"},
    )
    import base64

    token = base64.b64encode(b"datahub:datahub").decode()
    req.add_header("Authorization", f"Basic {token}")
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.load(r)


def dataset(urn: str) -> dict | None:
    q = """{ dataset(urn: "%s") {
        urn
        tags { tags { tag { urn } } }
        properties { customProperties { key value } }
        schemaMetadata { fields { fieldPath } }
        ownership { owners { owner { ... on CorpUser { urn } } } }
        upstream: lineage(input:{direction:UPSTREAM, start:0, count:20}) { total }
    } }""" % urn
    return gql(q).get("data", {}).get("dataset")


def ghost_urns_for_want(want: str) -> list[str]:
    """Exact-want match via datasetProperties — never WANT.split()[0] prefix search."""
    q = """
    {
      search(input: {
        type: DATASET,
        query: "*",
        orFilters: [{ and: [{ field: "platform", values: ["urn:li:dataPlatform:nullspace"] }] }],
        start: 0, count: 100
      }) {
        searchResults {
          entity {
            urn
            ... on Dataset {
              properties { customProperties { key value } }
            }
          }
        }
      }
    }
    """
    res = gql(q)["data"]["search"]["searchResults"]
    want_key = want.strip().lower()
    matched: list[str] = []
    for row in res:
        entity = row.get("entity") or {}
        urn = entity.get("urn") or ""
        if ":nullspace," not in urn:
            continue
        props = {
            p["key"]: p["value"]
            for p in ((entity.get("properties") or {}).get("customProperties") or [])
        }
        if (props.get("nullspace.want") or "").strip().lower() == want_key:
            matched.append(urn)
    return matched


def ghost_count(want: str) -> list[str]:
    return ghost_urns_for_want(want)


# ---------------------------------------------------------------------- mcp


def _text(result) -> str:
    return "\n".join(getattr(b, "text", "") for b in result.content)


async def agent_call(name: str, version: str, tool: str, args: dict) -> dict:
    params = StdioServerParameters(
        command=sys.executable, args=["-m", "nullspace.mcp_server"], env={**os.environ}
    )
    async with stdio_client(params) as (read, write):
        async with ClientSession(
            read, write, client_info=Implementation(name=name, version=version)
        ) as session:
            await session.initialize()
            raw = _text(await session.call_tool(tool, args))
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"_raw": raw}


# --------------------------------------------------------------------- run


async def main() -> int:
    started = time.time()

    if "--cold" in sys.argv:
        if os.path.exists(STORE):
            os.remove(STORE)
            print(f"(cold: removed {STORE})")
        contracts = os.getenv("NULLSPACE_CONTRACTS", "/tmp/nullspace-contracts.json")
        if os.path.exists(contracts):
            os.remove(contracts)
            print(f"(cold: removed {contracts})")
        # `--cold` used to call `nullspace reset`, which HARD-DELETES every
        # asset on platform nullspace. The README points judges at this command.
        # Running our own documented verification therefore destroyed the demo
        # graph — 41 harvested wants and 395 attributed requesters — and it would
        # have done the same to a judge mid-evaluation, or to us mid-recording.
        #
        # Cold means "this eval starts from nothing", not "the catalog starts
        # from nothing". It now clears only its own caches and its own want.
        # Wiping everything is still available, but you have to ask for it by
        # name and it tells you what it is about to do.
        if "--wipe-catalog" in sys.argv:
            print("(cold: --wipe-catalog — hard-deleting EVERY nullspace asset)")
            reset = subprocess.run(
                [sys.executable, "-m", "nullspace.cli", "reset"],
                capture_output=True,
                text=True,
            )
            print(reset.stdout or reset.stderr)
            if reset.returncode != 0:
                bad(f"cold reset failed (exit {reset.returncode})")
                return summary(started)
        else:
            print(
                f"(cold: caches cleared; catalog left alone. This eval uses a "
                f"fresh want, so it needs no wipe. Pass --wipe-catalog to "
                f"hard-delete every nullspace asset.)"
            )

    head("CHECK 0 — DataHub is answering")
    try:
        with urllib.request.urlopen(f"{GMS}/health", timeout=10) as r:
            (ok if r.status == 200 else bad)(f"GMS {GMS}/health -> {r.status}")
    except Exception as exc:
        bad(f"GMS unreachable ({exc}) — nothing below can be trusted")
        return summary(started)

    head("CHECK 1 — independent agents converge on ONE ghost")
    urn = None
    for i, (name, ver) in enumerate(REQUESTERS, start=1):
        r = await agent_call(name, ver, "find_dataset", {"want": WANT})
        if r.get("status") != "miss_ghosted":
            bad(f"{name} got status={r.get('status')!r}, expected miss_ghosted")
            continue
        if not str(r.get("identified_by", "")).startswith("mcp clientInfo"):
            bad(f"{name} was not identified over MCP ({r.get('identified_by')})")
        urn = r["ghost"]["urn"]
        demand = r["ghost"]["demand"]
        (ok if demand == i else bad)(
            f"{name} recorded as requester {i}; demand now {demand} (expected {i})"
        )

    head("CHECK 2 — DataHub holds exactly one ghost, with all requesters")
    urns = ghost_count(WANT)
    (ok if len(urns) == 1 else bad)(
        f"DataHub returns {len(urns)} nullspace entity/entities for this demand (expected 1)"
    )
    d = dataset(urn) if urn else None
    props = (
        {p["key"]: p["value"] for p in d["properties"]["customProperties"]}
        if d and d.get("properties")
        else {}
    )
    reqs = [x for x in props.get("nullspace.requesters", "").split(",") if x]
    (ok if len(reqs) == 3 else bad)(
        f"DataHub returns {len(reqs)} requesters: {reqs}"
    )

    head("CHECK 3 — a 4th agent increments, never duplicates")
    r4 = await agent_call(*FOURTH, "find_dataset", {"want": WANT})
    d4 = r4.get("ghost", {}).get("demand")
    (ok if d4 == 4 else bad)(f"4th independent agent -> demand {d4} (expected 4)")
    (ok if len(ghost_count(WANT)) == 1 else bad)(
        "still exactly one ghost in DataHub after the 4th miss"
    )

    head("CHECK 4 — refusal states its reason AND the shortfall")
    r = await agent_call(
        "premature-builder", "1.0.0", "claim_and_build", {"want": "nobody asked for this"}
    )
    reason = r.get("reason", "")
    (ok if r.get("status") == "refused" else bad)("claiming an unknown ghost is refused")
    (ok if reason else bad)(f"refusal states a reason: {reason!r}")

    head("CHECK 5 — the ghost goes solid")
    built = await agent_call("nullspace-builder", "1.0.0", "claim_and_build", {"want": WANT})
    (ok if built.get("status") in ("solidified", "refused") else bad)(
        f"builder returned status={built.get('status')!r}"
    )
    d = dataset(urn) if urn else None
    tags = [t["tag"]["urn"] for t in d["tags"]["tags"]] if d and d.get("tags") else []
    (ok if "urn:li:tag:solid" in tags else bad)(f"DataHub returns tags {tags}")

    head("CHECK 6 — what the README promises (Lane A's open work)")
    fields = (d.get("schemaMetadata") or {}).get("fields") if d else None
    if fields:
        ok(f"DataHub returns schemaMetadata with {len(fields)} field(s)")
    else:
        pending("schemaMetadata is null — README claims 'real schema'", "Lane A / L1")

    up = ((d or {}).get("upstream") or {}).get("total", 0)
    if up and up > 0:
        ok(f"DataHub returns {up} upstream lineage edge(s)")
    else:
        pending("0 upstream lineage — README claims 'real lineage'", "Lane A / L2")

    owners = (
        [o["owner"]["urn"] for o in d["ownership"]["owners"]]
        if d and d.get("ownership")
        else []
    )
    if len(owners) >= 3:
        ok(f"requesters are native Owners and render in the UI: {owners}")
    else:
        pending(
            f"{len(owners)} native Owner(s) — the requesters should appear here (STEAL 1)",
            "Lane A / L2b",
        )

    pr = props.get("nullspace.pr_url", "")
    if pr.startswith("https://github.com/"):
        state = subprocess.run(
            ["gh", "pr", "view", pr, "--json", "state", "-q", ".state"],
            capture_output=True, text=True,
        ).stdout.strip()
        (ok if state == "OPEN" else bad)(f"pr_url is a real PR, state={state!r}")
    else:
        pending(f"pr_url is not a real PR ({pr[:40]}…) — blocked on D9", "Oscar / D9")

    head("CHECK 7 — stranger clock")
    elapsed = int(time.time() - started)
    (ok if elapsed < 180 else bad)(f"reached solid in {elapsed}s (< 180s)")

    return summary(started)


def summary(started: float) -> int:
    print()
    print(f"RESULT: {len(PASS)} passed, {len(FAIL)} failed, {len(PEND)} pending")
    for p in PEND:
        print(f"  PENDING: {p}")
    return 1 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
