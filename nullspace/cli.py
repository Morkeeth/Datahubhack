from __future__ import annotations

import argparse
import json
import os
import sys

from nullspace.builder import build_and_solidify, solidify_after_merge
from nullspace.client import DataHubClient
from nullspace.config import settings
from nullspace.ghosts import MemoryGhostStore, Nullspace, consumer_search
from nullspace.persist import FileGhostStore


def _store():
    """Local JSON is an optional cache. ``memory`` / empty → hydrate-only."""
    path = os.getenv("NULLSPACE_STORE", "/tmp/nullspace-ghosts.json").strip()
    if path.lower() in {"", "memory", ":memory:", "none"}:
        return MemoryGhostStore()
    return FileGhostStore()


def _ns(*, require_catalog: bool = True, hydrate: bool = True) -> Nullspace:
    cfg = settings()
    store = _store()
    dh = DataHubClient(cfg)
    if require_catalog and not dh.healthy():
        raise SystemExit(
            json.dumps(
                {
                    "status": "refused",
                    "reason": (
                        "DataHub GMS unreachable at "
                        f"{cfg.gms_url}; Nullspace has no shared namespace without "
                        "the catalog. shortfall is 1 healthy GMS"
                    ),
                }
            )
        )
    if dh.healthy():
        # Register nullspace.* structured property defs before any ghost write.
        from nullspace.emit import ensure_structured_property_definitions

        ensure_structured_property_definitions(dh)
    ns = Nullspace(
        store,
        demand_threshold=cfg.demand_threshold,
        dh=dh if dh.healthy() else None,
    )
    if hydrate and ns.dh is not None:
        # Catalog is SoT — replace local cache from GMS when using memory store.
        ns.hydrate(replace=isinstance(store, MemoryGhostStore))
    return ns


def cmd_ask(args: argparse.Namespace) -> int:
    dh = DataHubClient()
    if not dh.healthy():
        print(
            json.dumps(
                {
                    "status": "refused",
                    "agent_id": args.agent,
                    "want": args.want,
                    "reason": (
                        "DataHub GMS unreachable at "
                        f"{settings().gms_url}; Nullspace has no shared namespace "
                        "without the catalog. shortfall is 1 healthy GMS"
                    ),
                },
                indent=2,
            )
        )
        return 1
    ns = _ns(require_catalog=True)
    # Same client as ns.dh so buffered ghost MCPs land before the process exits.
    receipt = consumer_search(
        ns,
        want=args.want,
        agent_id=args.agent,
        dh=ns.dh,
    )
    if ns.dh is not None:
        ns.dh.flush_ghost_emits()
    print(json.dumps(receipt, indent=2))
    return 0 if receipt.get("status") != "refused" else 1


def cmd_build(args: argparse.Namespace) -> int:
    ns = _ns(require_catalog=True)
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
    ns = _ns(hydrate=False)
    result = ns.reset()
    print(json.dumps(result, indent=2))
    if result.get("datahub_nullspace_count", 0) != 0:
        return 1
    return 0


def cmd_hydrate(_: argparse.Namespace) -> int:
    ns = _ns(hydrate=False)
    result = ns.hydrate(replace=True)
    print(json.dumps(result, indent=2))
    return 0


def cmd_board_dump(_: argparse.Namespace) -> int:
    """Dump ghosts from the catalog (hydrate cache first). Local file alone is not truth."""
    ns = _ns(hydrate=False)
    if ns.dh is None:
        print("[]")
        return 1
    ns.hydrate(replace=True)
    print(json.dumps([g.to_public() for g in ns.store.list_ghosts()], indent=2))
    return 0


def cmd_register_query(args: argparse.Namespace) -> int:
    ns = _ns()
    fields = [f.strip() for f in args.fields.split(",") if f.strip()]
    result = ns.register_contract(
        args.want,
        agent_id=args.agent,
        sql=args.sql,
        needs_fields=fields,
    )
    print(json.dumps(result, indent=2))
    return 0


def cmd_contract_status(args: argparse.Namespace) -> int:
    """Answer from GMS even when the /tmp contracts sidecar is gone."""
    ns = _ns()
    contracts = ns.contracts_for(args.want)
    print(
        json.dumps(
            {
                "status": "ok",
                "want": args.want,
                "source": "datahub",
                "contracts": contracts,
                "demanded_schema": ns.demanded_schema_from_catalog(args.want),
            },
            indent=2,
        )
    )
    return 0


def cmd_demo(_: argparse.Namespace) -> int:
    """Three consumers → demand=3 → builder solidifies. Prints receipts."""
    want = "trial-to-paid conversion by cohort"
    ns = _ns(require_catalog=True)
    dh = DataHubClient()

    for agent in ("consumer-a", "consumer-b", "consumer-c"):
        receipt = consumer_search(ns, want=want, agent_id=agent, dh=dh)
        print(json.dumps(receipt, indent=2))
        print("---")
        if receipt.get("status") == "refused":
            return 1

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

    h = sub.add_parser(
        "hydrate",
        help="rebuild local cache from DataHub alone (catalog is source of truth)",
    )
    h.set_defaults(func=cmd_hydrate)

    d = sub.add_parser("demo", help="full ghost→solid beat")
    d.set_defaults(func=cmd_demo)

    s = sub.add_parser("dump", help="hydrate from DataHub then print ghosts")
    s.set_defaults(func=cmd_board_dump)

    rq = sub.add_parser(
        "register-query",
        help="register a requester SQL contract onto the ghost in DataHub",
    )
    rq.add_argument("--want", required=True)
    rq.add_argument("--agent", required=True)
    rq.add_argument("--sql", required=True)
    rq.add_argument(
        "--fields",
        required=True,
        help="comma-separated field names the query needs",
    )
    rq.set_defaults(func=cmd_register_query)

    cs = sub.add_parser(
        "contract-status",
        help="read registered contracts from DataHub (sidecar optional)",
    )
    cs.add_argument("--want", required=True)
    cs.set_defaults(func=cmd_contract_status)

    args = p.parse_args(argv)
    raise SystemExit(args.func(args))


if __name__ == "__main__":
    main()
