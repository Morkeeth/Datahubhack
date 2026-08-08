"""Builder agent: claim a ready ghost → write dbt model → open PR → solidify."""

from __future__ import annotations

import subprocess
from pathlib import Path

from nullspace.config import settings
from nullspace.ghosts import Ghost, Nullspace


DBT_MODEL = '''-- Nullspace-generated model for demand: {want}
-- Requesters: {requesters}
-- Ghost URN: {urn}

with base as (
    select
        cohort_id,
        trial_started_at,
        converted_at,
        case when converted_at is not null then 1 else 0 end as converted
    from {{{{ ref('stg_trials') }}}}
)

select
    cohort_id,
    count(*) as trials,
    sum(converted) as conversions,
    sum(converted)::float / nullif(count(*), 0) as trial_to_paid_rate
from base
group by 1
'''


STG_MODEL = '''-- Seed staging model so the generated model can ref something real in CI/demo.
select
    '2026-q1'::varchar as cohort_id,
    '2026-01-01'::timestamp as trial_started_at,
    '2026-01-20'::timestamp as converted_at
union all
select
    '2026-q1',
    '2026-01-03'::timestamp,
    null::timestamp
'''


def write_dbt_model(ghost: Ghost, repo: Path) -> Path:
    models = repo / "models"
    models.mkdir(parents=True, exist_ok=True)
    stg = models / "stg_trials.sql"
    if not stg.exists():
        stg.write_text(STG_MODEL, encoding="utf-8")
    out = models / f"{ghost.dataset_name}.sql"
    out.write_text(
        DBT_MODEL.format(
            want=ghost.want,
            requesters=", ".join(ghost.requesters),
            urn=ghost.urn,
        ),
        encoding="utf-8",
    )
    return out


def open_local_pr(repo: Path, branch: str, title: str) -> str:
    """Create a local branch + commit. Returns a file:// PR surrogate or gh URL."""
    subprocess.run(["git", "init"], cwd=repo, check=False, capture_output=True)
    subprocess.run(["git", "checkout", "-B", branch], cwd=repo, check=True, capture_output=True)
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True, capture_output=True)
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
            capture_output=True,
            text=True,
        )
        if pr.returncode == 0 and pr.stdout.strip():
            return pr.stdout.strip().splitlines()[-1]
    # Local surrogate that still proves a mergeable artifact exists
    return f"file://{repo.resolve()}#{branch}"


def build_and_solidify(ns: Nullspace, want: str, *, builder_id: str = "builder-1") -> Ghost:
    cfg = settings()
    repo = Path(cfg.dbt_repo_path).resolve()
    repo.mkdir(parents=True, exist_ok=True)
    if not (repo / "dbt_project.yml").exists():
        (repo / "dbt_project.yml").write_text(
            "name: nullspace_fulfillment\nversion: '1.0.0'\nprofile: nullspace\n"
            "model-paths: ['models']\n",
            encoding="utf-8",
        )

    ghost = ns.claim(want, builder_id)
    path = write_dbt_model(ghost, repo)
    branch = f"nullspace/{ghost.dataset_name}"
    title = f"feat(nullspace): materialize {ghost.want}"
    pr_url = open_local_pr(repo, branch, title)
    ns.attach_pr(want, pr_url)
    # Demo treats successful PR open as merge for the solidify beat;
    # a hosted run can swap this for a real merge webhook later.
    return ns.solidify(
        want,
        schema_fields=["cohort_id", "trials", "conversions", "trial_to_paid_rate"],
    )
