"""The agents come back and run the query they failed at. Nobody asked again.

This is the end of the loop, and it is the half everybody forgets. The catalog's
story ends when the ghost goes solid. The *agent's* story does not: it failed on
Monday, it went away, and nothing has told it anything since.

So: read the queries the requesters registered against a table that did not
exist, point them at the table that now does, and run them. Real SQL, real rows,
same agents, same statements — the exact text each one registered, with only the
placeholder replaced. If a query still cannot run, this says so and shows the
error, because a green wall of ticks that never fails is not evidence.

Nothing here re-asks. The three agents did not poll and did not retry. The
catalog knew who was blocked, because it recorded who asked.

    python scripts/agents_return.py --want "monthly recurring revenue by segment"

LANE B (Claude). Reads Lane A's state; writes nothing.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Run as `python scripts/agents_return.py` from anywhere: only `scripts/` lands
# on sys.path that way, so the package next to it has to be added explicitly.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import psycopg

from nullspace.agents.contracts import ContractStore
from nullspace.config import settings
from nullspace.persist import FileGhostStore

PLACEHOLDERS = ("<the table that does not exist>", "{}", "{table}")


def resolve_relation(dataset_name: str, schema: str) -> str:
    return f'{schema}."{dataset_name}"'


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--want", required=True)
    p.add_argument(
        "--schema",
        default="nullspace",
        help="schema dbt materialised the model into",
    )
    p.add_argument("--rows", type=int, default=5)
    a = p.parse_args()

    cfg = settings()
    ghost = FileGhostStore().get(a.want)
    if ghost is None:
        print(f"No ghost for {a.want!r}. Nobody has asked for it.")
        return 1
    if ghost.state != "solid":
        print(
            f"{a.want!r} is still {ghost.state} — demand {ghost.demand}. "
            "Nothing to tell anyone yet, so nothing is being claimed."
        )
        return 1

    contracts = ContractStore().queries(a.want)
    if not contracts:
        print(f"{a.want!r} is solid, but no requester registered a query.")
        return 1

    relation = resolve_relation(ghost.dataset_name, a.schema)

    print()
    print(f"  {a.want}")
    print(f"  went solid as {relation}")
    print(
        f"  {len(contracts)} agents registered a query against it while it did "
        "not exist."
    )
    print("  None of them asked again.")
    print()

    ok = 0
    with psycopg.connect(cfg.warehouse_dsn) as conn:
        for c in contracts:
            agent = c.get("agent_id", "unknown")
            sql = c.get("sql", "")
            for ph in PLACEHOLDERS:
                sql = sql.replace(ph, relation)
            print(f"  ── {agent}")
            print(f"     {sql}")
            try:
                with conn.cursor() as cur:
                    cur.execute(sql)
                    cols = [d.name for d in (cur.description or [])]
                    rows = cur.fetchmany(a.rows)
                conn.rollback()
            except Exception as exc:  # noqa: BLE001
                conn.rollback()
                print(f"     STILL BLOCKED — {type(exc).__name__}: {exc}")
                print()
                continue
            ok += 1
            print(f"     RUNS — {len(rows)} rows")
            if cols:
                print("     " + " | ".join(cols))
            for r in rows:
                print("     " + " | ".join(str(v) for v in r))
            print()

    print(f"  {ok} of {len(contracts)} queries that could not run, now run.")
    print("  The catalog knew who was blocked, because it recorded who asked.")
    print()
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
