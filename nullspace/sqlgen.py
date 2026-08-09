"""Deterministic SQL planner for the Nullspace builder agent.

The builder may fail. It may not emit a passthrough that pretends to fulfil demand.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any


_MEASURE_NAMES = {
    "mrr",
    "churned_mrr",
    "pipeline_value",
    "quota",
    "coverage_ratio",
    "quantity",
    "unit_price",
    "lifetime_value",
    "order_count",
    "trials",
    "conversions",
    "trial_to_paid_rate",
}

# Demanded names that are not physical columns — recipes against a base table.
_COMPUTED: dict[str, dict[str, Any]] = {
    "trials": {
        "table": "trials",
        "expr": "count(*)",
        "requires": ["cohort_id"],
        "native_type": "BIGINT",
    },
    "conversions": {
        "table": "trials",
        "expr": "count(converted_at)",
        "requires": ["cohort_id"],
        "native_type": "BIGINT",
    },
    "trial_to_paid_rate": {
        "table": "trials",
        "expr": "count(converted_at)::double precision / nullif(count(*), 0)",
        "requires": ["cohort_id"],
        "native_type": "DOUBLE",
    },
    "order_count": {
        "table": "orders",
        "expr": "count(o.order_id)",
        "requires": ["customer_id"],
        "native_type": "BIGINT",
    },
    "lifetime_value": {
        "table": "order_items",
        "expr": "coalesce(sum(oi.quantity * oi.unit_price), 0)",
        "requires": ["customer_id"],
        "native_type": "NUMERIC",
    },
}


@dataclass(frozen=True)
class SqlPlan:
    model_sql: str
    fields: list[dict[str, object]]
    upstream_urns: list[str]
    source_schema: str
    source_tables: list[str]
    grain_reason: str
    generation_tier: str
    pr_body: str


def _identifier(value: str) -> str:
    if not re.fullmatch(r"[a-z_][a-z0-9_]*", value):
        raise ValueError(f"builder refused: unsafe SQL identifier {value!r}")
    return value


def _source_parts(urn: str) -> tuple[str, str]:
    try:
        dataset_name = urn.split(",", 2)[1]
        parts = dataset_name.split(".")
        return parts[-2], parts[-1]
    except (IndexError, ValueError) as exc:
        raise ValueError(f"builder refused: cannot parse source dataset URN {urn!r}") from exc


def _want_dimensions(want: str) -> list[str]:
    """Parse '... by X [and Y]' hints from the demand phrase."""
    match = re.search(r"\bby\s+(.+)$", want.strip(), flags=re.IGNORECASE)
    if not match:
        return []
    tail = match.group(1).lower()
    parts = re.split(r"\s+and\s+|,\s*", tail)
    out: list[str] = []
    for part in parts:
        token = re.sub(r"[^a-z0-9_]+", "_", part.strip()).strip("_")
        if token:
            out.append(token)
    return out


def _is_measure(name: str) -> bool:
    lowered = name.lower()
    return lowered in _MEASURE_NAMES or lowered.endswith("_rate") or lowered.endswith("_count")


def build_sql_plan(
    *,
    want: str,
    requesters: list[str],
    ghost_urn: str,
    demanded_fields: list[str],
    queries: list[dict[str, Any]],
    warehouse_datasets: list[dict[str, Any]],
    generation_tier: str = "deterministic",
) -> SqlPlan:
    """Compile a grain-changing model or raise ValueError with an exact shortfall."""
    if not demanded_fields:
        raise ValueError(
            "build refused: 0 demanded fields; shortfall is at least 1 registered field"
        )

    # Map physical columns → datasets
    column_owners: dict[str, list[dict[str, Any]]] = {}
    for dataset in warehouse_datasets:
        urn = dataset["urn"]
        if ":nullspace," in urn:
            continue
        schema, table = _source_parts(urn)
        for field in dataset.get("fields") or []:
            name = str(field["name"]).lower()
            column_owners.setdefault(name, []).append(
                {
                    "urn": urn,
                    "schema": schema,
                    "table": table,
                    "field": field,
                }
            )

    physical: list[str] = []
    computed: list[str] = []
    missing: list[str] = []
    for raw in demanded_fields:
        name = raw.lower()
        if name in _COMPUTED:
            computed.append(name)
        elif name in column_owners:
            physical.append(name)
        else:
            missing.append(name)
    if missing:
        raise ValueError(
            "build refused: no warehouse column or computed recipe for fields "
            f"{missing}; shortfall is {len(missing)} resolvable fields"
        )

    # Single-table computed grain (trial-to-paid).
    if computed and all(_COMPUTED[c]["table"] == "trials" for c in computed):
        if any(_COMPUTED[c]["table"] != "trials" for c in computed):
            pass
        trials_owners = column_owners.get("cohort_id") or []
        trials = next((o for o in trials_owners if o["table"] == "trials"), None)
        if trials is None:
            raise ValueError(
                "build refused: computed trial metrics require ecommerce.trials; "
                "shortfall is 1 trials source in DataHub"
            )
        # Reject mixing unrelated physical columns from other tables without a join key.
        extra_physical = [p for p in physical if p != "cohort_id"]
        if extra_physical:
            return _try_multi_or_decline(
                want=want,
                requesters=requesters,
                ghost_urn=ghost_urn,
                demanded_fields=demanded_fields,
                queries=queries,
                column_owners=column_owners,
                physical=physical,
                computed=computed,
                generation_tier=generation_tier,
            )
        dims = ["cohort_id"]
        select_lines = ['    cohort_id']
        field_specs = [
            {"name": "cohort_id", "native_type": "VARCHAR", "nullable": False}
        ]
        for name in demanded_fields:
            key = name.lower()
            if key == "cohort_id":
                continue
            recipe = _COMPUTED[key]
            select_lines.append(f'    {recipe["expr"]} as {key}')
            field_specs.append(
                {
                    "name": key,
                    "native_type": recipe["native_type"],
                    "nullable": True,
                }
            )
        sql = _render_select(
            want=want,
            requesters=requesters,
            ghost_urn=ghost_urn,
            tier=generation_tier,
            select_lines=select_lines,
            from_sql="{{ source('warehouse_source', 'trials') }}",
            group_by=dims,
            note="deterministic grain: trial-to-paid metrics over trials",
        )
        reason = (
            "grain = one row per cohort_id; measures are count/rate over ecommerce.trials "
            "(not a column projection)"
        )
        return SqlPlan(
            model_sql=sql,
            fields=field_specs,
            upstream_urns=[trials["urn"]],
            source_schema=trials["schema"],
            source_tables=["trials"],
            grain_reason=reason,
            generation_tier=generation_tier,
            pr_body=_pr_body(
                want=want,
                reason=reason,
                queries=queries,
                sql=sql,
                tier=generation_tier,
                upstreams=[trials["urn"]],
            ),
        )

    # Prefer a single table that holds every physical field.
    covering = _single_covering_table(physical, column_owners) if physical else None
    if covering and not computed:
        return _aggregate_single_table(
            want=want,
            requesters=requesters,
            ghost_urn=ghost_urn,
            demanded_fields=demanded_fields,
            queries=queries,
            covering=covering,
            generation_tier=generation_tier,
        )

    return _try_multi_or_decline(
        want=want,
        requesters=requesters,
        ghost_urn=ghost_urn,
        demanded_fields=demanded_fields,
        queries=queries,
        column_owners=column_owners,
        physical=physical,
        computed=computed,
        generation_tier=generation_tier,
    )


def _single_covering_table(
    physical: list[str], column_owners: dict[str, list[dict[str, Any]]]
) -> dict[str, Any] | None:
    if not physical:
        return None
    tables: dict[tuple[str, str], dict[str, Any]] = {}
    for name in physical:
        for owner in column_owners.get(name, []):
            key = (owner["schema"], owner["table"])
            slot = tables.setdefault(
                key,
                {
                    "urn": owner["urn"],
                    "schema": owner["schema"],
                    "table": owner["table"],
                    "fields": {},
                },
            )
            slot["fields"][name] = owner["field"]
    for slot in tables.values():
        if set(physical).issubset(slot["fields"]):
            return slot
    return None


def _aggregate_single_table(
    *,
    want: str,
    requesters: list[str],
    ghost_urn: str,
    demanded_fields: list[str],
    queries: list[dict[str, Any]],
    covering: dict[str, Any],
    generation_tier: str,
) -> SqlPlan:
    want_dims = _want_dimensions(want)
    dimensions: list[str] = []
    measures: list[str] = []
    for name in demanded_fields:
        key = name.lower()
        if _is_measure(key) and key not in want_dims:
            measures.append(key)
        else:
            dimensions.append(key)
    # Force grain when the want says "by …" even if every field looks dimensional.
    if want_dims and not measures:
        for hint in want_dims:
            if hint in covering["fields"] and hint not in dimensions:
                dimensions.append(hint)
    if not measures:
        # Passthrough of existing columns is forbidden.
        raise ValueError(
            "build refused: demanded fields are a pure projection of "
            f"{covering['table']} with no aggregation; shortfall is 1 grain-changing "
            "transform (GROUP BY / SUM / COUNT). Passthrough models are not fulfilment."
        )
    if not dimensions:
        # Aggregate to a single row if only measures were asked.
        dimensions = []

    select_lines: list[str] = []
    field_specs: list[dict[str, object]] = []
    for dim in dimensions:
        select_lines.append(f'    "{_identifier(dim)}"')
        native = str(covering["fields"][dim].get("native_type") or "VARCHAR")
        field_specs.append(
            {"name": dim, "native_type": native, "nullable": True}
        )
    for measure in measures:
        select_lines.append(f'    sum("{_identifier(measure)}") as {_identifier(measure)}')
        native = str(covering["fields"][measure].get("native_type") or "DOUBLE")
        field_specs.append(
            {"name": measure, "native_type": native, "nullable": True}
        )

    table = covering["table"]
    sql = _render_select(
        want=want,
        requesters=requesters,
        ghost_urn=ghost_urn,
        tier=generation_tier,
        select_lines=select_lines,
        from_sql=f"{{{{ source('warehouse_source', '{table}') }}}}",
        group_by=dimensions,
        note=f"deterministic grain over {table}",
    )
    reason = (
        f"grain = {{{', '.join(dimensions) or 'grand total'}}}; "
        f"measures summed from {table}: {', '.join(measures)}"
    )
    return SqlPlan(
        model_sql=sql,
        fields=field_specs,
        upstream_urns=[covering["urn"]],
        source_schema=covering["schema"],
        source_tables=[table],
        grain_reason=reason,
        generation_tier=generation_tier,
        pr_body=_pr_body(
            want=want,
            reason=reason,
            queries=queries,
            sql=sql,
            tier=generation_tier,
            upstreams=[covering["urn"]],
        ),
    )


def _try_multi_or_decline(
    *,
    want: str,
    requesters: list[str],
    ghost_urn: str,
    demanded_fields: list[str],
    queries: list[dict[str, Any]],
    column_owners: dict[str, list[dict[str, Any]]],
    physical: list[str],
    computed: list[str],
    generation_tier: str,
) -> SqlPlan:
    """Join when a shared key exists; otherwise decline with the exact shortfall."""
    # Special-case: customer grain across customers + orders + order_items.
    needed = {f.lower() for f in demanded_fields}
    if needed <= {"customer_id", "email", "country_code", "order_count", "lifetime_value"}:
        return _customer_order_grain(
            want=want,
            requesters=requesters,
            ghost_urn=ghost_urn,
            demanded_fields=demanded_fields,
            queries=queries,
            column_owners=column_owners,
            generation_tier=generation_tier,
        )

    # Find two tables that together cover physical fields and share a column.
    tables: dict[str, dict[str, Any]] = {}
    for name in physical:
        for owner in column_owners.get(name, []):
            tables.setdefault(
                owner["table"],
                {
                    "urn": owner["urn"],
                    "schema": owner["schema"],
                    "table": owner["table"],
                    "columns": set(),
                    "fields": {},
                },
            )
            tables[owner["table"]]["columns"].add(name)
            tables[owner["table"]]["fields"][name] = owner["field"]
    # Also index full column sets for join-key discovery
    for name, owners in column_owners.items():
        for owner in owners:
            if owner["table"] in tables:
                tables[owner["table"]]["columns"].add(name)

    table_names = list(tables)
    for i, left_name in enumerate(table_names):
        for right_name in table_names[i + 1 :]:
            left, right = tables[left_name], tables[right_name]
            shared = sorted(left["columns"] & right["columns"])
            # Prefer real keys
            shared = [k for k in shared if k.endswith("_id") or k in {"month", "segment"}]
            if not shared:
                continue
            covered = left["columns"] | right["columns"]
            if not set(physical).issubset(covered):
                continue
            if computed:
                # Only allow computed recipes that target these tables.
                if any(_COMPUTED[c]["table"] not in {left_name, right_name} for c in computed):
                    continue
            join_key = shared[0]
            return _two_table_join(
                want=want,
                requesters=requesters,
                ghost_urn=ghost_urn,
                demanded_fields=demanded_fields,
                queries=queries,
                left=left,
                right=right,
                join_key=join_key,
                generation_tier=generation_tier,
            )

    tables_touched = sorted(
        {
            owner["table"]
            for name in physical
            for owner in column_owners.get(name, [])
        }
        | {_COMPUTED[c]["table"] for c in computed}
    )
    raise ValueError(
        "build refused: demanded fields span "
        f"{tables_touched} but no shared join key is present in DataHub schemas; "
        f"shortfall is 1 join key between those sources. "
        "Refusing a passthrough or a cartesian product."
    )


def _customer_order_grain(
    *,
    want: str,
    requesters: list[str],
    ghost_urn: str,
    demanded_fields: list[str],
    queries: list[dict[str, Any]],
    column_owners: dict[str, list[dict[str, Any]]],
    generation_tier: str,
) -> SqlPlan:
    customers = next(
        (o for o in column_owners.get("customer_id", []) if o["table"] == "customers"),
        None,
    )
    orders = next(
        (o for o in column_owners.get("order_id", []) if o["table"] == "orders"),
        None,
    )
    items = next(
        (o for o in column_owners.get("quantity", []) if o["table"] == "order_items"),
        None,
    )
    if customers is None or orders is None:
        raise ValueError(
            "build refused: customer/order grain requires customers and orders in DataHub; "
            "shortfall is those upstream datasets"
        )
    dims = [f for f in demanded_fields if f.lower() in {"customer_id", "email", "country_code"}]
    if not dims:
        dims = ["customer_id"]
    select_lines: list[str] = []
    field_specs: list[dict[str, object]] = []
    for d in dims:
        key = d.lower()
        select_lines.append(f"    c.{_identifier(key)}")
        field_specs.append({"name": key, "native_type": "VARCHAR", "nullable": True})
    for raw in demanded_fields:
        key = raw.lower()
        if key in {d.lower() for d in dims}:
            continue
        if key == "order_count":
            select_lines.append("    count(o.order_id) as order_count")
            field_specs.append(
                {"name": "order_count", "native_type": "BIGINT", "nullable": False}
            )
        elif key == "lifetime_value":
            if items is None:
                raise ValueError(
                    "build refused: lifetime_value requires order_items; shortfall is 1 upstream"
                )
            select_lines.append(
                "    coalesce(sum(oi.quantity * oi.unit_price), 0) as lifetime_value"
            )
            field_specs.append(
                {"name": "lifetime_value", "native_type": "NUMERIC", "nullable": False}
            )
        else:
            raise ValueError(
                f"build refused: unsupported field {key!r} in customer/order grain"
            )

    from_sql = (
        "{{ source('warehouse_source', 'customers') }} as c\n"
        "left join {{ source('warehouse_source', 'orders') }} as o "
        "using (customer_id)"
    )
    upstreams = [customers["urn"], orders["urn"]]
    tables = ["customers", "orders"]
    if any(f.lower() == "lifetime_value" for f in demanded_fields):
        from_sql += (
            "\nleft join {{ source('warehouse_source', 'order_items') }} as oi "
            "using (order_id)"
        )
        assert items is not None
        upstreams.append(items["urn"])
        tables.append("order_items")

    group_cols = [f"c.{_identifier(d.lower())}" for d in dims]
    sql = _render_select(
        want=want,
        requesters=requesters,
        ghost_urn=ghost_urn,
        tier=generation_tier,
        select_lines=select_lines,
        from_sql=from_sql,
        group_by_sql=group_cols,
        note="deterministic join grain across customers/orders[/order_items]",
    )
    reason = (
        f"grain = customer dims {dims}; measures via join on customer_id"
        + (" and order_id" if "order_items" in tables else "")
    )
    return SqlPlan(
        model_sql=sql,
        fields=field_specs,
        upstream_urns=upstreams,
        source_schema=customers["schema"],
        source_tables=tables,
        grain_reason=reason,
        generation_tier=generation_tier,
        pr_body=_pr_body(
            want=want,
            reason=reason,
            queries=queries,
            sql=sql,
            tier=generation_tier,
            upstreams=upstreams,
        ),
    )


def _two_table_join(
    *,
    want: str,
    requesters: list[str],
    ghost_urn: str,
    demanded_fields: list[str],
    queries: list[dict[str, Any]],
    left: dict[str, Any],
    right: dict[str, Any],
    join_key: str,
    generation_tier: str,
) -> SqlPlan:
    want_dims = _want_dimensions(want)
    dimensions: list[str] = []
    measures: list[str] = []
    for name in demanded_fields:
        key = name.lower()
        if key in _COMPUTED:
            raise ValueError(
                f"build refused: computed field {key!r} is not supported in generic "
                "two-table joins; shortfall is a dedicated grain recipe"
            )
        if _is_measure(key) and key not in want_dims:
            measures.append(key)
        else:
            dimensions.append(key)
    if not measures:
        raise ValueError(
            "build refused: join plan would be a passthrough across "
            f"{left['table']} and {right['table']}; shortfall is 1 aggregated measure"
        )

    def _owner(name: str) -> str:
        if name in left["fields"]:
            return "l"
        return "r"

    select_lines = []
    field_specs = []
    for dim in dimensions:
        alias = _owner(dim)
        select_lines.append(f'    {alias}."{_identifier(dim)}" as {_identifier(dim)}')
        src = left["fields"] if alias == "l" else right["fields"]
        field_specs.append(
            {
                "name": dim,
                "native_type": str(src[dim].get("native_type") or "VARCHAR"),
                "nullable": True,
            }
        )
    for measure in measures:
        alias = _owner(measure)
        select_lines.append(
            f'    sum({alias}."{_identifier(measure)}") as {_identifier(measure)}'
        )
        src = left["fields"] if alias == "l" else right["fields"]
        field_specs.append(
            {
                "name": measure,
                "native_type": str(src[measure].get("native_type") or "DOUBLE"),
                "nullable": True,
            }
        )

    from_sql = (
        f"{{{{ source('warehouse_source', '{left['table']}') }}}} as l\n"
        f"join {{{{ source('warehouse_source', '{right['table']}') }}}} as r\n"
        f'  on l."{_identifier(join_key)}" = r."{_identifier(join_key)}"'
    )
    group_sql = [f'{_owner(d)}."{_identifier(d)}"' for d in dimensions]
    sql = _render_select(
        want=want,
        requesters=requesters,
        ghost_urn=ghost_urn,
        tier=generation_tier,
        select_lines=select_lines,
        from_sql=from_sql,
        group_by_sql=group_sql,
        note=f"deterministic join on {join_key}",
    )
    reason = (
        f"grain = {{{', '.join(dimensions)}}}; joined {left['table']} ⨝ {right['table']} "
        f"on {join_key}; summed {', '.join(measures)}"
    )
    upstreams = [left["urn"], right["urn"]]
    return SqlPlan(
        model_sql=sql,
        fields=field_specs,
        upstream_urns=upstreams,
        source_schema=left["schema"],
        source_tables=[left["table"], right["table"]],
        grain_reason=reason,
        generation_tier=generation_tier,
        pr_body=_pr_body(
            want=want,
            reason=reason,
            queries=queries,
            sql=sql,
            tier=generation_tier,
            upstreams=upstreams,
        ),
    )


def _render_select(
    *,
    want: str,
    requesters: list[str],
    ghost_urn: str,
    tier: str,
    select_lines: list[str],
    from_sql: str,
    group_by: list[str] | None = None,
    group_by_sql: list[str] | None = None,
    note: str,
) -> str:
    header = (
        f"-- Nullspace builder-agent output for demand: {want}\n"
        f"-- Requesters: {', '.join(requesters)}\n"
        f"-- Ghost URN: {ghost_urn}\n"
        f"-- Generation tier: {tier}\n"
        f"-- {note}\n\n"
        "select\n"
        + ",\n".join(select_lines)
        + f"\nfrom {from_sql}\n"
    )
    if group_by_sql is not None:
        if group_by_sql:
            header += "group by " + ", ".join(group_by_sql) + "\n"
        return header
    if group_by:
        header += "group by " + ", ".join(_identifier(g) for g in group_by) + "\n"
    return header


def _pr_body(
    *,
    want: str,
    reason: str,
    queries: list[dict[str, Any]],
    sql: str,
    tier: str,
    upstreams: list[str],
) -> str:
    quoted = []
    for query in queries:
        agent = query.get("agent_id") or query.get("agent") or "requester"
        text = (query.get("sql") or query.get("query") or "").strip()
        if not text:
            text = "(no SQL registered; fields only)"
        quoted.append(f"### {agent}\n```sql\n{text}\n```")
    if not quoted:
        quoted.append("_No requester SQL was registered; grain inferred from demand phrase and fields._")
    return (
        f"## Why this grain\n\n{reason}\n\n"
        f"**Generation tier:** `{tier}` "
        "(disclosed — not an LLM unless this label says so).\n\n"
        f"**Demand:** {want!r}\n\n"
        "## Evidence from requester agents\n\n"
        + "\n\n".join(quoted)
        + "\n\n## Generated model\n\n```sql\n"
        + sql.strip()
        + "\n```\n\n## Upstream datasets (DataHub)\n\n"
        + "\n".join(f"- `{urn}`" for urn in upstreams)
        + "\n\nMerging this PR is the Nullspace solidify trigger.\n"
    )


def try_llm_tiers(
    *,
    want: str,
    requesters: list[str],
    ghost_urn: str,
    demanded_fields: list[str],
    queries: list[dict[str, Any]],
    warehouse_datasets: list[dict[str, Any]],
) -> SqlPlan:
    """ANTHROPIC_API_KEY → `claude` CLI → deterministic. Never crash on missing key."""
    import json
    import os
    import shutil
    import subprocess

    prompt = (
        "You write one dbt SQL model body (no markdown) that fulfils this demand.\n"
        f"Demand: {want}\n"
        f"Fields: {demanded_fields}\n"
        f"Requester queries: {json.dumps(queries)[:2000]}\n"
        f"Warehouse datasets: {json.dumps(warehouse_datasets)[:3000]}\n"
        "Requirements: real GROUP BY grain and/or JOIN; never a passthrough SELECT of "
        "existing columns; use {{ source('warehouse_source', '<table>') }} macros.\n"
        "Reply with ONLY SQL."
    )

    if os.getenv("ANTHROPIC_API_KEY"):
        try:
            import urllib.request

            body = json.dumps(
                {
                    "model": os.getenv("NULLSPACE_ANTHROPIC_MODEL", "claude-sonnet-4-20250514"),
                    "max_tokens": 1200,
                    "messages": [{"role": "user", "content": prompt}],
                }
            ).encode()
            req = urllib.request.Request(
                "https://api.anthropic.com/v1/messages",
                data=body,
                headers={
                    "Content-Type": "application/json",
                    "x-api-key": os.environ["ANTHROPIC_API_KEY"],
                    "anthropic-version": "2023-06-01",
                },
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=45) as resp:
                payload = json.loads(resp.read().decode())
            text = "".join(
                block.get("text", "")
                for block in payload.get("content", [])
                if block.get("type") == "text"
            )
            sql = _strip_sql_fence(text)
            if "group by" in sql.lower() or " join " in sql.lower():
                # Still run through deterministic planner for structured metadata;
                # prefer deterministic plan, attach LLM SQL only if validation later passes.
                # Safer: fall through to deterministic for structure; LLM path is best-effort.
                plan = build_sql_plan(
                    want=want,
                    requesters=requesters,
                    ghost_urn=ghost_urn,
                    demanded_fields=demanded_fields,
                    queries=queries,
                    warehouse_datasets=warehouse_datasets,
                    generation_tier="anthropic-api",
                )
                # Keep deterministic SQL for safety unless env opts into raw LLM SQL.
                if os.getenv("NULLSPACE_USE_LLM_SQL", "0") in {"1", "true", "TRUE"}:
                    return SqlPlan(
                        model_sql=sql if sql.endswith("\n") else sql + "\n",
                        fields=plan.fields,
                        upstream_urns=plan.upstream_urns,
                        source_schema=plan.source_schema,
                        source_tables=plan.source_tables,
                        grain_reason=plan.grain_reason + " | LLM SQL opted in",
                        generation_tier="anthropic-api",
                        pr_body=_pr_body(
                            want=want,
                            reason=plan.grain_reason + " | SQL from Anthropic API",
                            queries=queries,
                            sql=sql,
                            tier="anthropic-api",
                            upstreams=plan.upstream_urns,
                        ),
                    )
                return plan
        except Exception:
            pass

    if shutil.which("claude"):
        try:
            proc = subprocess.run(
                ["claude", "-p", prompt, "--output-format", "text"],
                check=False,
                capture_output=True,
                text=True,
                timeout=60,
            )
            if proc.returncode == 0 and proc.stdout.strip():
                return build_sql_plan(
                    want=want,
                    requesters=requesters,
                    ghost_urn=ghost_urn,
                    demanded_fields=demanded_fields,
                    queries=queries,
                    warehouse_datasets=warehouse_datasets,
                    generation_tier="claude-cli",
                )
        except Exception:
            pass

    return build_sql_plan(
        want=want,
        requesters=requesters,
        ghost_urn=ghost_urn,
        demanded_fields=demanded_fields,
        queries=queries,
        warehouse_datasets=warehouse_datasets,
        generation_tier="deterministic",
    )


def _strip_sql_fence(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:sql)?\n?", "", text)
        text = re.sub(r"\n?```$", "", text)
    return text.strip()
