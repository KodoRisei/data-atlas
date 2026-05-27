"""Initial schema: tables, columns, lineage_edges, ingestion_runs

Revision ID: 001
Revises:
Create Date: 2026-05-26

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "tables",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("schema_name", sa.String(255), nullable=False),
        sa.Column("table_name", sa.String(255), nullable=False),
        sa.Column("table_type", sa.String(50), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("business_purpose", sa.Text(), nullable=True),
        sa.Column("usage_examples", postgresql.JSONB(), nullable=True),
        sa.Column("related_tables", postgresql.JSONB(), nullable=True),
        sa.Column("row_count", sa.Integer(), nullable=True),
        sa.Column("size_bytes", sa.Integer(), nullable=True),
        sa.Column("owner", sa.String(255), nullable=True),
        sa.Column("source_database", sa.String(500), nullable=True),
        sa.Column("tags", postgresql.JSONB(), nullable=True),
        sa.Column("is_pii_flagged", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("last_scanned_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("schema_name", "table_name", name="uq_table_fqn"),
    )
    op.create_index("ix_tables_schema_name", "tables", ["schema_name"])
    op.create_index("ix_tables_table_name", "tables", ["table_name"])

    op.create_table(
        "columns",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("table_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("column_name", sa.String(255), nullable=False),
        sa.Column("ordinal_position", sa.Integer(), nullable=False),
        sa.Column("data_type", sa.String(100), nullable=False),
        sa.Column("is_nullable", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("default_value", sa.Text(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_pii", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("pii_type", sa.String(50), nullable=True),
        sa.Column("statistics", postgresql.JSONB(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["table_id"], ["tables.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("table_id", "column_name", name="uq_column_in_table"),
    )
    op.create_index("ix_columns_table_id", "columns", ["table_id"])

    op.create_table(
        "lineage_edges",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source_table_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("target_table_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("relationship_type", sa.String(50), nullable=False),
        sa.Column("lineage_source", sa.String(50), nullable=False),
        sa.Column("sql_snippet", sa.Text(), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="1.0"),
        sa.Column("source_file", sa.String(500), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["source_table_id"], ["tables.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["target_table_id"], ["tables.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "source_table_id", "target_table_id", name="uq_lineage_edge"
        ),
    )
    op.create_index(
        "ix_lineage_edges_source", "lineage_edges", ["source_table_id"]
    )
    op.create_index(
        "ix_lineage_edges_target", "lineage_edges", ["target_table_id"]
    )

    op.create_table(
        "ingestion_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source_name", sa.String(500), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("tables_scanned", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("columns_scanned", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    # Trigger to auto-update updated_at on tables
    op.execute("""
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = now();
            RETURN NEW;
        END;
        $$ language 'plpgsql';
    """)

    op.execute("""
        CREATE TRIGGER update_tables_updated_at
        BEFORE UPDATE ON tables
        FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    """)

    op.execute("""
        CREATE TRIGGER update_columns_updated_at
        BEFORE UPDATE ON columns
        FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    """)


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS update_columns_updated_at ON columns;")
    op.execute("DROP TRIGGER IF EXISTS update_tables_updated_at ON tables;")
    op.execute("DROP FUNCTION IF EXISTS update_updated_at_column();")
    op.drop_table("ingestion_runs")
    op.drop_table("lineage_edges")
    op.drop_table("columns")
    op.drop_table("tables")
