"""Builder agent: claim a ready ghost → write dbt model → change reference → solidify."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import subprocess
import sys
from dataclasses import asdict, dataclass, replace
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
_RECEIPT_PATH = Path(
    os.getenv("NULLSPACE_BUILDER_RECEIPT", "/tmp/nullspace-builder-receipt.json")
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
    validation: dict[str, Any] | None = None


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


def _identifier(value: str) -> str:
    if not re.fullmatch(r"[a-z_][a-z0-9_]*", value):
        raise ValueError(f"builder refused: unsafe SQL identifier {value!r}")
    return value


def generate_model_sql(
    *,
    want: str,
    requesters: list[str],
    ghost_urn: str,
    fields: list[dict[str, object]],
    source_table: str,
) -> str:
    """Compile executable SQL from the fields in the registered requester queries."""
    source_table = _identifier(source_table)
    projections = ",\n".join(
        f'    "{_identifier(str(field["name"]))}"' for field in fields
    )
    return (
        f"-- Nullspace builder-agent output for demand: {want}\n"
        f"-- Requesters: {', '.join(requesters)}\n"
        f"-- Ghost URN: {ghost_urn}\n"
        "-- Generated from registered query contracts and a DataHub-returned source.\n\n"
        "select\n"
        f"{projections}\n"
        f"from {{{{ source('warehouse_source', '{source_table}') }}}}\n"
    )


def validate_model_sql(
    plan: BuildPlan, *, rendered_sql: str | None = None
) -> dict[str, Any]:
    """EXPLAIN and sample the generated model against the real warehouse."""
    import psycopg

    schema = _identifier(plan.source_schema)
    table = _identifier(plan.source_table)
    relation = f'"{schema}"."{table}"'
    macro = "{{ source('warehouse_source', '" + table + "') }}"
    executable_sql = (rendered_sql or plan.model_sql).replace(
        macro, relation
    ).strip().rstrip(";")
    if "{{" in executable_sql or "}}" in executable_sql:
        raise ValueError(
            "build refused: generated SQL contains unresolved dbt macros; "
            "shortfall is 1 executable model"
        )

    with psycopg.connect(settings().warehouse_dsn) as connection:
        with connection.cursor() as cursor:
            cursor.execute("EXPLAIN (FORMAT JSON) " + executable_sql)
            explain = cursor.fetchone()
            cursor.execute(
                "SELECT * FROM (" + executable_sql + ") AS nullspace_validation LIMIT 5"
            )
            sample = cursor.fetchall()
            columns = [column.name for column in cursor.description or []]
        connection.rollback()

    expected = [str(field["name"]) for field in plan.fields]
    missing = [field for field in expected if field not in columns]
    if missing:
        raise ValueError(
            f"build refused: warehouse returned columns {columns}; "
            f"shortfall is {len(missing)} demanded fields {missing}"
        )
    plan_root = explain[0][0]["Plan"] if explain else {}
    return {
        "status": "passed",
        "source_relation": f"{schema}.{table}",
        "returned_columns": columns,
        "sample_row_count": len(sample),
        "explain_node": plan_root.get("Node Type"),
    }


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


def _remote_with_token(remote: str, token: str | None) -> str:
    if not token or not remote.startswith("https://"):
        return remote
    # Avoid embedding credentials in logs; only used for git push env.
    rest = remote.removeprefix("https://")
    return f"https://x-access-token:{token}@{rest}"


def ensure_dbt_remote(repo: Path, remote: str, token: str | None) -> str:
    """Ensure origin exists; return the URL used for `git push`."""
    public = remote
    push_url = _remote_with_token(remote, token)
    existing = subprocess.run(
        ["git", "remote", "get-url", "origin"],
        cwd=repo,
        check=False,
        capture_output=True,
        text=True,
    )
    if existing.returncode != 0:
        subprocess.run(
            ["git", "remote", "add", "origin", public],
            cwd=repo,
            check=False,
            capture_output=True,
            text=True,
        )
    else:
        subprocess.run(
            ["git", "remote", "set-url", "origin", public],
            cwd=repo,
            check=False,
            capture_output=True,
            text=True,
        )
    return push_url


def create_change_reference(repo: Path, branch: str, title: str, model_path: Path) -> str:
    """Commit explicit dbt files; return a real PR URL only when one exists."""
    cfg = settings()
    subprocess.run(["git", "init"], cwd=repo, check=False, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "nullspace-builder@local"],
        cwd=repo,
        check=False,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "nullspace-builder"],
        cwd=repo,
        check=False,
        capture_output=True,
    )
    subprocess.run(
        ["git", "checkout", "-B", branch], cwd=repo, check=True, capture_output=True
    )
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
    push_url = ensure_dbt_remote(repo, cfg.dbt_remote, cfg.dbt_token)
    push_env = {**os.environ}
    if cfg.dbt_token:
        push_env["GH_TOKEN"] = cfg.dbt_token
        push_env["GITHUB_TOKEN"] = cfg.dbt_token
    push = subprocess.run(
        ["git", "push", push_url, f"HEAD:refs/heads/{branch}"],
        cwd=repo,
        check=False,
        capture_output=True,
        text=True,
        env=push_env,
    )
    if push.returncode == 0:
        pr = subprocess.run(
            [
                "gh",
                "pr",
                "create",
                "--repo",
                "Morkeeth/nullspace-dbt",
                "--title",
                title,
                "--body",
                (
                    "Opened by the Nullspace builder agent after warehouse SQL "
                    "validation. Merging this PR solidifies the ghost in DataHub."
                ),
                "--head",
                branch,
            ],
            cwd=repo,
            check=False,
            capture_output=True,
            text=True,
            env=push_env,
        )
        if pr.returncode == 0 and pr.stdout.strip():
            return pr.stdout.strip().splitlines()[-1]
    # Honest local change reference. This is not a pull request.
    return f"file://{repo.resolve()}#{branch}"


def merge_pull_request(pr_url: str) -> dict[str, Any]:
    """Merge an open GitHub PR. Returns gh's JSON view after merge."""
    cfg = settings()
    env = {**os.environ}
    if cfg.dbt_token:
        env["GH_TOKEN"] = cfg.dbt_token
        env["GITHUB_TOKEN"] = cfg.dbt_token
    merged = subprocess.run(
        ["gh", "pr", "merge", pr_url, "--merge", "--delete-branch"],
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )
    viewed = subprocess.run(
        ["gh", "pr", "view", pr_url, "--json", "state,url,mergedAt,title"],
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )
    payload: dict[str, Any]
    try:
        payload = json.loads(viewed.stdout or "{}")
    except json.JSONDecodeError:
        payload = {}
    payload["merge_ok"] = merged.returncode == 0
    payload["merge_stderr"] = (merged.stderr or "")[:500]
    return payload


def solidify_after_merge(
    ns: Nullspace,
    want: str,
    *,
    builder_id: str = "builder-1",
    merge: bool = True,
) -> Ghost:
    """Observe (and optionally perform) PR merge, then solidify the claimed ghost."""
    ghost = ns.store.get(want)
    if ghost is None:
        raise ValueError(f"finalize refused: no ghost exists for demand {want!r}")
    if not ghost.pr_url or not str(ghost.pr_url).startswith("https://github.com/"):
        raise ValueError(
            "finalize refused: ghost has no https://github.com PR URL; "
            "shortfall is write access to Morkeeth/nullspace-dbt (NULLSPACE_DBT_TOKEN)"
        )
    if merge:
        merge_view = merge_pull_request(ghost.pr_url)
        ns.record_resolution(
            want,
            agent_id=builder_id,
            event="pr_merged" if merge_view.get("state") == "MERGED" else "pr_merge_failed",
            detail=json.dumps(merge_view, sort_keys=True),
        )
        if merge_view.get("state") != "MERGED":
            raise RuntimeError(
                "finalize refused: PR did not reach MERGED; "
                f"returned {merge_view!r}"
            )
    else:
        env = {**os.environ}
        cfg = settings()
        if cfg.dbt_token:
            env["GH_TOKEN"] = cfg.dbt_token
        viewed = subprocess.run(
            ["gh", "pr", "view", ghost.pr_url, "--json", "state,url,mergedAt"],
            check=True,
            capture_output=True,
            text=True,
            env=env,
        )
        state = json.loads(viewed.stdout).get("state")
        if state != "MERGED":
            raise RuntimeError(
                f"finalize refused: PR state is {state!r}, expected MERGED"
            )
        ns.record_resolution(
            want,
            agent_id=builder_id,
            event="pr_merged",
            detail=viewed.stdout.strip(),
        )
    plan = plan_for_demand(want)
    return ns.solidify(
        want,
        schema_fields=plan.fields,
        upstream_urns=[plan.upstream_urn],
        schema_source=plan.schema_source,
    )


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
    try:
        validation = validate_model_sql(
            plan, rendered_sql=path.read_text(encoding="utf-8")
        )
    except Exception as exc:
        detail = f"{type(exc).__name__}: {str(exc)[:500]}"
        ns.record_resolution(
            want,
            agent_id=builder_id,
            event="sql_validation_failed",
            detail=detail,
        )
        raise ValueError(
            "build refused: generated SQL failed warehouse validation; "
            f"shortfall is 1 executable model; {detail}"
        ) from exc
    plan = replace(plan, validation=validation)
    save_agent_plan(want, plan)
    ns.record_resolution(
        want,
        agent_id=builder_id,
        event="sql_validated",
        detail=json.dumps(validation, sort_keys=True),
    )
    branch = f"nullspace/{ghost.dataset_name}"
    title = f"feat(nullspace): solidify {ghost.want}"
    pr_url = create_change_reference(repo, branch, title, path)
    ns.attach_pr(want, pr_url)
    ns.record_resolution(
        want,
        agent_id=builder_id,
        event="pr_opened" if pr_url.startswith("https://github.com/") else "change_reference",
        detail=pr_url,
    )
    # Real GitHub PR: leave claimed so merge is the solidify trigger.
    # Local file:// reference: solidify immediately — honest, no PR claimed.
    if pr_url.startswith("https://github.com/"):
        if cfg.auto_merge_pr:
            return solidify_after_merge(ns, want, builder_id=builder_id, merge=True)
        return ns.store.get(want) or ghost
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


def _write_review_receipt(
    *,
    want: str,
    reason: str,
    plan: BuildPlan,
    result: dict[str, Any],
) -> str:
    witness = DataHubClient().solid_witness(str(result["urn"]))
    properties = witness.get("properties") or {}
    receipt = {
        "outcome": result.get("status"),
        "want": want,
        "urn": result.get("urn"),
        "decision": reason,
        "generated_sql": plan.model_sql,
        "source_urn": plan.upstream_urn,
        "sql_validation": plan.validation,
        "datahub_returned": {
            "state": properties.get("nullspace.state"),
            "demand": properties.get("nullspace.demand"),
            "requesters": properties.get("nullspace.requesters"),
            "schemaMetadata": witness.get("schemaMetadata"),
            "lineage": witness.get("lineage"),
            "ownership": witness.get("ownership"),
            "tags": witness.get("tags"),
        },
        "change_reference": result.get("pr_url"),
        "honest_boundary": (
            "file:// is a local change reference, not a pull request"
            if str(result.get("pr_url", "")).startswith("file://")
            else None
        ),
    }
    _RECEIPT_PATH.parent.mkdir(parents=True, exist_ok=True)
    temp = _RECEIPT_PATH.with_suffix(f".{os.getpid()}.tmp")
    temp.write_text(json.dumps(receipt, indent=2), encoding="utf-8")
    os.replace(temp, _RECEIPT_PATH)
    return str(_RECEIPT_PATH)


def review_receipt(path: Path) -> dict[str, Any]:
    """Re-read DataHub and show whether the saved builder receipt still holds."""
    receipt = json.loads(path.read_text(encoding="utf-8"))
    returned_now = DataHubClient().solid_witness(str(receipt["urn"]))
    recorded = receipt["datahub_returned"]
    current_properties = returned_now.get("properties") or {}
    current = {
        "state": current_properties.get("nullspace.state"),
        "demand": current_properties.get("nullspace.demand"),
        "requesters": current_properties.get("nullspace.requesters"),
        "schemaMetadata": returned_now.get("schemaMetadata"),
        "lineage": returned_now.get("lineage"),
        "ownership": returned_now.get("ownership"),
        "tags": returned_now.get("tags"),
    }
    return {
        "receipt": str(path),
        "want": receipt["want"],
        "decision": receipt["decision"],
        "sql_validation": receipt["sql_validation"],
        "datahub_still_matches": current == recorded,
        "datahub_returned_now": current,
        "generated_sql": receipt["generated_sql"],
        "honest_boundary": receipt.get("honest_boundary"),
    }


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
        verified_plan = _load_agent_plan(want) or plan
        built["sql_validation"] = verified_plan.validation
        built["review_receipt"] = _write_review_receipt(
            want=want,
            reason=reason,
            plan=verified_plan,
            result=built,
        )
        return built


def main() -> None:
    parser = argparse.ArgumentParser(description="Nullspace autonomous builder agent")
    parser.add_argument(
        "--review",
        type=Path,
        metavar="RECEIPT",
        help="re-read DataHub and review a prior builder receipt",
    )
    args = parser.parse_args()
    if args.review:
        print(json.dumps(review_receipt(args.review), indent=2))
        return
    result = asyncio.run(run_builder_agent())
    print("RESULT:")
    print(json.dumps(result, indent=2))
    # claimed = real PR opened, waiting on merge → solidify
    if result.get("status") not in {"solidified", "declined", "claimed"}:
        # MCP tool historically stamps solidified; accept ghost.state too.
        if result.get("state") not in {"solid", "claimed"}:
            raise SystemExit(1)


if __name__ == "__main__":
    main()
