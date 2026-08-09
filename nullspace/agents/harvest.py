"""Harvest demand from a database's own error log — nobody has to adopt anything.

The version of Nullspace everyone sees first requires agents to opt in: they call
`find_dataset` through MCP, and their miss becomes demand. That is the honest
demo, and it has an obvious problem — it only works for agents that already know
about us.

This module is the answer, and it is smaller than it sounds. **Postgres already
writes every miss down.** When anything asks for a table that does not exist, the
server logs it verbatim:

    ERROR:  relation "ecommerce.churn_by_cohort" does not exist at character 15
    STATEMENT:  SELECT cohort, churn_rate FROM ecommerce.churn_by_cohort

That is a want, a timestamp, the columns that were needed, and the session that
needed them, sitting in a file on every warehouse in the world, being deleted
weekly by log rotation. No adoption, no SDK, no code change on the caller's side.
We read it and it becomes demand.

**On identity, plainly.** An MCP requester proves who it is through the
`clientInfo` handshake. A log line does not: the best we get is the backend PID
and, when `log_line_prefix` carries it, the application name. Every receipt from
this path says `postgres-log` as its identity source so a reader can tell the two
apart. We would rather be weaker and legible than strong and unfalsifiable.

Usage:
    docker logs warehouse 2>&1 | python -m nullspace.agents.harvest --stdin
    python -m nullspace.agents.harvest --log /var/log/postgresql/postgresql.log

LANE B (Claude). Calls Lane A's API; never edits it.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from typing import Iterable

from nullspace.agents.contracts import ContractStore, RegisteredQuery, infer_fields
from nullspace.client import DataHubClient
from nullspace.config import settings
from nullspace.ghosts import Nullspace, consumer_search
from nullspace.persist import FileGhostStore

# `ERROR:  relation "schema.table" does not exist` — Postgres phrases this one
# way and has for two decades. The pid in brackets is the backend that asked.
_ERROR = re.compile(
    r"\[(?P<pid>\d+)\][^:]*ERROR:\s+relation\s+\"(?P<relation>[^\"]+)\"\s+does not exist"
)
_STATEMENT = re.compile(r"\[(?P<pid>\d+)\][^:]*STATEMENT:\s+(?P<sql>.*)")
# Some deployments put the application name in log_line_prefix as [app=name].
_APP = re.compile(r"\[app=(?P<app>[^\]]+)\]")


@dataclass
class Miss:
    relation: str
    pid: str
    app: str | None = None
    sql: str | None = None
    at: str | None = None
    lines: list[str] = field(default_factory=list)

    @property
    def want(self) -> str:
        """`ecommerce.churn_by_cohort` -> `churn by cohort`.

        The relation name is what the caller typed, so it is the closest thing to
        a plain-English want that exists without asking anyone anything.
        """
        table = self.relation.split(".")[-1]
        return table.replace("_", " ").strip()

    @property
    def agent_id(self) -> str:
        return f"postgres-log-{self.app or 'session'}-{self.pid}"


def parse(lines: Iterable[str]) -> list[Miss]:
    """Pull missing-relation errors, and the statement that caused each one.

    Postgres emits ERROR and STATEMENT as separate lines sharing a backend pid,
    with the statement second. We key on the pid so interleaved sessions do not
    get each other's SQL.
    """
    pending: dict[str, Miss] = {}
    found: list[Miss] = []
    for raw in lines:
        line = raw.rstrip("\n")
        err = _ERROR.search(line)
        if err:
            app = _APP.search(line)
            miss = Miss(
                relation=err.group("relation"),
                pid=err.group("pid"),
                app=app.group("app") if app else None,
                at=line[:23].strip() or None,
                lines=[line],
            )
            pending[miss.pid] = miss
            found.append(miss)
            continue
        stmt = _STATEMENT.search(line)
        if stmt:
            miss = pending.get(stmt.group("pid"))
            if miss is not None and miss.sql is None:
                miss.sql = stmt.group("sql").strip()
                miss.lines.append(line)
    return found


def dedupe(misses: list[Miss]) -> list[Miss]:
    """Collapse a log to one entry per (want, requester).

    A real log repeats: a dashboard that refreshes every ten minutes logs the
    same miss 144 times a day. Demand is a count of *independent requesters*, so
    replaying every repeat would neither change the number nor tell us anything
    — it would just write the same fact to the catalog hundreds of times. We
    keep the richest query per pair, because the widest column list is the one
    that constrains the schema the builder has to deliver.
    """
    best: dict[tuple[str, str], Miss] = {}
    for m in misses:
        key = (m.want, m.agent_id)
        prev = best.get(key)
        if prev is None or len(m.sql or "") > len(prev.sql or ""):
            best[key] = m
    return list(best.values())


def harvest(misses: list[Miss], *, dry_run: bool = False) -> dict:
    """Turn parsed misses into demand, through the same path an agent uses."""
    cfg = settings()
    dh = DataHubClient(cfg)
    live = dh if dh.healthy() else None
    if live is None and not dry_run:
        return {
            "status": "refused",
            "reason": (
                "DataHub GMS is not reachable, so harvested demand would exist "
                "nowhere but this process. Refusing rather than recording a miss "
                "the catalog never sees."
            ),
            "parsed": len(misses),
        }

    ns = Nullspace(
        FileGhostStore(), demand_threshold=cfg.demand_threshold, dh=live
    )
    contracts = ContractStore()
    receipts = []

    for miss in misses:
        if dry_run:
            receipts.append(
                {
                    "want": miss.want,
                    "relation": miss.relation,
                    "agent_id": miss.agent_id,
                    "sql": miss.sql,
                    "identity_source": "postgres-log",
                    "would_record": True,
                }
            )
            continue

        receipt = consumer_search(
            ns, want=miss.want, agent_id=miss.agent_id, dh=live
        )
        receipt["identity_source"] = "postgres-log"
        receipt["harvested_from"] = miss.relation
        receipt["evidence"] = miss.lines

        if miss.sql:
            fields, how = infer_fields(miss.sql)
            # `infer_fields` reads a bare SELECT list and cannot know that
            # `ecommerce.churn_by_cohort` is the relation rather than two
            # columns. Drop anything that is part of the name we already know we
            # are missing, and say when a `SELECT *` told us nothing at all.
            noise = {miss.relation.lower(), *miss.relation.lower().split(".")}
            fields = [f for f in fields if f.lower() not in noise]
            if not fields:
                how = f"{how}; no usable column list (SELECT * or name-only)"

            contracts.register(
                RegisteredQuery(
                    want=miss.want,
                    agent_id=miss.agent_id,
                    sql=miss.sql,
                    needs_fields=fields,
                )
            )
            receipt["registered_fields"] = fields
            receipt["fields_inferred_by"] = how
        receipts.append(receipt)

    return {
        "status": "harvested" if not dry_run else "dry-run",
        "parsed": len(misses),
        "recorded": len(receipts),
        "identity_source": "postgres-log",
        "identity_caveat": (
            "A log line cannot prove who ran the query the way an MCP clientInfo "
            "handshake can. These requesters are attributed to the backend "
            "session that hit the error, and every receipt says so."
        ),
        "receipts": receipts,
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    src = p.add_mutually_exclusive_group(required=True)
    src.add_argument("--log", help="path to a Postgres server log")
    src.add_argument("--stdin", action="store_true", help="read the log on stdin")
    p.add_argument(
        "--all",
        action="store_true",
        help="record every repeat instead of one per (want, requester)",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="parse and report, write nothing to the catalog",
    )
    a = p.parse_args()

    lines = sys.stdin if a.stdin else open(a.log, encoding="utf-8", errors="replace")
    misses = parse(lines)
    raw_count = len(misses)
    if not a.all:
        misses = dedupe(misses)
    if not misses:
        # Silence is not a verdict — say what was looked for and not found.
        print(
            json.dumps(
                {
                    "status": "nothing to harvest",
                    "reason": "no `relation \"...\" does not exist` errors in this log",
                    "parsed": 0,
                },
                indent=2,
            )
        )
        return 0
    out = harvest(misses, dry_run=a.dry_run)
    out["log_lines_matched"] = raw_count
    out["unique_requester_want_pairs"] = len(misses)
    print(json.dumps(out, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
