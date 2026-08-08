"""Builder agent: claim a ready ghost → write dbt model → change reference → solidify."""

from __future__ import annotations

import asyncio
import json
import os
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from nullspace.client import DataHubClient
from nullspace.config import settings
from nullspace.ghosts import Ghost, Nullspace

FALLBACK_DBT_MODEL = '''-- Nullspace fallback model for demand: {want}
-- Requesters: {requesters}
-- Ghost URN: {urn}
-- Schema source: disclosed fallback (no requester queries were registered)

select
    cohort_id,
    count(*) as trials,
    count(converted_at) as conversions,
    count(converted_at)::double precision / nullif(count(*), 0) as trial_to_paid_rate
from {{{{ source('warehouse_source', 'trials') }}}}
group by cohort_id
'''

SOLID_SCHEMA_FIELDS = [
    {"name": "cohort_id", "native_type": "VARCHAR", "nullable": False},
    {"name": "trials", "native_type": "BIGINT", "nullable": False},
    {"name": "conversions", "native_type": "BIGINT", "nullable": False},
    {"name": "trial_to_paid_rate", "native_type": "DOUBLE", "nullable": True},
]
_PLAN_STORE = Path(
    os.getenv("NULLSPACE_BUILDER_PLANS", "/tmp/nullspace-builder-plans.json")
)

@dataclass(frozen=True)
class BuildPlan:
    fields: list[dict[str, object]]
    model_sql: str
    upstream_urn: str
    schema_source: str
    source_schema: str
    source_table: str
    decision_reason: str


def _plan_key(want: str) -> str:
    return want.strip().lower()


def save_agent_plan(want: str, plan: BuildPlan) -> None:
    """Persist the real builder agent's decision for the MCP build tool."""
    data: dict[str, Any] = {}
    if _PLAN_STORE.exists():
        try:
            data = json.loads(_PLAN_STORE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            data = {}
    data[_plan_key(want)] = asdict(plan)
    _PLAN_STORE.parent.mkdir(parents=True, exist_ok=True)
    temp = _PLAN_STORE.with_suffix(f".{os.getpid()}.tmp")
    temp.write_text(json.dumps(data, indent=2), encoding="utf-8")
    os.replace(temp, _PLAN_STORE)


def _load_agent_plan(want: str) -> BuildPlan | None:
    if not _PLAN_STORE.exists():
        return None
    try:
        raw = json.loads(_PLAN_STORE.read_text(encoding="utf-8")).get(_plan_key(want))
    except (json.JSONDecodeError, OSError):
        return None
    return BuildPlan(**raw) if raw else None


def _source_parts(urn: str) -> tuple[str, str]:
    try:
        dataset_name = urn.split(",", 2)[1]
        parts = dataset_name.split(".")
        return parts[-2], parts[-1]
    except (IndexError, ValueError) as exc:
        raise ValueError(f"builder refused: cannot parse source dataset URN {urn!r}") from exc


def generate_model_sql(
    *,
    want: str,
    requesters: list[str],
    ghost_urn: str,
    fields: list[dict[str, object]],
    source_table: str,
) -> str:
    """Compile executable SQL from the fields in the registered requester queries."""
    projections = ",\n".join(f'    "{field["name"]}"' for field in fields)
    return (
        f"-- Nullspace builder-agent output for demand: {want}\n"
        f"-- Requesters: {', '.join(requesters)}\n"
        f"-- Ghost URN: {ghost_urn}\n"
        "-- Generated from registered query contracts and a DataHub-returned source.\n\n"
        "select\n"
        f"{projections}\n"
        f"from {{{{ source('warehouse_source', '{source_table}') }}}}\n"
    )


def plan_for_demand(want: str) -> BuildPlan:
    """Use a real builder-agent plan, otherwise an explicitly disclosed fallback."""
    agent_plan = _load_agent_plan(want)
    if agent_plan is not None:
        return agent_plan

    from nullspace.agents.contracts import ContractStore

    demanded = ContractStore().demanded_schema(want)
    if demanded:
        raise ValueError(
            "build refused: registered requester queries require the autonomous "
            "builder agent to inspect open_demand, choose a ghost, discover a "
            f"source, and write SQL; shortfall is a builder plan for {len(demanded)} "
            "demanded fields"
        )

    cfg = settings()
    source_schema, source_table = _source_parts(cfg.warehouse_source_urn)
    return BuildPlan(
        fields=SOLID_SCHEMA_FIELDS,
        model_sql=FALLBACK_DBT_MODEL,
        upstream_urn=cfg.warehouse_source_urn,
        schema_source="disclosed fallback: no builder-agent plan was present",
        source_schema=source_schema,
        source_table=source_table,
        decision_reason="direct build tool call used the disclosed fallback plan",
    )


def write_dbt_model(ghost: Ghost, repo: Path, plan: BuildPlan) -> Path:
    models = repo / "models"
    models.mkdir(parents=True, exist_ok=True)
    sources = models / "sources.yml"
    sources.write_text(
        "version: 2\n"
        "sources:\n"
        "  - name: warehouse_source\n"
        f"    schema: {plan.source_schema}\n"
        "    tables:\n"
        f"      - name: {plan.source_table}\n",
        encoding="utf-8",
    )
    out = models / f"{ghost.dataset_name}.sql"
    rendered_sql = (
        plan.model_sql.format(
            want=ghost.want,
            requesters=", ".join(ghost.requesters),
            urn=ghost.urn,
        )
        if "{want}" in plan.model_sql
        else plan.model_sql
    )
    out.write_text(
        rendered_sql,
        encoding="utf-8",
    )
    return out


def create_change_reference(repo: Path, branch: str, title: str, model_path: Path) -> str:
    """Commit explicit dbt files; return a real PR URL only when one exists."""
    subprocess.run(["git", "init"], cwd=repo, check=False, capture_output=True)
    subprocess.run(["git", "checkout", "-B", branch], cwd=repo, check=True, capture_output=True)
    explicit_paths = [
        "dbt_project.yml",
        "models/sources.yml",
        str(model_path.relative_to(repo)),
    ]
    subprocess.run(
        ["git", "add", "--", *explicit_paths],
        cwd=repo,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "commit", "-m", title, "--allow-empty"],
        cwd=repo,
        check=False,
        capture_output=True,
    )
    # Prefer real GitHub PR when remote + gh exist
    remote = subprocess.run(
        ["git", "remote", "get-url", "origin"],
        cwd=repo,
        check=False,
        capture_output=True,
        text=True,
    )
    if remote.returncode == 0 and remote.stdout.strip():
        subprocess.run(
            ["git", "push", "-u", "origin", branch],
            cwd=repo,
            check=False,
            capture_output=True,
        )
        pr = subprocess.run(
            ["gh", "pr", "create", "--title", title, "--body", title],
            cwd=repo,
            check=False,
            capture_output=True,
            text=True,
        )
        if pr.returncode == 0 and pr.stdout.strip():
            return pr.stdout.strip().splitlines()[-1]
    # Honest local change reference. This is not a pull request.
    return f"file://{repo.resolve()}#{branch}"


def build_and_solidify(ns: Nullspace, want: str, *, builder_id: str = "builder-1") -> Ghost:
    cfg = settings()
    plan = plan_for_demand(want)
    repo = Path(cfg.dbt_repo_path).resolve()
    repo.mkdir(parents=True, exist_ok=True)
    if not (repo / "dbt_project.yml").exists():
        (repo / "dbt_project.yml").write_text(
            "name: nullspace_fulfillment\nversion: '1.0.0'\nprofile: nullspace\n"
            "model-paths: ['models']\n",
            encoding="utf-8",
        )

    ghost = ns.claim(want, builder_id)
    path = write_dbt_model(ghost, repo, plan)
    branch = f"nullspace/{ghost.dataset_name}"
    title = f"feat(nullspace): solidify {ghost.want}"
    pr_url = create_change_reference(repo, branch, title, path)
    ns.attach_pr(want, pr_url)
    return ns.solidify(
        want,
        schema_fields=plan.fields,
        upstream_urns=[plan.upstream_urn],
        schema_source=plan.schema_source,
    )


def _tool_json(result: Any) -> dict[str, Any]:
    text = "\n".join(getattr(block, "text", "") for block in result.content)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {"status": "error", "reason": f"MCP returned non-JSON: {text[:300]}"}


def _choose_ghost(board: dict[str, Any]) -> tuple[dict[str, Any] | None, str]:
    threshold = int(board.get("threshold", 3))
    ghosts = [
        ghost
        for ghost in board.get("ghosts", [])
        if ghost.get("state") == "ghost"
    ]
    if not ghosts:
        return None, "declined: the demand board has 0 open ghosts"
    ranked = sorted(
        ghosts,
        key=lambda ghost: (
            -int(ghost.get("demand", 0)),
            min(
                (
                    event.get("at_ms", 0)
                    for event in ghost.get("resolution", [])
                    if event.get("event") == "miss"
                ),
                default=0,
            ),
            str(ghost.get("want", "")),
        ),
    )
    choice = ranked[0]
    demand = int(choice.get("demand", 0))
    if demand < threshold:
        shortfall = threshold - demand
        requester_word = "requester agent" if shortfall == 1 else "requester agents"
        decline_reason = (
            f"declined: highest demand is {demand} of {threshold}; "
            f"{shortfall} more {requester_word} must ask"
        )
        return None, decline_reason
    reason = (
        f"chose {choice['want']!r}: highest independent demand "
        f"({demand}, threshold {threshold}); oldest demand breaks ties"
    )
    return choice, reason


async def run_builder_agent() -> dict[str, Any]:
    """Observe the board over MCP, decide, generate SQL, then invoke the build tool."""
    from mcp import ClientSession, Implementation, StdioServerParameters
    from mcp.client.stdio import stdio_client

    params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "nullspace.mcp_server"],
        env={**os.environ},
    )
    async with stdio_client(params) as (read, write), ClientSession(
        read,
        write,
        client_info=Implementation(name="nullspace-builder", version="1.0.0"),
    ) as session:
        await session.initialize()
        board = _tool_json(await session.call_tool("open_demand", {}))
        choice, reason = _choose_ghost(board)
        print(f"DECISION: {reason}")
        if choice is None:
            return {"status": "declined", "reason": reason, "board": board}

        want = str(choice["want"])
        contract = _tool_json(
            await session.call_tool("contract_status", {"want": want})
        )
        fields = [str(field) for field in contract.get("demanded_schema", [])]
        queries = contract.get("queries", [])
        if not fields or not queries:
            reason = (
                f"declined: {want!r} has {len(queries)} registered queries and "
                f"{len(fields)} demanded fields; at least 1 of each is required"
            )
            print(f"DECISION: {reason}")
            return {"status": "declined", "reason": reason}

        source = DataHubClient().find_source_covering_fields(fields)
        if source is None:
            reason = (
                f"declined: no DataHub warehouse dataset covers all {len(fields)} "
                f"demanded fields {fields}; shortfall cannot be satisfied"
            )
            print(f"DECISION: {reason}")
            return {"status": "declined", "reason": reason}

        source_schema, source_table = _source_parts(str(source["urn"]))
        model_sql = generate_model_sql(
            want=want,
            requesters=list(choice.get("requesters", [])),
            ghost_urn=str(choice["urn"]),
            fields=list(source["fields"]),
            source_table=source_table,
        )
        plan = BuildPlan(
            fields=list(source["fields"]),
            model_sql=model_sql,
            upstream_urn=str(source["urn"]),
            schema_source=(
                "builder agent: registered requester queries + "
                "DataHub-returned warehouse schema"
            ),
            source_schema=source_schema,
            source_table=source_table,
            decision_reason=reason,
        )
        save_agent_plan(want, plan)
        print("GENERATED SQL:")
        print(model_sql)

        built = _tool_json(
            await session.call_tool("claim_and_build", {"want": want})
        )
        built["decision_reason"] = reason
        built["generated_sql"] = model_sql
        built["source_urn"] = source["urn"]
        return built


def main() -> None:
    result = asyncio.run(run_builder_agent())
    print("RESULT:")
    print(json.dumps(result, indent=2))
    if result.get("status") not in {"solidified", "declined"}:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
