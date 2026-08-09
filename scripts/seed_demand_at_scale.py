"""Generate a week of realistic warehouse traffic, so the order book has a shape.

Three agents asking for one table proves the mechanism. It does not show what
the mechanism is *for*, which is the moment a data platform team looks at a
ranked list of what their consumers could not get and recognises their own
backlog in it.

**What is real here and what is not, stated plainly.** The table names, the
services and the queries below are demo traffic — invented, and disclosed as
invented everywhere they are shown. Everything downstream of them is real: every
query is executed against the live Postgres warehouse, every error is a genuine
`relation ... does not exist` raised by Postgres, every log line is written by
Postgres itself, and the harvester reads that log with no knowledge that this
script exists. Nothing is injected into Nullspace directly. If the parser is
wrong, this produces nothing.

Attribution comes from the server's own log prefix. Set it once:

    ALTER SYSTEM SET log_line_prefix = '%m [%p] [app=%a] ';
    SELECT pg_reload_conf();

and every miss is attributable to the service that made it, with no change to
the services themselves. That is the whole adoption story in one config line.

Usage:
    python scripts/seed_demand_at_scale.py --container datahub-hack-warehouse-1
    docker logs datahub-hack-warehouse-1 2>&1 | python -m nullspace.agents.harvest --stdin

LANE B (Claude).
"""

from __future__ import annotations

import argparse
import random
import subprocess
import sys

# Services a mid-size company actually runs. The mix matters: dashboards and
# scheduled jobs ask repeatedly, one-off notebooks ask once, and that difference
# is what makes a demand ranking mean anything.
SERVICES = [
    ("revenue-copilot", 9), ("finance-agent", 8), ("board-deck-writer", 7),
    ("churn-analyst", 8), ("cfo-copilot", 6), ("sales-ops-agent", 7),
    ("forecast-bot", 6), ("support-triage-agent", 6), ("cs-forecast-agent", 5),
    ("growth-experiments", 5), ("pricing-analyst", 4), ("exec-dashboard", 6),
    ("weekly-business-review", 5), ("marketing-attribution", 5),
    ("lifecycle-email-agent", 4), ("product-analytics", 6), ("onboarding-funnel", 4),
    ("partner-reporting", 3), ("compliance-export", 2), ("data-science-notebook", 3),
    ("ml-feature-builder", 4), ("anomaly-watch", 3), ("investor-update-agent", 2),
    ("account-health-bot", 5),
]

# Wants, with the columns a service would actually select. Weight is roughly how
# central the metric is to a SaaS business, which is what produces a long tail
# rather than a flat list.
WANTS = [
    ("net_revenue_retention_by_cohort", ["cohort", "nrr", "period", "expansion_mrr"], 10),
    ("monthly_active_users_by_plan", ["plan", "month", "mau"], 9),
    ("churn_by_cohort", ["cohort", "churn_rate", "month", "retained_accounts"], 9),
    ("customer_health_score_by_account", ["account_id", "health_score", "arr", "last_login"], 8),
    ("pipeline_coverage_by_rep", ["rep_id", "pipeline_value", "quota", "coverage_ratio"], 8),
    ("support_ticket_volume_by_product_area", ["product_area", "tickets", "sla_breaches"], 7),
    ("trial_to_paid_conversion_by_source", ["source", "trials", "conversions", "rate"], 7),
    ("expansion_revenue_by_segment", ["segment", "expansion_mrr", "month"], 6),
    ("feature_adoption_by_account", ["account_id", "feature", "first_used_at"], 6),
    ("weekly_active_teams_by_plan_tier", ["plan_tier", "week", "active_teams"], 6),
    ("cac_payback_by_channel", ["channel", "cac", "payback_months"], 5),
    ("seat_utilisation_by_account", ["account_id", "seats_purchased", "seats_active"], 5),
    ("onboarding_completion_by_week", ["week", "started", "completed"], 5),
    ("gross_margin_by_product", ["product", "revenue", "cogs", "margin"], 5),
    ("lead_response_time_by_rep", ["rep_id", "median_minutes"], 4),
    ("nps_by_segment", ["segment", "nps", "responses"], 4),
    ("failed_payments_by_reason", ["reason", "attempts", "recovered"], 4),
    ("api_usage_by_customer", ["account_id", "calls", "month"], 4),
    ("time_to_first_value_by_plan", ["plan", "median_days"], 4),
    ("win_rate_by_competitor", ["competitor", "deals", "won", "win_rate"], 3),
    ("discount_depth_by_segment", ["segment", "avg_discount"], 3),
    ("support_csat_by_agent", ["agent_id", "csat", "tickets"], 3),
    ("expansion_pipeline_by_owner", ["owner", "open_expansion_arr"], 3),
    ("usage_anomalies_by_account", ["account_id", "metric", "z_score"], 3),
    ("renewal_risk_by_account", ["account_id", "risk_score", "renewal_date"], 4),
    ("marketing_qualified_leads_by_campaign", ["campaign", "mqls", "spend"], 3),
    ("product_qualified_leads_by_signal", ["signal", "pqls"], 2),
    ("invoice_aging_by_customer", ["account_id", "days_outstanding", "amount"], 3),
    ("expansion_by_feature_usage", ["feature", "accounts", "expansion_arr"], 2),
    ("logo_churn_by_industry", ["industry", "logos_lost", "rate"], 3),
    ("support_deflection_by_article", ["article_id", "views", "deflected"], 2),
    ("sales_cycle_length_by_segment", ["segment", "median_days"], 3),
    ("free_to_paid_by_activation_step", ["step", "users", "converted"], 2),
    ("region_revenue_by_quarter", ["region", "quarter", "revenue"], 4),
    ("partner_sourced_revenue", ["partner", "revenue", "quarter"], 2),
    ("model_inference_cost_by_feature", ["feature", "tokens", "usd"], 2),
    ("data_freshness_by_pipeline", ["pipeline", "lag_minutes"], 2),
    ("seat_expansion_by_manager", ["manager_id", "seats_added"], 1),
    ("dunning_recovery_by_step", ["step", "recovered_amount"], 1),
    ("enterprise_sso_adoption", ["account_id", "sso_enabled_at"], 1),
]

SCHEMA = "ecommerce"


def build(seed: int, volume: int) -> dict[str, list[str]]:
    """Assign queries to services. Returns {service: [sql, ...]}."""
    rng = random.Random(seed)
    services = [s for s, _ in SERVICES]
    svc_w = [w for _, w in SERVICES]
    wants = [(n, c) for n, c, _ in WANTS]
    want_w = [w for _, _, w in WANTS]

    plan: dict[str, list[str]] = {s: [] for s in services}
    for _ in range(volume):
        svc = rng.choices(services, weights=svc_w, k=1)[0]
        (name, cols) = rng.choices(wants, weights=want_w, k=1)[0]
        # A service asks for a subset of the columns, the way a real query does.
        k = rng.randint(2, len(cols))
        picked = cols[:1] + rng.sample(cols[1:], k - 1) if k > 1 else cols[:1]
        tail = rng.choice(
            ["", " LIMIT 100", " ORDER BY 1", " WHERE 1=1", " GROUP BY 1"]
        )
        plan[svc].append(
            f"SELECT {', '.join(picked)} FROM {SCHEMA}.{name}{tail};"
        )
    return plan


def run(plan: dict[str, list[str]], container: str) -> tuple[int, int]:
    """Execute every query for real. Each one raises a genuine Postgres error."""
    sent = 0
    for svc, queries in plan.items():
        if not queries:
            continue
        script = "\n".join(queries)
        proc = subprocess.run(
            [
                "docker", "exec", "-i",
                "-e", f"PGAPPNAME={svc}",
                container, "psql", "-U", "agent", "-d", "warehouse",
                "-v", "ON_ERROR_STOP=0", "-q",
            ],
            input=script, capture_output=True, text=True,
        )
        errs = proc.stderr.count("does not exist")
        sent += errs
        print(f"  {svc:<26} {len(queries):>4} queries  {errs:>4} real errors logged")
    return sent, sum(len(q) for q in plan.values())


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--container", default="datahub-hack-warehouse-1")
    p.add_argument("--volume", type=int, default=1200, help="queries to run")
    p.add_argument("--seed", type=int, default=20260809, help="deterministic")
    p.add_argument("--dry-run", action="store_true")
    a = p.parse_args()

    plan = build(a.seed, a.volume)
    distinct_wants = len(
        {q.split(" FROM ")[1].split()[0].rstrip(";") for qs in plan.values() for q in qs}
    )
    print(
        f"disclosed demo traffic: {a.volume} queries across "
        f"{sum(1 for v in plan.values() if v)} services, {distinct_wants} distinct "
        f"missing tables, seed {a.seed}\n"
    )
    if a.dry_run:
        for svc, qs in list(plan.items())[:3]:
            print(f"  {svc}: {qs[0] if qs else '(none)'}")
        return 0

    errors, total = run(plan, a.container)
    print(
        f"\n{errors} genuine Postgres errors written to the server log out of "
        f"{total} queries."
    )
    print(
        "Nothing was written to Nullspace. Harvest it the same way you would "
        "harvest a real warehouse:\n\n"
        f"  docker logs {a.container} 2>&1 | "
        "python -m nullspace.agents.harvest --stdin\n"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
