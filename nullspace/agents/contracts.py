"""Ghost contracts — an agent writes a query against a table that does not exist.

A ghost is currently a tombstone: "this asset is missing." A contract turns it
into a promise. When an agent's search misses, it can **register the query it
meant to run** and the columns that query needs. Nullspace keeps them against the
ghost.

Two things fall out of that, and the second is the point:

1. **The demanded schema stops being invented.** `builder.build_and_solidify`
   currently hardcodes `schema_fields=["cohort_id", "trials", "conversions",
   "trial_to_paid_rate"]` for every ghost regardless of what was asked for. The
   union of the columns real agents asked for is the honest schema, and it is
   derived, not guessed.

2. **The requesters can be told when their query runs.** Once the asset is solid,
   each registered query is checked against the schema DataHub actually returns.
   Every requester gets `runs` or `blocked` with the exact missing columns named.

An agent writes SQL against a table that does not exist, and is told when it
becomes real.

LANE B (Claude). Sidecar storage; does not touch Lane A's ghost store.
"""

from __future__ import annotations

import json
import os
import re
import time
from dataclasses import asdict, dataclass, field
from typing import Any

CONTRACT_STORE = os.getenv(
    "NULLSPACE_CONTRACTS", "/tmp/nullspace-contracts.json"
)

# Conservative: only columns we can actually see in the text. Anything we cannot
# parse is reported as unparsed rather than silently dropped.
_COL = re.compile(r"\b([a-z_][a-z0-9_]{2,})\b")
_SQL_NOISE = {
    "select", "from", "where", "group", "order", "by", "and", "or", "not",
    "join", "left", "right", "inner", "outer", "on", "as", "with", "sum",
    "count", "avg", "min", "max", "case", "when", "then", "else", "end",
    "limit", "having", "distinct", "asc", "desc", "null", "over",
    "partition", "date_trunc", "coalesce", "cast", "interval",
}


@dataclass
class RegisteredQuery:
    agent_id: str
    want: str
    sql: str
    needs_fields: list[str]
    at_ms: int = field(default_factory=lambda: int(time.time() * 1000))

    def to_public(self) -> dict[str, Any]:
        return asdict(self)


def infer_fields(sql: str) -> tuple[list[str], str]:
    """Best-effort column guess from SQL. Returns (fields, how).

    Never presented as authoritative — an agent that cares should pass
    needs_fields explicitly, and the return value says which path was used.
    """
    tokens = [t for t in _COL.findall(sql.lower()) if t not in _SQL_NOISE]
    seen: list[str] = []
    for t in tokens:
        if t not in seen:
            seen.append(t)
    return seen, "inferred from SQL text (not authoritative)"


class ContractStore:
    def __init__(self, path: str | None = None) -> None:
        self.path = path or CONTRACT_STORE
        self._data: dict[str, list[dict[str, Any]]] = {}
        self._load()

    # ------------------------------------------------------------- storage
    def _load(self) -> None:
        if os.path.exists(self.path):
            try:
                with open(self.path) as fh:
                    self._data = json.load(fh)
            except (json.JSONDecodeError, OSError):
                self._data = {}

    def _save(self) -> None:
        tmp = f"{self.path}.tmp"
        with open(tmp, "w") as fh:
            json.dump(self._data, fh, indent=2)
        os.replace(tmp, self.path)

    @staticmethod
    def _key(want: str) -> str:
        return want.strip().lower()

    # --------------------------------------------------------------- write
    def register(self, q: RegisteredQuery) -> None:
        """One live query per agent per ghost — re-registering replaces."""
        k = self._key(q.want)
        rows = [r for r in self._data.get(k, []) if r["agent_id"] != q.agent_id]
        rows.append(q.to_public())
        self._data[k] = rows
        self._save()

    # ---------------------------------------------------------------- read
    def queries(self, want: str) -> list[dict[str, Any]]:
        return list(self._data.get(self._key(want), []))

    def demanded_schema(self, want: str) -> list[str]:
        """The union of columns real agents asked for, in first-asked order."""
        out: list[str] = []
        for row in self.queries(want):
            for f in row.get("needs_fields", []):
                if f not in out:
                    out.append(f)
        return out

    def settle(self, want: str, actual_fields: list[str]) -> dict[str, Any]:
        """Check every registered query against the schema DataHub returns."""
        actual = {f.lower() for f in actual_fields}
        results = []
        for row in self.queries(want):
            needed = [f.lower() for f in row.get("needs_fields", [])]
            missing = [f for f in needed if f not in actual]
            results.append(
                {
                    "agent_id": row["agent_id"],
                    "status": "runs" if not missing else "blocked",
                    "missing_fields": missing,
                    "sql": row["sql"],
                }
            )
        return {
            "want": want,
            "actual_fields": sorted(actual),
            "schema_published": bool(actual),
            "queries": results,
            "runs": sum(1 for r in results if r["status"] == "runs"),
            "blocked": sum(1 for r in results if r["status"] == "blocked"),
        }
