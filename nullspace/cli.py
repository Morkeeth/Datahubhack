from __future__ import annotations

import argparse
import json
import sys

from nullspace.builder import build_and_solidify, solidify_after_merge
from nullspace.client import DataHubClient
from nullspace.config import settings
from nullspace.ghosts import Nullspace, consumer_search
from nullspace.persist import FileGhostStore


def _ns() -> Nullspace:
    cfg = settings()
    store = FileGhostStore()
    dh = DataHubClient(cfg)
    return Nullspace(store, demand_threshold=cfg.demand_threshold, dh=dh if dh.healthy() else None)


def cmd_ask(args: argparse.Namespace) -> int:
    ns = _ns()
    dh = DataHubClient()
    receipt = consumer_search(
        ns,
        want=args.want,
        agent_id=args.agent,
        dh=dh if dh.healthy() else None,
    )
    print(json.dumps(receipt, indent=2))
    return 0


def cmd_build(args: argparse.Namespace) -> int:
    ns = _ns()
    ghost = build_and_solidify(ns, args.want, builder_id=args.agent)
    print(json.dumps(ghost.to_public(), indent=2))
    return 0


def cmd_finalize(args: argparse.Namespace) -> int:
    ns = _ns()
    ghost = solidify_after_merge(
        ns,
        args.want,
        builder_id=args.agent,
        merge=not args.observe_only,
    )
    print(json.dumps(ghost.to_public(), indent=2))
    return 0


def cmd_reset(_: argparse.Namespace) -> int:
    ns = _ns()
    result = ns.reset()
    print(json.dumps(result, indent=2))
    if result.get("datahub_nullspace_count", 0) != 0:
        return 1
    return 0


def cmd_board_dump(_: argparse.Namespace) -> int:
    store = FileGhostStore()
    print(json.dumps([g.to_public() for g in store.list_ghosts()], indent=2))
    return 0


def cmd_demo(_: argparse.Namespace) -> int:
    """Three consumers → demand=3 → builder solidifies. Prints receipts."""
    cfg = settings()
    want = cfg.demo_asset_name.replace("_", " ")
    # nicer phrase for the board
    want = "trial-to-paid conversion by cohort"
    ns = _ns()
    dh = DataHubClient()
    live = dh if dh.healthy() else None
    if live is None:
        print("WARN: DataHub GMS not reachable — running memory/file loop only", file=sys.stderr)

    for agent in ("consumer-a", "consumer-b", "consumer-c"):
        receipt = consumer_search(ns, want=want, agent_id=agent, dh=live)
        print(json.dumps(receipt, indent=2))
        print("---")

    ready = ns.ready_to_build()
    if not ready:
        print("ERROR: demand threshold not reached", file=sys.stderr)
        return 1
    ghost = build_and_solidify(ns, want)
    print(json.dumps(ghost.to_public(), indent=2))
    if ghost.state == "claimed" and str(ghost.pr_url or "").startswith("https://"):
        print("PR open — finalize with: python3 -m nullspace.cli finalize --want", want)
    print("\nBoard: http://localhost:8787")
    return 0


def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser(prog="nullspace")
    sub = p.add_subparsers(dest="cmd", required=True)

    a = sub.add_parser("ask", help="consumer agent: search, ghost on miss")
    a.add_argument("--want", required=True)
    a.add_argument("--agent", required=True)
    a.set_defaults(func=cmd_ask)

    b = sub.add_parser("build", help="builder agent: claim + dbt PR + solidify")
    b.add_argument("--want", required=True)
    b.add_argument("--agent", default="builder-1")
    b.set_defaults(func=cmd_build)

    f = sub.add_parser(
        "finalize",
        help="merge open PR (or observe merge) and solidify the claimed ghost",
    )
    f.add_argument("--want", required=True)
    f.add_argument("--agent", default="builder-1")
    f.add_argument(
        "--observe-only",
        action="store_true",
        help="do not merge; require the PR to already be MERGED",
    )
    f.set_defaults(func=cmd_finalize)

    r = sub.add_parser("reset", help="wipe local store and hard-delete nullspace assets")
    r.set_defaults(func=cmd_reset)

    d = sub.add_parser("demo", help="full ghost→solid beat")
    d.set_defaults(func=cmd_demo)

    s = sub.add_parser("dump", help="print ghost store JSON")
    s.set_defaults(func=cmd_board_dump)

    args = p.parse_args(argv)
    raise SystemExit(args.func(args))


if __name__ == "__main__":
    main()
