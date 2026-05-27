import pytest
from app.lineage.sql_parser import extract_lineage_from_sql, extract_lineage_from_dbt_model


def test_simple_view():
    sql = """
    CREATE VIEW reporting.daily_sales AS
    SELECT s.id, s.amount, p.name
    FROM sales.orders s
    JOIN products.catalog p ON s.product_id = p.id
    """
    result = extract_lineage_from_sql(sql, default_schema="reporting")
    assert result.target == "reporting.daily_sales"
    assert "sales.orders" in result.sources
    assert "products.catalog" in result.sources


def test_cte_view():
    sql = """
    CREATE VIEW analytics.user_activity AS
    WITH active_users AS (
        SELECT user_id FROM events.sessions WHERE created_at > now() - interval '30 days'
    )
    SELECT u.id, u.email, au.user_id
    FROM users.accounts u
    JOIN active_users au ON u.id = au.user_id
    """
    result = extract_lineage_from_sql(sql, default_schema="analytics")
    assert result.target == "analytics.user_activity"
    # CTE 'active_users' should NOT appear in sources
    assert "analytics.active_users" not in result.sources
    assert "events.sessions" in result.sources
    assert "users.accounts" in result.sources


def test_insert_select():
    sql = """
    INSERT INTO warehouse.fact_sales
    SELECT o.id, o.amount, c.region
    FROM raw.orders o
    JOIN raw.customers c ON o.customer_id = c.id
    """
    result = extract_lineage_from_sql(sql, default_schema="warehouse")
    assert result.target == "warehouse.fact_sales"
    assert "raw.orders" in result.sources
    assert "raw.customers" in result.sources


def test_dbt_ref_macro():
    sql = """
    SELECT
        o.id,
        o.total,
        c.name
    FROM {{ ref('orders') }} o
    JOIN {{ ref('customers') }} c ON o.customer_id = c.id
    """
    result = extract_lineage_from_dbt_model(
        model_name="fact_orders",
        model_sql=sql,
        schema="dbt",
    )
    assert result.target == "dbt.fact_orders"
    assert "dbt.orders" in result.sources
    assert "dbt.customers" in result.sources


def test_dbt_source_macro():
    sql = """
    SELECT id, email FROM {{ source('raw', 'users') }}
    """
    result = extract_lineage_from_dbt_model(
        model_name="stg_users",
        model_sql=sql,
        schema="staging",
    )
    assert result.target == "staging.stg_users"
    assert "raw.users" in result.sources


def test_empty_sql_returns_no_sources():
    result = extract_lineage_from_sql("", target_table="schema.table")
    assert result.sources == []
    assert result.target == "schema.table"
