"""
Prompt templates for AI enrichment.

All prompts are plain Python strings — no templating library dependency.
Column descriptions and business context are injected via .format().
"""

SYSTEM_PROMPT = """You are a senior data engineer and documentation expert for an enterprise data platform.
Your job is to generate clear, accurate, and useful documentation for database objects.
Write for a mixed audience: data analysts, backend engineers, and business stakeholders.
Be concise, precise, and avoid filler phrases. Never hallucinate column names or data that wasn't provided.
Respond with plain text only — no markdown headers, no bullet points unless explicitly asked."""


def table_description_prompt(
    schema: str,
    table_name: str,
    table_type: str,
    columns: list[dict],
    row_count: int | None,
    existing_description: str | None = None,
) -> str:
    col_summary = "\n".join(
        f"  - {c['name']} ({c['type']})"
        + (" [PII]" if c.get("is_pii") else "")
        for c in columns[:30]
    )
    context = f"Row count: approximately {row_count:,}" if row_count else "Row count: unknown"

    prompt = f"""Describe the database {table_type} `{schema}.{table_name}` in 2–3 sentences.

{context}
Columns:
{col_summary}
"""
    if existing_description:
        prompt += f"\nExisting description to improve: {existing_description}"

    prompt += """
Write a clear, factual description of what this table contains, what business entity it represents, and how it might be used analytically. Do not repeat the table name at the start of the sentence."""
    return prompt


def column_description_prompt(
    table_name: str,
    column_name: str,
    data_type: str,
    is_nullable: bool,
    is_pii: bool,
    pii_type: str | None,
    sibling_columns: list[str],
) -> str:
    pii_note = f" This column may contain {pii_type} data and should be handled with care." if is_pii else ""
    nullable_note = "It is optional (nullable)." if is_nullable else "It is required (NOT NULL)."

    siblings = ", ".join(sibling_columns[:10]) if sibling_columns else "none listed"

    return f"""Explain the column `{column_name}` ({data_type}) in the table `{table_name}` in one clear sentence.

{nullable_note}{pii_note}
Other columns in this table: {siblings}

Write a concise, factual description of what this column stores and its likely business meaning."""


def business_purpose_prompt(
    schema: str,
    table_name: str,
    description: str,
    column_names: list[str],
) -> str:
    cols = ", ".join(column_names[:20])
    return f"""Given this database table:
Table: {schema}.{table_name}
Description: {description}
Key columns: {cols}

In 1–2 sentences, explain what business process or analytical use case this table primarily supports.
Focus on the "why" — what business question does this data answer?"""


def usage_examples_prompt(
    schema: str,
    table_name: str,
    column_names: list[str],
) -> str:
    cols = ", ".join(column_names[:15])
    return f"""Generate 2 realistic SQL query examples for the table `{schema}.{table_name}`.

Available columns (partial): {cols}

Requirements:
- Each query should answer a real analytical question a data analyst might ask
- Use proper SQL syntax (PostgreSQL dialect)
- Keep queries concise (under 5 lines each)
- Return ONLY the two SQL statements, separated by a blank line, with no explanation"""


def related_tables_prompt(
    table_name: str,
    upstream_tables: list[str],
    downstream_tables: list[str],
) -> str:
    upstream_str = ", ".join(upstream_tables[:10]) or "none"
    downstream_str = ", ".join(downstream_tables[:10]) or "none"

    return f"""For the table `{table_name}`:
Upstream dependencies (data sources): {upstream_str}
Downstream dependents (data consumers): {downstream_str}

In 1–2 sentences, describe the data flow context: what does this table read from and what does it feed into?"""
