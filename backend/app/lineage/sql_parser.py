"""
SQL lineage extraction using sqlglot.

Given a SQL expression (view definition, CTEs, INSERT...SELECT, etc.),
extract (source_table, target_table) pairs representing data flow.
"""
from dataclasses import dataclass, field

import sqlglot
import sqlglot.expressions as exp

from app.core.exceptions import LineageParseError
from app.core.logging import get_logger

log = get_logger(__name__)


@dataclass
class ParsedLineage:
    target: str | None
    sources: list[str] = field(default_factory=list)
    raw_sql: str = ""


def _normalize_table_ref(node: exp.Table, default_schema: str = "public") -> str:
    """Returns schema.table_name (lowercased)."""
    schema = (node.args.get("db") or exp.Identifier(this=default_schema)).name
    table = node.name
    return f"{schema.lower()}.{table.lower()}"


def extract_lineage_from_sql(
    sql: str,
    target_table: str | None = None,
    default_schema: str = "public",
    dialect: str = "postgres",
) -> ParsedLineage:
    """
    Parse SQL and return upstream source tables.

    - For view definitions: target is the view itself (passed in), sources are FROM clauses.
    - For INSERT/MERGE: target is the INSERT target, sources are FROM/SELECT.
    - For CTEs: traces through each WITH clause.
    """
    if not sql or not sql.strip():
        return ParsedLineage(target=target_table)

    try:
        statements = sqlglot.parse(sql, dialect=dialect, error_level=sqlglot.ErrorLevel.WARN)
    except Exception as exc:
        raise LineageParseError(f"sqlglot failed to parse SQL: {exc}", sql=sql[:200]) from exc

    sources: set[str] = set()
    resolved_target: str | None = target_table

    for statement in statements:
        if statement is None:
            continue

        # Determine target from INSERT/CREATE TABLE AS
        if isinstance(statement, exp.Insert):
            if target_table is None:
                tbl = statement.args.get("this")
                if tbl and isinstance(tbl, exp.Table):
                    resolved_target = _normalize_table_ref(tbl, default_schema)

        elif isinstance(statement, (exp.Create,)):
            kind = statement.args.get("kind", "").upper()
            if kind in {"VIEW", "TABLE", "MATERIALIZED VIEW"}:
                this = statement.args.get("this")
                if this and isinstance(this, exp.Table) and target_table is None:
                    resolved_target = _normalize_table_ref(this, default_schema)

        # Collect all FROM / JOIN table references
        for table_node in statement.find_all(exp.Table):
            # Skip CTE references (they're ephemeral aliases, not real tables)
            ref = _normalize_table_ref(table_node, default_schema)
            # Avoid self-reference
            if resolved_target and ref == resolved_target:
                continue
            sources.add(ref)

    # Remove CTE names from sources — they're not real tables
    cte_names: set[str] = set()
    for statement in statements:
        if statement is None:
            continue
        for cte in statement.find_all(exp.CTE):
            alias = cte.args.get("alias")
            if alias:
                cte_names.add(f"{default_schema}.{alias.name.lower()}")

    real_sources = sources - cte_names

    return ParsedLineage(
        target=resolved_target,
        sources=sorted(real_sources),
        raw_sql=sql,
    )


def extract_lineage_from_dbt_model(
    model_name: str,
    model_sql: str,
    schema: str = "public",
    dialect: str = "postgres",
) -> ParsedLineage:
    """
    Resolves dbt {{ ref('...') }} and {{ source('...', '...') }} macros to table names,
    then extracts lineage.

    Macro stubs are replaced with literal table references before parsing.
    """
    import re

    # Replace {{ ref('model_name') }} → schema.model_name
    processed = re.sub(
        r"\{\{\s*ref\s*\(\s*['\"](\w+)['\"]\s*\)\s*\}\}",
        lambda m: f"{schema}.{m.group(1).lower()}",
        model_sql,
    )
    # Replace {{ source('source_name', 'table_name') }} → source_name.table_name
    processed = re.sub(
        r"\{\{\s*source\s*\(\s*['\"](\w+)['\"]\s*,\s*['\"](\w+)['\"]\s*\)\s*\}\}",
        lambda m: f"{m.group(1).lower()}.{m.group(2).lower()}",
        processed,
    )
    # Remove remaining {{ ... }} macros to avoid parse errors
    processed = re.sub(r"\{\{.*?\}\}", "1", processed, flags=re.DOTALL)
    processed = re.sub(r"\{%-?.*?-%?\}", "", processed, flags=re.DOTALL)

    return extract_lineage_from_sql(
        processed,
        target_table=f"{schema}.{model_name.lower()}",
        default_schema=schema,
        dialect=dialect,
    )
