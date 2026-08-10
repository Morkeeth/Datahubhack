"""A builder agent that does not wait to be asked.

Everything up to now has a human at the trigger: demand accrues, and then
somebody runs the builder. That is fine for a demo and it is not what the product
is. The product is an order book that fills itself — you leave it running, agents
keep missing, and the things enough of them wanted keep becoming real.

So this watches open demand and claims what has crossed the threshold, one at a
time, stating every decision out loud. It is deliberately unexciting code. The
interesting part is what it refuses to do:

- **It will not run on a public instance.** Building writes a dbt model, pushes a
  branch and opens a pull request with the host's GitHub credentials. A watcher
  doing that unattended, driven by demand a stranger can create, is a way to turn
  an open endpoint into someone else's write access. `NULLSPACE_PUBLIC=1` stops
  it dead.
- **It will not build the same want twice**, and it will not retry a want that has
  already refused, until the refusal reason could plausibly have changed. A loop
  that retries a permanent failure forever is not autonomy, it is a busy signal.
- **It stops.** `--max-builds` is required to have a default, and the default is
  small. An agent with commit rights and no ceiling is not a feature.

Every cycle prints what it saw and what it did, including the cycles where it did
nothing, because "quiet" and "broken" have to be distinguishable at a glance.

    python -m nullspace.agents.watcher --interval 20 --max-builds 3

LANE B (Claude). Calls Lane A's builder; never edits it.
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from datetime import datetime, timezone

from nullspace.client import DataHubClient
from nullspace.config import settings
from nullspace.ghosts import Nullspace
from nullspace.persist import FileGhostStore


def stamp() -> str:
    return datetime.now(timezone.utc).strftime("%H:%M:%S")


def say(msg: str) -> None:
    print(f"  {stamp()}  {msg}", flush=True)


def public_mode() -> bool:
    return os.getenv("NULLSPACE_PUBLIC", "").lower() in {"1", "true", "yes"}


def run(interval: int, max_builds: int, once: bool) -> int:
    if public_mode():
        print(
            "watcher refused to start: NULLSPACE_PUBLIC=1.\n\n"
            "  On a public instance demand is created by strangers, and building\n"
            "  spends this machine's GitHub credentials. An unattended builder\n"
            "  driven by anonymous demand is a way to hand those credentials away.\n"
            "  Run the watcher on an instance you own, with demand you can see.",
            file=sys.stderr,
        )
        return 2

    cfg = settings()
    built = 0
    refused: dict[str, str] = {}
    cycle = 0

    print()
    print(f"  watching open demand · threshold {cfg.demand_threshold} · "
          f"stops after {max_builds} builds")
    print()

    while built < max_builds:
        cycle += 1
        dh = DataHubClient(cfg)
        if not dh.healthy():
            say("DataHub is not answering — not building on a catalog I cannot read")
            if once:
                return 1
            time.sleep(interval)
            continue

        ns = Nullspace(
            FileGhostStore(), demand_threshold=cfg.demand_threshold, dh=dh
        )
        ready = [g for g in ns.ready_to_build() if g.want not in refused]

        if not ready:
            waiting = [g for g in ns.store.list_ghosts() if g.state == "ghost"]
            top = max((g.demand for g in waiting), default=0)
            say(
                f"cycle {cycle}: nothing at threshold — {len(waiting)} open, "
                f"highest demand {top}"
                + (f", {len(refused)} parked after refusing" if refused else "")
            )
            if once:
                return 0
            time.sleep(interval)
            continue

        target = max(ready, key=lambda g: g.demand)
        say(
            f"cycle {cycle}: claiming {target.want!r} — demand {target.demand}, "
            f"asked by {len(target.requesters)} independent agents"
        )

        # The builder is an agent, not a function: it connects over MCP, reads
        # open_demand itself, picks, discovers a source and writes SQL. Calling
        # build_and_solidify directly is refused by design — the plan has to
        # come from the agent that made the decision. So the watcher starts the
        # agent and lets it choose; the watcher's job is deciding *when*, not
        # *what*. Imported here so a refusal above never depends on this
        # importing cleanly.
        import asyncio

        from nullspace.builder import run_builder_agent

        try:
            result = asyncio.run(run_builder_agent())
        except Exception as exc:  # noqa: BLE001
            refused[target.want] = f"{type(exc).__name__}: {exc}"
            say(f"          refused — {refused[target.want]}")
            say("          parked; it will not be retried this run")
            if once:
                return 1
            time.sleep(interval)
            continue

        status = (result or {}).get("status")
        chose = (result or {}).get("want") or target.want
        if status != "solidified":
            reason = (
                (result or {}).get("reason")
                or (result or {}).get("awaiting")
                or f"status {status}"
            )
            if chose in refused:
                # The watcher decides *when* to build; the builder decides
                # *what*, and there is currently no way to tell it "not that
                # one". So a top-of-book want the warehouse cannot satisfy is
                # picked again every cycle and the loop never advances past it.
                # Stopping is the honest response — a watcher that spins on the
                # same refusal is indistinguishable from one that is working.
                say(f"          refused {chose!r} again for the same reason")
                say("          stopping: the builder always picks the highest")
                say("          demand and cannot be told to skip it, so this")
                say("          would loop. See HANDOFF 007 — run_builder_agent")
                say("          needs a want argument.")
                break
            refused[chose] = reason
            say(f"          did not go solid — {reason}")
            say("          parked; it will not be retried this run")
        else:
            built += 1
            say(f"          solid · {(result or {}).get('pr_url') or 'no pull request'}")
            say(f"          {built} of {max_builds} builds used")

        if once:
            break
        time.sleep(interval)

    print()
    print(f"  stopped after {built} build(s). {len(refused)} want(s) parked:")
    for want, why in refused.items():
        print(f"    {want}: {why}")
    print()
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--interval", type=int, default=20, help="seconds between cycles")
    p.add_argument(
        "--max-builds",
        type=int,
        default=3,
        help="stop after this many. an agent with commit rights needs a ceiling",
    )
    p.add_argument("--once", action="store_true", help="one cycle, then exit")
    a = p.parse_args()
    return run(a.interval, a.max_builds, a.once)


if __name__ == "__main__":
    raise SystemExit(main())
