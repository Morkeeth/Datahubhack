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
