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
    upstream_urns: tuple[str, ...] = ()
    source_tables: tuple[str, ...] = ()
    generation_tier: str = "deterministic"
    pr_body: str = ""
    grain_reason: str = ""

    def all_upstreams(self) -> list[str]:
        if self.upstream_urns:
            return list(self.upstream_urns)
        return [self.upstream_urn]

    def all_tables(self) -> list[str]:
        if self.source_tables:
            return list(self.source_tables)
        return [self.source_table]


def _plan_key(want: str) -> str:
    return want.strip().lower()


def save_agent_plan(
    want: str, plan: BuildPlan, *, dh: DataHubClient | None = None
) -> None:
    """Persist the builder plan on the ghost URN (catalog SoT) + optional file cache."""
    payload = asdict(plan)
    client = dh
    if client is None:
        try:
            probe = DataHubClient()
            client = probe if probe.healthy() else None
        except Exception:  # noqa: BLE001
            client = None
    if client is not None:
        from datahub.metadata.schema_classes import DatasetPropertiesClass
        from nullspace.urns import ghost_urn

        urn = ghost_urn(want)
        props = client.graph.get_aspect(urn, DatasetPropertiesClass)
        if props is not None:
            custom = dict(props.customProperties or {})
            custom["nullspace.builder_plan"] = json.dumps(payload, sort_keys=True)
            client.emit_aspect(
                urn,
                DatasetPropertiesClass(
                    name=props.name,
                    description=props.description,
                    customProperties=custom,
                ),
            )
            read_back = client.dataset_custom_properties(urn).get(
                "nullspace.builder_plan"
            )
            if read_back != custom["nullspace.builder_plan"]:
                raise RuntimeError(
                    "DataHub builder_plan read-after-write failed for "
                    f"{urn!r}"
                )

    # Write-through cache only — deleting it must not lose the plan.
    data: dict[str, Any] = {}
    if _PLAN_STORE.exists():
        try:
            data = json.loads(_PLAN_STORE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            data = {}
    data[_plan_key(want)] = payload
    _PLAN_STORE.parent.mkdir(parents=True, exist_ok=True)
    temp = _PLAN_STORE.with_suffix(f".{os.getpid()}.tmp")
    temp.write_text(json.dumps(data, indent=2), encoding="utf-8")
    os.replace(temp, _PLAN_STORE)


def _load_agent_plan(
    want: str, *, dh: DataHubClient | None = None
) -> BuildPlan | None:
    client = dh
    if client is None:
        try:
            probe = DataHubClient()
            client = probe if probe.healthy() else None
        except Exception:  # noqa: BLE001
            client = None
    if client is not None:
        from nullspace.urns import ghost_urn

        props = client.dataset_custom_properties(ghost_urn(want))
        raw_plan = props.get("nullspace.builder_plan")
        if raw_plan:
            try:
                raw = json.loads(raw_plan)
                if isinstance(raw.get("upstream_urns"), list):
                    raw["upstream_urns"] = tuple(raw["upstream_urns"])
                if isinstance(raw.get("source_tables"), list):
                    raw["source_tables"] = tuple(raw["source_tables"])
                return BuildPlan(**raw)
            except (TypeError, ValueError, json.JSONDecodeError):
                pass

    if not _PLAN_STORE.exists():
        return None
    try:
        raw = json.loads(_PLAN_STORE.read_text(encoding="utf-8")).get(_plan_key(want))
    except (json.JSONDecodeError, OSError):
        return None
    if not raw:
        return None
    if isinstance(raw.get("upstream_urns"), list):
        raw["upstream_urns"] = tuple(raw["upstream_urns"])
    if isinstance(raw.get("source_tables"), list):
        raw["source_tables"] = tuple(raw["source_tables"])
    return BuildPlan(**raw)


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
    """Backward-compatible wrapper — prefers the grain-aware planner."""
    from nullspace.sqlgen import build_sql_plan

    demanded = [str(field["name"]) for field in fields]
    # Minimal warehouse view when called without DataHub (unit/offline).
    datasets = [
        {
            "urn": (
                "urn:li:dataset:(urn:li:dataPlatform:postgres,"
                f"local-warehouse.warehouse.ecommerce.{source_table},DEV)"
            ),
            "fields": list(fields),
        }
    ]
    plan = build_sql_plan(
        want=want,
        requesters=requesters,
        ghost_urn=ghost_urn,
        demanded_fields=demanded,
        queries=[],
        warehouse_datasets=datasets,
        generation_tier="deterministic",
    )
    return plan.model_sql


def compile_agent_plan(
    *,
    want: str,
    requesters: list[str],
    ghost_urn: str,
    demanded_fields: list[str],
    queries: list[dict[str, Any]],
    decision_reason: str,
) -> BuildPlan:
    """Plan SQL with disclosed tier (API → claude CLI → deterministic)."""
    from nullspace.sqlgen import try_llm_tiers

    dh = DataHubClient()
    warehouse = dh.list_warehouse_datasets() if dh.healthy() else []
    sql_plan = try_llm_tiers(
        want=want,
        requesters=requesters,
        ghost_urn=ghost_urn,
        demanded_fields=demanded_fields,
        queries=queries,
        warehouse_datasets=warehouse,
    )
    primary = sql_plan.source_tables[0]
    return BuildPlan(
        fields=sql_plan.fields,
        model_sql=sql_plan.model_sql,
        upstream_urn=sql_plan.upstream_urns[0],
        schema_source=(
            f"builder agent ({sql_plan.generation_tier}): registered queries + "
            "DataHub-returned warehouse schema + grain planner"
        ),
        source_schema=sql_plan.source_schema,
        source_table=primary,
        decision_reason=decision_reason,
        upstream_urns=tuple(sql_plan.upstream_urns),
        source_tables=tuple(sql_plan.source_tables),
        generation_tier=sql_plan.generation_tier,
        pr_body=sql_plan.pr_body,
        grain_reason=sql_plan.grain_reason,
    )


def validate_model_sql(
    plan: BuildPlan, *, rendered_sql: str | None = None
) -> dict[str, Any]:
    """EXPLAIN and sample the generated model against the real warehouse."""
    import psycopg

    schema = _identifier(plan.source_schema)
    executable_sql = rendered_sql or plan.model_sql
    for table in plan.all_tables():
        safe = _identifier(table)
        relation = f'"{schema}"."{safe}"'
        macro = "{{ source('warehouse_source', '" + safe + "') }}"
        executable_sql = executable_sql.replace(macro, relation)
    executable_sql = executable_sql.strip().rstrip(";")
    if "{{" in executable_sql or "}}" in executable_sql:
        raise ValueError(
            "build refused: generated SQL contains unresolved dbt macros; "
            "shortfall is 1 executable model"
        )
    # Passthrough guard: fulfilment must change grain.
    lowered = executable_sql.lower()
    if "group by" not in lowered and " join " not in lowered:
        raise ValueError(
            "build refused: SQL has neither GROUP BY nor JOIN; "
            "shortfall is 1 grain-changing transform (passthrough is not fulfilment)"
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
        "source_relation": ", ".join(
            f"{schema}.{_identifier(table)}" for table in plan.all_tables()
        ),
        "returned_columns": columns,
        "sample_row_count": len(sample),
        "explain_node": plan_root.get("Node Type"),
        "generation_tier": plan.generation_tier,
        "grain_reason": plan.grain_reason,
        "upstream_count": len(plan.all_upstreams()),
    }


def plan_for_demand(want: str, ns: Nullspace | None = None) -> BuildPlan:
    """Use a real builder-agent plan, otherwise an explicitly disclosed fallback."""
    agent_plan = _load_agent_plan(want, dh=ns.dh if ns is not None else None)
    if agent_plan is not None:
        return agent_plan

    demanded: list[str] = []
    if ns is not None:
        demanded = ns.demanded_schema_from_catalog(want)
    if not demanded:
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
    table_lines = "".join(f"      - name: {table}\n" for table in plan.all_tables())
    sources.write_text(
        "version: 2\n"
        "sources:\n"
        "  - name: warehouse_source\n"
        f"    schema: {plan.source_schema}\n"
        "    tables:\n"
        f"{table_lines}",
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


def _normalize_remote(remote: str) -> str:
    remote = remote.strip()
    if remote.endswith(".git"):
        remote = remote[: -len(".git")]
    return remote


def _gh_env(token: str | None) -> dict[str, str]:
    env = {**os.environ}
    if token:
        env["GH_TOKEN"] = token
        env["GITHUB_TOKEN"] = token
    return env


def _last_change_ref_error(detail: str) -> None:
    """Persist the most recent push/PR failure for receipts and STATE."""
    path = Path(
        os.getenv("NULLSPACE_DBT_LAST_ERROR", "/tmp/nullspace-dbt-last-error.txt")
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(detail[:2000], encoding="utf-8")


def create_change_reference(
    repo: Path,
    branch: str,
    title: str,
    model_path: Path,
    *,
    body: str | None = None,
) -> str:
    """Open a real PR against nullspace-dbt main; else honest file:// reference.

    D9: main stays hollow (no ghost_* models). Every model arrives via PR.
    Push uses the authenticated `gh` CLI / GH_TOKEN on this machine.
    """
    cfg = settings()
    remote = _normalize_remote(cfg.dbt_remote)
    base = cfg.dbt_pr_base or "main"
    slug = cfg.dbt_repo_slug
    env = _gh_env(cfg.dbt_token)
    pr_body = body or (
        "Opened by the Nullspace builder agent after warehouse SQL validation.\n\n"
        "Merging this PR is the solidify trigger."
    )

    # Keep a local working copy for warehouse validation / board demos.
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
    # Only stage paths that exist (sources.yml may be absent on hollow main).
    existing_paths = [p for p in explicit_paths if (repo / p).exists()]
    subprocess.run(
        ["git", "add", "--", *existing_paths],
        cwd=repo,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "commit", "-m", title],
        cwd=repo,
        check=False,
        capture_output=True,
    )

    # Publish from a fresh clone of hollow main so history matches the remote.
    work = Path(
        os.getenv("NULLSPACE_DBT_WORKTREE", f"/tmp/nullspace-dbt-pr-{os.getpid()}")
    )
    if work.exists():
        subprocess.run(["rm", "-rf", str(work)], check=False)
    clone = subprocess.run(
        ["gh", "repo", "clone", slug, str(work), "--", "--depth", "1", "--branch", base],
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )
    if clone.returncode != 0:
        detail = (
            f"clone failed for {slug}@{base}: "
            f"{(clone.stderr or clone.stdout or '')[:500]}"
        )
        _last_change_ref_error(detail)
        return f"file://{repo.resolve()}#{branch}"

    subprocess.run(
        ["git", "checkout", "-B", branch],
        cwd=work,
        check=True,
        capture_output=True,
        env=env,
    )
    subprocess.run(
        ["git", "config", "user.email", "nullspace-builder@local"],
        cwd=work,
        check=False,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "nullspace-builder"],
        cwd=work,
        check=False,
        capture_output=True,
    )
    (work / "models").mkdir(parents=True, exist_ok=True)
    for rel in existing_paths:
        src = repo / rel
        dest = work / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(src.read_bytes())
    subprocess.run(
        ["git", "add", "--", *existing_paths],
        cwd=work,
        check=True,
        capture_output=True,
        env=env,
    )
    commit = subprocess.run(
        ["git", "commit", "-m", title],
        cwd=work,
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )
    if commit.returncode != 0 and "nothing to commit" in (commit.stdout + commit.stderr):
        detail = f"commit refused: nothing to commit on {branch}"
        _last_change_ref_error(detail)
        return f"file://{repo.resolve()}#{branch}"

    # Prefer gh-authenticated push (handoff §D9); fall back to token URL.
    push = subprocess.run(
        ["git", "push", "-u", "origin", f"HEAD:refs/heads/{branch}"],
        cwd=work,
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )
    if push.returncode != 0:
        detail = (
            f"git push to {slug} failed: {(push.stderr or push.stdout or '')[:700]}"
        )
        _last_change_ref_error(detail)
        return f"file://{repo.resolve()}#{branch}"

    pr = subprocess.run(
        [
            "gh",
            "pr",
            "create",
            "--repo",
            slug,
            "--base",
            base,
            "--head",
            branch,
            "--title",
            title,
            "--body",
            pr_body + f"\n\nRemote: {remote} (base `{base}`).\n",
        ],
        cwd=work,
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )
    if pr.returncode == 0 and pr.stdout.strip():
        return pr.stdout.strip().splitlines()[-1]

    detail = f"gh pr create failed: {(pr.stderr or pr.stdout or '')[:700]}"
    _last_change_ref_error(detail)
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
    if ns.dh is not None:
        ns.hydrate(replace=False)
    ghost = ns.store.get(want) or ns._from_datahub(want)
    if ghost is None:
        raise ValueError(f"finalize refused: no ghost exists for demand {want!r}")
    if ghost.urn and ns.store.get(want) is None:
        ns.store.save(ghost)
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
    agent_plan = _load_agent_plan(want, dh=ns.dh)
    if agent_plan is not None:
        plan = agent_plan
    else:
        demanded = ns.demanded_schema_from_catalog(want)
        if not demanded:
            raise ValueError(
                "finalize refused: no builder plan and no catalog contracts; "
                "shortfall is demanded fields on the ghost URN"
            )
        plan = compile_agent_plan(
            want=want,
            requesters=list(ghost.requesters),
            ghost_urn=ghost.urn,
            demanded_fields=demanded,
            queries=ns.contracts_for(want),
            decision_reason="finalize after merge: compile from catalog contracts",
        )
    return ns.solidify(
        want,
        schema_fields=plan.fields,
        upstream_urns=plan.all_upstreams(),
        schema_source=plan.schema_source,
    )


def build_and_solidify(ns: Nullspace, want: str, *, builder_id: str = "builder-1") -> Ghost:
    # Catalog is SoT — survive deletion of /tmp mid-flight by rehydrating first.
    if ns.dh is not None:
        ns.hydrate(replace=False)
    cfg = settings()
    plan = plan_for_demand(want, ns=ns)
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
        # Do not strand the ghost in `claimed` — half-up warehouse / bad SQL
        # must leave demand open for retry (redteam WEAPON 2).
        ns.release_claim(
            want,
            builder_id=builder_id,
            detail=f"sql_validation_failed: {detail}",
        )
        raise ValueError(
            "build refused: generated SQL failed warehouse validation; "
            f"shortfall is 1 executable model; {detail}"
        ) from exc
    plan = replace(plan, validation=validation)
    save_agent_plan(want, plan, dh=ns.dh)
    ns.record_resolution(
        want,
        agent_id=builder_id,
        event="sql_validated",
        detail=json.dumps(validation, sort_keys=True),
    )
    branch = f"nullspace/{ghost.dataset_name}"
    title = f"feat(nullspace): solidify {ghost.want}"
    pr_url = create_change_reference(
        repo, branch, title, path, body=plan.pr_body or None
    )
    ns.attach_pr(want, pr_url)
    if pr_url.startswith("https://github.com/"):
        ns.record_resolution(
            want,
            agent_id=builder_id,
            event="pr_opened",
            detail=pr_url,
        )
    else:
        err_path = Path(
            os.getenv("NULLSPACE_DBT_LAST_ERROR", "/tmp/nullspace-dbt-last-error.txt")
        )
        err = err_path.read_text(encoding="utf-8") if err_path.exists() else ""
        ns.record_resolution(
            want,
            agent_id=builder_id,
            event="change_reference",
            detail=json.dumps({"pr_url": pr_url, "push_error": err[:700]}, sort_keys=True),
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
        upstream_urns=plan.all_upstreams(),
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
    plan: BuildPlan | None,
    result: dict[str, Any],
) -> str:
    """Persist a review receipt. Refusals must not raise — they *are* the result."""
    status = str(result.get("status") or "")
    urn = result.get("urn")
    receipt: dict[str, Any] = {
        "outcome": status,
        "want": want,
        "decision": reason,
        "host": os.uname().nodename if hasattr(os, "uname") else "unknown",
        "generation_tier": getattr(plan, "generation_tier", None),
        "grain_reason": getattr(plan, "grain_reason", None),
        "generated_sql": getattr(plan, "model_sql", None),
        "change_reference": result.get("pr_url"),
    }
    if status in {"declined", "refused", "error"} or not urn:
        receipt["refusal"] = result.get("reason") or reason
        receipt["datahub_returned"] = None
        receipt["honest_boundary"] = "refusal stated; no solid asset to witness"
    else:
        witness = DataHubClient().solid_witness(str(urn))
        properties = witness.get("properties") or {}
        receipt.update(
            {
                "urn": urn,
                "source_urn": getattr(plan, "upstream_urn", None),
                "upstream_urns": list(getattr(plan, "all_upstreams", lambda: [])()),
                "sql_validation": getattr(plan, "validation", None),
                "datahub_returned": {
                    "state": properties.get("nullspace.state"),
                    "demand": properties.get("nullspace.demand"),
                    "requesters": properties.get("nullspace.requesters"),
                    "schemaMetadata": witness.get("schemaMetadata"),
                    "lineage": witness.get("lineage"),
                    "ownership": witness.get("ownership"),
                    "tags": witness.get("tags"),
                },
                "honest_boundary": (
                    "file:// is a local change reference, not a pull request"
                    if str(result.get("pr_url", "")).startswith("file://")
                    else None
                ),
            }
        )
    _RECEIPT_PATH.parent.mkdir(parents=True, exist_ok=True)
    temp = _RECEIPT_PATH.with_suffix(f".{os.getpid()}.tmp")
    temp.write_text(json.dumps(receipt, indent=2), encoding="utf-8")
    os.replace(temp, _RECEIPT_PATH)
    return str(_RECEIPT_PATH)


def review_receipt(path: Path) -> dict[str, Any]:
    """Re-read DataHub and show whether the saved builder receipt still holds."""
    receipt = json.loads(path.read_text(encoding="utf-8"))
    if not receipt.get("urn") or receipt.get("datahub_returned") is None:
        return {
            "receipt": str(path),
            "want": receipt.get("want"),
            "decision": receipt.get("decision"),
            "refusal": receipt.get("refusal"),
            "datahub_still_matches": False,
            "generated_sql": receipt.get("generated_sql"),
            "honest_boundary": receipt.get("honest_boundary"),
        }
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
        "sql_validation": receipt.get("sql_validation"),
        "datahub_still_matches": current == recorded,
        "datahub_returned_now": current,
        "generated_sql": receipt.get("generated_sql"),
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
        queries = list(contract.get("queries") or [])
        if not fields or not queries:
            reason = (
                f"declined: {want!r} has {len(queries)} registered queries and "
                f"{len(fields)} demanded fields; at least 1 of each is required"
            )
            print(f"DECISION: {reason}")
            declined = {"status": "declined", "reason": reason}
            declined["review_receipt"] = _write_review_receipt(
                want=want, reason=reason, plan=None, result=declined
            )
            return declined

        try:
            plan = compile_agent_plan(
                want=want,
                requesters=list(choice.get("requesters", [])),
                ghost_urn=str(choice["urn"]),
                demanded_fields=fields,
                queries=queries,
                decision_reason=reason,
            )
        except ValueError as exc:
            reason = str(exc)
            print(f"DECISION: {reason}")
            declined = {"status": "declined", "reason": reason}
            declined["review_receipt"] = _write_review_receipt(
                want=want, reason=reason, plan=None, result=declined
            )
            return declined

        save_agent_plan(want, plan, dh=DataHubClient())
        print(f"GENERATION TIER: {plan.generation_tier}")
        print(f"GRAIN: {plan.grain_reason}")
        print("GENERATED SQL:")
        print(plan.model_sql)

        built = _tool_json(
            await session.call_tool("claim_and_build", {"want": want})
        )
        built["decision_reason"] = reason
        built["generated_sql"] = plan.model_sql
        built["source_urn"] = plan.upstream_urn
        built["upstream_urns"] = plan.all_upstreams()
        built["generation_tier"] = plan.generation_tier
        built["grain_reason"] = plan.grain_reason
        verified_plan = _load_agent_plan(want, dh=DataHubClient()) or plan
        # BUG-1: never KeyError on refusal — receipt must carry the reason.
        if built.get("status") in {"declined", "refused", "error"} or not built.get(
            "urn"
        ):
            built.setdefault("status", "refused")
            built.setdefault(
                "reason",
                built.get("reason")
                or built.get("detail")
                or "build refused without urn",
            )
            print(f"REFUSAL: {built['reason']}")
        built["review_receipt"] = _write_review_receipt(
            want=want,
            reason=reason if built.get("status") not in {"declined", "refused"} else str(
                built.get("reason") or reason
            ),
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
