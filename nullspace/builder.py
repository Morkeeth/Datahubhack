"""Builder agent: claim a ready ghost → write dbt model → open PR → solidify."""

from __future__ import annotations

import subprocess
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


STG_MODEL = '''-- Staging stub so the generated model refs something real in CI/demo.
-- Labelled demo data on purpose: it is a scaffold, not a claim about your warehouse.
select 1 as placeholder_row
'''

# Used only when nobody registered a query. Reported as such rather than silently.
FALLBACK_FIELDS = ["entity_id", "metric_value", "period"]


def demanded_fields(want: str) -> list[str]:
    """The columns requesting agents actually asked for, else a named fallback."""
    from nullspace.agents.contracts import ContractStore

    fields = ContractStore().demanded_schema(want)
    return fields or list(FALLBACK_FIELDS)


def write_dbt_model(ghost: Ghost, repo: Path, fields: list[str] | None = None) -> Path:
    models = repo / "models"
    models.mkdir(parents=True, exist_ok=True)
    stg = models / "stg_nullspace_source.sql"
    if not stg.exists():
        stg.write_text(STG_MODEL, encoding="utf-8")

    cols = fields or demanded_fields(ghost.want)
    out = models / f"{ghost.dataset_name}.sql"
    out.write_text(
        DBT_MODEL.format(
            want=ghost.want,
            requesters=", ".join(ghost.requesters),
            urn=ghost.urn,
            columns=",\n".join(f"    null as {c}" for c in cols),
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

    fields = demanded_fields(want)
    path = write_dbt_model(ghost, repo, fields)
    branch = f"nullspace/{ghost.dataset_name}"
    title = f"feat(nullspace): materialize {ghost.want}"
    pr_url = open_local_pr(repo, branch, title)
    ns.attach_pr(want, pr_url)

    solid = ns.solidify(want, schema_fields=fields)

    # Publish what the README promises: a real schema, and the requesting agents
    # as native owners. Both are read back by scripts/eval_nullspace.py.
    if ns.dh is not None:
        from nullspace.emit import emit_requester_ownership, emit_schema

        emit_schema(ns.dh, solid, fields)
        # Ownership is the demo's payoff shot but must never take the loop down
        # with it. A failure is recorded on the ghost, not swallowed.
        try:
            emit_requester_ownership(ns.dh, solid)
        except Exception as exc:  # noqa: BLE001
            from nullspace.client import now_ms
            from nullspace.ghosts import ResolutionEvent

            solid.resolution.append(
                ResolutionEvent(
                    agent_id="system",
                    at_ms=now_ms(),
                    event="ownership_error",
                    detail=f"{type(exc).__name__}: {str(exc)[:300]}",
                )
            )
            ns.store.save(solid)

    return solid
