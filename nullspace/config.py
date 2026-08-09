from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    gms_url: str = os.getenv("DATAHUB_GMS_URL", "http://localhost:8080")
    token: str | None = os.getenv("DATAHUB_GMS_TOKEN") or None
    demand_threshold: int = int(os.getenv("NULLSPACE_DEMAND_THRESHOLD", "3"))
    board_host: str = os.getenv("NULLSPACE_BOARD_HOST", "0.0.0.0")
    board_port: int = int(os.getenv("NULLSPACE_BOARD_PORT", "8787"))
    dbt_repo_path: str = os.getenv(
        "NULLSPACE_DBT_REPO",
        os.path.join(os.path.dirname(__file__), "..", "dbt_project"),
    )
    # Public fulfillment repo (D9 — ruled YES). Models arrive only via PR.
    dbt_remote: str = os.getenv(
        "NULLSPACE_DBT_REMOTE",
        "https://github.com/Morkeeth/nullspace-dbt",
    )
    dbt_pr_base: str = os.getenv("NULLSPACE_DBT_PR_BASE", "main")
    dbt_repo_slug: str = os.getenv("NULLSPACE_DBT_REPO_SLUG", "Morkeeth/nullspace-dbt")
    dbt_token: str | None = (
        os.getenv("NULLSPACE_DBT_TOKEN")
        or os.getenv("GH_TOKEN")
        or os.getenv("GITHUB_TOKEN")
        or None
    )
    # When a real PR opens, leave the ghost claimed until merge unless true.
    auto_merge_pr: bool = os.getenv("NULLSPACE_AUTO_MERGE_PR", "0") in {
        "1",
        "true",
        "TRUE",
        "yes",
    }
    # Asset the demo agents ask for (must miss on a fresh catalog)
    demo_asset_name: str = os.getenv(
        "NULLSPACE_DEMO_ASSET", "trial_to_paid_conversion_by_cohort"
    )
    warehouse_source_urn: str = os.getenv(
        "NULLSPACE_WAREHOUSE_SOURCE_URN",
        (
            "urn:li:dataset:(urn:li:dataPlatform:postgres,"
            "local-warehouse.warehouse.ecommerce.trials,DEV)"
        ),
    )
    revenue_source_urn: str = os.getenv(
        "NULLSPACE_REVENUE_SOURCE_URN",
        (
            "urn:li:dataset:(urn:li:dataPlatform:postgres,"
            "local-warehouse.warehouse.ecommerce.revenue_events,DEV)"
        ),
    )
    warehouse_dsn: str = os.getenv(
        "NULLSPACE_WAREHOUSE_DSN",
        "postgresql://agent:agent@localhost:5432/warehouse",
    )


def settings() -> Settings:
    return Settings()
