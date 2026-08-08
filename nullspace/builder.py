"""Builder agent: claim a ready ghost → write dbt model → change reference → solidify."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path

from nullspace.config import settings
from nullspace.ghosts import Ghost, Nullspace

DBT_MODEL = '''-- Nullspace-generated model for demand: {want}
-- Requesters: {requesters}
-- Ghost URN: {urn}
--
-- Columns below are the union of what the requesting agents asked for.
-- Source: nullspace/agents/contracts.py :: ContractStore.demanded_schema
-- This is a scaffold a human reviews and fills in, not a finished model.

select
{columns}
from {{{{ ref('stg_nullspace_source') }}}}
'''

REVENUE_DBT_MODEL = '''-- Nullspace-generated model for demand: {want}
-- Requesters: {requesters}
-- Ghost URN: {urn}
-- Schema source: union of fields declared by requester-agent contracts

select
    month,
    segment,
    sum(mrr)::double precision as mrr,
    sum(churned_mrr)::double precision as churned_mrr
from {{{{ source('ecommerce', 'revenue_events') }}}}
group by month, segment
'''


STG_MODEL = '''-- Seed staging model so the generated model can ref something real in CI/demo.
select * from {{{{ source('ecommerce', 'trials') }}}}
'''

SOURCES_YML = """version: 2
sources:
  - name: ecommerce
    schema: ecommerce
    tables:
      - name: trials
      - name: revenue_events
"""

SOLID_SCHEMA_FIELDS = [
    {"name": "cohort_id", "native_type": "VARCHAR", "nullable": False},
    {"name": "trials", "native_type": "BIGINT", "nullable": False},
    {"name": "conversions", "native_type": "BIGINT", "nullable": False},
    {"name": "trial_to_paid_rate", "native_type": "DOUBLE", "nullable": True},
]
FALLBACK_FIELDS = [str(field["name"]) for field in SOLID_SCHEMA_FIELDS]

REVENUE_FIELDS = {
    "month": {"name": "month", "native_type": "VARCHAR", "nullable": False},
    "segment": {"name": "segment", "native_type": "VARCHAR", "nullable": False},
    "mrr": {"name": "mrr", "native_type": "DOUBLE", "nullable": False},
    "churned_mrr": {
        "name": "churned_mrr",
        "native_type": "DOUBLE",
        "nullable": False,
    },
}

@dataclass(frozen=True)
class BuildPlan:
    fields: list[dict[str, object]]
    model_sql: str
    upstream_urn: str
    schema_source: str


def plan_for_demand(want: str) -> BuildPlan:
    """Use requester contracts when present; otherwise disclose the demo fallback."""
    from nullspace.agents.contracts import ContractStore

    cfg = settings()
    demanded = ContractStore().demanded_schema(want)
    if not demanded:
        return BuildPlan(
            fields=SOLID_SCHEMA_FIELDS,
            model_sql=DBT_MODEL,
            upstream_urn=cfg.warehouse_source_urn,
            schema_source=(
                "fallback demo contract: no requester query fields were registered"
            ),
        )

    unsupported = [field for field in demanded if field not in REVENUE_FIELDS]
    if unsupported:
        raise ValueError(
            "build refused: requester contract includes unsupported fields "
            f"{unsupported}; supported demo warehouse fields are "
            f"{sorted(REVENUE_FIELDS)}; shortfall is {len(unsupported)} field"
            f"{'s' if len(unsupported) != 1 else ''}"
        )
    return BuildPlan(
        fields=[REVENUE_FIELDS[field] for field in demanded],
        model_sql=REVENUE_DBT_MODEL,
        upstream_urn=cfg.revenue_source_urn,
        schema_source="requester contracts: union of declared query fields",
    )


def write_dbt_model(ghost: Ghost, repo: Path, model_sql: str) -> Path:
    models = repo / "models"
    models.mkdir(parents=True, exist_ok=True)
    stg = models / "stg_trials.sql"
    stg.write_text(STG_MODEL, encoding="utf-8")
    sources = models / "sources.yml"
    sources.write_text(SOURCES_YML, encoding="utf-8")
    out = models / f"{ghost.dataset_name}.sql"
    out.write_text(
        model_sql.format(
            want=ghost.want,
            requesters=", ".join(ghost.requesters),
            urn=ghost.urn,
        ),
        encoding="utf-8",
    )
    return out


def create_change_reference(repo: Path, branch: str, title: str, model_path: Path) -> str:
    """Commit explicit dbt files; return a real PR URL only when one exists."""
    subprocess.run(["git", "init"], cwd=repo, check=False, capture_output=True)
    subprocess.run(["git", "checkout", "-B", branch], cwd=repo, check=True, capture_output=True)
    explicit_paths = [
        "dbt_project.yml",
        "models/stg_trials.sql",
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
    path = write_dbt_model(ghost, repo, plan.model_sql)
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
