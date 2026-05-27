from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class TableType(StrEnum):
    TABLE = "table"
    VIEW = "view"
    MATERIALIZED_VIEW = "materialized_view"
    FOREIGN_TABLE = "foreign_table"


class TableSummary(BaseModel):
    """Lightweight representation used in list responses."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    schema_name: str
    table_name: str
    table_type: TableType
    description: str | None
    row_count: int | None
    owner: str | None
    is_pii_flagged: bool
    tag_names: list[str] = Field(default_factory=list)
    last_scanned_at: datetime | None


class TableDetail(TableSummary):
    """Full table representation including AI enrichment fields."""

    size_bytes: int | None
    source_database: str | None
    business_purpose: str | None
    usage_examples: list[str] = Field(default_factory=list)
    related_tables: list[str] = Field(default_factory=list)
    column_count: int = 0
    created_at: datetime
    updated_at: datetime


class TableCreate(BaseModel):
    """Used internally by the ingestion layer."""

    schema_name: str
    table_name: str
    table_type: TableType = TableType.TABLE
    row_count: int | None = None
    size_bytes: int | None = None
    owner: str | None = None
    source_database: str | None = None


class TableUpdate(BaseModel):
    description: str | None = None
    business_purpose: str | None = None
    usage_examples: list[str] | None = None
    owner: str | None = None
    tag_names: list[str] | None = None


class TableListResponse(BaseModel):
    items: list[TableSummary]
    total: int
    page: int
    page_size: int
