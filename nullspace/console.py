"""The Nullspace console — what a person types when they want to look.

`nullspace.cli` is the machine surface: it emits JSON, and it should keep doing
that, because agents and scripts read it. This is the other half. It is for the
human standing in front of the catalog asking what their agents could not get,
and it prints something they can read without a JSON parser in their head.

Same design language as the board (`docs/design/design-prompt.md`, M1 Darkroom):
the demand count is the hero and it is cyan while a want is still waiting; when a
want becomes real the colour drains out of the number, because absence becoming
presence is a change in value, not a change in hue. Nothing blinks. Nothing is an
emoji.

    nullspace status                 is the catalog answering, and what is in it
    nullspace book                   the order book, ranked
    nullspace show "<want>"          one want's whole story
    nullspace ask "<want>"           one agent asks, once
    nullspace watch                  the same, live

LANE B (Claude). Reads Lane A's API; writes only through it.
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from datetime import datetime, timezone

# ---------------------------------------------------------------------- colour

_TTY = sys.stdout.isatty() and not os.getenv("NO_COLOR")


def _c(code: str, s: str) -> str:
    return f"\033[{code}m{s}\033[0m" if _TTY else s


def dim(s: str) -> str:
    return _c("2", s)


def bold(s: str) -> str:
    return _c("1", s)


def cyan(s: str) -> str:
    return _c("36", s)


def red(s: str) -> str:
    return _c("31", s)


def rule(title: str = "") -> None:
    width = 74
    if not title:
        print(dim("─" * width))
        return
    print()
    print(dim("── ") + bold(title) + " " + dim("─" * max(0, width - len(title) - 4)))


def ago(ms: int | None) -> str:
    if not ms:
        return "—"
    s = max(0.0, (time.time() * 1000 - ms) / 1000)
    if s < 90:
        return f"{s:.0f}s"
    if s < 5400:
        return f"{s/60:.0f}m"
    if s < 172800:
        return f"{s/3600:.0f}h"
    return f"{s/86400:.0f}d"


def stamp(ms: int | None) -> str:
    if not ms:
        return "--:--:--"
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).strftime("%H:%M:%S")


# ------------------------------------------------------------------- catalog

def _catalog():
    from nullspace.board import order_book, read_catalog

    return read_catalog, order_book


def _unreachable(snap: dict) -> bool:
    if snap.get("catalog") == "live":
        return False
    print()
    print(red("  The catalog is not answering, so there is nothing to show."))
    print(dim(f"  {snap.get('source','')} — {snap.get('detail', snap.get('reason',''))}"))
    print(dim("  Nullspace keeps no copy of its own. That is the point, and it"))
    print(dim("  is also why this is empty rather than stale."))
    print()
    return True


# -------------------------------------------------------------------- commands

def cmd_status(_: argparse.Namespace) -> int:
    read_catalog, _ob = _catalog()
    snap = read_catalog()
    if _unreachable(snap):
        return 1

    c = snap["counts"]
    ghosts = snap["ghosts"]
    demand = sum(g["demand"] for g in ghosts)
    voices = len({r for g in ghosts for r in g["requesters"]})

    rule("nullspace")
    print(f"  catalog     {snap['source']}  " + _c("32", "answering"))
    print(f"  wanted      {bold(str(c['ghost']))} not built yet")
    print(f"  claimed     {bold(str(c['claimed']))} being built")
    print(f"  real        {bold(str(c['solid']))} built because the demand was visible")
    print(f"  demand      {bold(str(demand))} requests from {bold(str(voices))} agents")

    top = [g for g in ghosts if g["state"] != "solid"][:3]
    if top:
        print()
        print(dim("  most wanted"))
        for g in top:
            print(f"    {cyan(str(g['demand']).rjust(4))}  {g['want']}")
    print()
    return 0


def cmd_book(a: argparse.Namespace) -> int:
    _rc, order_book = _catalog()
    d = order_book()
    if _unreachable(d):
        return 1

    t = d["totals"]
    rule("the order book")
    print(dim("  what your agents needed and could not get"))
    print()
    print(
        f"  {cyan(str(t['open_orders']))} unfilled   "
        f"{cyan(str(t['blocked_agents']))} agents blocked   "
        f"{bold(str(t['filled']))} built   "
        f"{bold(str(t['requests_unblocked']))} requests unblocked"
    )

    open_rows = d["open"][: a.limit]
    if open_rows:
        print()
        for r in open_rows:
            who = ", ".join(r["requesters"][:2])
            extra = len(r["requesters"]) - 2
            if extra > 0:
                who += dim(f" +{extra}")
            print(f"  {cyan(str(r['demand']).rjust(4))}  {bold(r['want'])}")
            print(f"        {dim('open ' + ago(r['first_asked_ms']) + ' · ' + who)}")
        rest = len(d["open"]) - len(open_rows)
        if rest > 0:
            tail = sum(r["demand"] for r in d["open"][a.limit :])
            print()
            print(dim(f"  and {rest} more, wanted by {tail} agents between them."))
            print(dim("  The long tail is most of the backlog, which is the point."))
    else:
        print()
        print(dim("  Nothing outstanding. Every table an agent asked for exists."))

    if d["filled"]:
        print()
        print(dim("  filled"))
        for r in d["filled"][:5]:
            built = r.get("time_to_fill_ms")
            when = f"{built/1000:.0f}s" if built else "—"
            print(f"  {bold(str(r['demand']).rjust(4))}  {r['want']}")
            print(
                f"        {dim('built in ' + when + ' · ' + str(r.get('upstream_total', 0)) + ' upstream')}"
            )
            if r.get("pr_url", "").startswith("http"):
                print(f"        {dim(r['pr_url'])}")
    print()
    return 0


def cmd_show(a: argparse.Namespace) -> int:
    _rc, order_book = _catalog()
    d = order_book()
    if _unreachable(d):
        return 1

    rows = [r for r in d["open"] + d["filled"] if r["want"].lower() == a.want.lower()]
    if not rows:
        print()
        print(f"  Nobody has asked for {a.want!r}.")
        print(dim("  `nullspace book` lists what they have asked for."))
        print()
        return 1
    r = rows[0]
    solid = r in d["filled"]

    rule(r["want"])
    print(f"  {(bold if solid else cyan)(str(r['demand']))}  agents asked"
          + (dim("  ·  now it exists") if solid else ""))
    print()
    for who in r["requesters"]:
        print(f"    {who}")
    print()
    print(dim(f"  {r['urn']}"))
    if solid:
        if r.get("fields"):
            print(dim("  schema      ") + ", ".join(r["fields"]))
        if r.get("pr_url", "").startswith("http"):
            print(dim("  pull req    ") + r["pr_url"])
        print(dim("  upstream    ") + str(r.get("upstream_total", 0)))
        print()
        print(dim("  `nullspace unblocked` runs the queries that could not run."))
    else:
        print(dim(f"  open {ago(r['first_asked_ms'])} · {r['blocked_agents']} blocked"))
    print()
    return 0


def cmd_ask(a: argparse.Namespace) -> int:
    from nullspace.client import DataHubClient
    from nullspace.config import settings
    from nullspace.ghosts import Nullspace, consumer_search
    from nullspace.persist import FileGhostStore

    cfg = settings()
    dh = DataHubClient(cfg)
    if not dh.healthy():
        print()
        print(red("  The catalog is not answering, so a miss would go nowhere."))
        print(dim("  Refusing rather than recording demand DataHub never sees."))
        print()
        return 1

    ns = Nullspace(FileGhostStore(), demand_threshold=cfg.demand_threshold, dh=dh)
    r = consumer_search(ns, want=a.want, agent_id=a.agent, dh=dh)

    print()
    if r["status"] != "miss_ghosted":
        print(f"  {bold(a.want)} already exists.")
        print(dim(f"  {r.get('urn') or r.get('status')}"))
        print()
        return 0

    g = r["ghost"]
    short = max(0, cfg.demand_threshold - g["demand"])
    print(f"  {bold(a.agent)} asked for {bold(a.want)} and it does not exist.")
    print()
    n = g['demand']
    print(f"  {cyan(str(n))}  agent{'' if n == 1 else 's'} {'has' if n == 1 else 'have'} now asked")
    print(
        dim(
            "  buildable — run `python -m nullspace.builder`"
            if short == 0
            else f"  {short} more independent agent{'' if short == 1 else 's'} must ask before it can be built"
        )
    )
    print()
    print(dim(f"  {g['urn']}"))
    print()
    return 0


def cmd_watch(a: argparse.Namespace) -> int:
    _rc, order_book = _catalog()
    seen: dict[str, str] = {}
    print()
    print(dim("  watching the catalog. ctrl-c to stop."))
    print()
    try:
        while True:
            d = order_book()
            if d.get("catalog") != "live":
                print(f"  {stamp(int(time.time()*1000))}  " + red("catalog unreachable"))
                time.sleep(a.interval)
                continue
            for r in d["open"] + d["filled"]:
                key = r["want"]
                now = f"{r['state'] if 'state' in r else ('solid' if r in d['filled'] else 'ghost')}:{r['demand']}"
                was = seen.get(key)
                if was == now:
                    continue
                seen[key] = now
                t = stamp(int(time.time() * 1000))
                if r in d["filled"]:
                    print(f"  {dim(t)}  {bold('REAL ')}  {r['want']}")
                elif was is None:
                    print(f"  {dim(t)}  {cyan('WANT ')}  {r['want']}  {dim('demand ' + str(r['demand']))}")
                else:
                    print(f"  {dim(t)}  {cyan('ASKED')}  {r['want']}  {dim('demand ' + str(r['demand']))}")
            time.sleep(a.interval)
    except KeyboardInterrupt:
        print()
        return 0


def cmd_unblocked(a: argparse.Namespace) -> int:
    from nullspace.board import unblocked

    d = unblocked(a.want)
    print()
    if d["status"] != "verified":
        print(f"  {d['status']} — {d.get('reason','')}")
        print()
        return 1
    print(f"  {bold(a.want)}")
    print(dim(f"  became {d['relation']}"))
    print(dim("  None of these agents asked again."))
    print()
    for q in d["queries"]:
        print(f"  {cyan(q['agent_id'])}")
        print(dim(f"    {q['sql']}"))
        if q["status"] == "runs":
            print(f"    {bold('RUNS')} — {len(q['rows'])} rows")
            if q.get("columns"):
                print(dim("    " + "  ".join(q["columns"])))
            for row in q["rows"][:3]:
                print(dim("    " + "  ".join(row)))
        else:
            print(f"    {red('STILL BLOCKED')} — {q.get('error','')}")
        print()
    print(f"  {bold(str(d['runs']))} of {d['total']} queries that could not run, now run.")
    print(dim(f"  Verified by {d['verified_by']}."))
    print()
    return 0


def main() -> int:
    p = argparse.ArgumentParser(prog="nullspace", description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("status", help="is the catalog answering, and what is in it")
    s.set_defaults(func=cmd_status)

    b = sub.add_parser("book", help="the order book, ranked")
    b.add_argument("--limit", type=int, default=10)
    b.set_defaults(func=cmd_book)

    sh = sub.add_parser("show", help="one want's whole story")
    sh.add_argument("want")
    sh.set_defaults(func=cmd_show)

    k = sub.add_parser("ask", help="one agent asks for something, once")
    k.add_argument("want")
    k.add_argument("--agent", default="you-at-the-terminal")
    k.set_defaults(func=cmd_ask)

    w = sub.add_parser("watch", help="the order book, live")
    w.add_argument("--interval", type=float, default=2.0)
    w.set_defaults(func=cmd_watch)

    u = sub.add_parser("unblocked", help="run the queries that could not run")
    u.add_argument("want")
    u.set_defaults(func=cmd_unblocked)

    a = p.parse_args()
    return a.func(a)


if __name__ == "__main__":
    raise SystemExit(main())
