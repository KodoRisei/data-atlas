from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class RelationshipType(StrEnum):
    DERIVED_FROM = "derived_from"
    REFERENCES = "references"
    DEPENDS_ON = "depends_on"
    COPIES_FROM = "copies_from"


class LineageSource(StrEnum):
    SQL_VIEW = "sql_view"
    DBT_MODEL = "dbt_model"
    MANUAL = "manual"
    INFERRED = "inferred"


class LineageEdge(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    source_table_id: UUID
    target_table_id: UUID
    source_table_name: str
    target_table_name: str
    relationship_type: RelationshipType
    lineage_source: LineageSource
    sql_snippet: str | None = None
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    source_file: str | None = None
    created_at: datetime


class LineageEdgeCreate(BaseModel):
    source_table_id: UUID
    target_table_id: UUID
    relationship_type: RelationshipType = RelationshipType.DERIVED_FROM
    lineage_source: LineageSource = LineageSource.INFERRED
    sql_snippet: str | None = None
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    source_file: str | None = None


class LineageNode(BaseModel):
    """Graph node for visualization."""

    id: str
    table_id: UUID
    schema_name: str
    table_name: str
    full_name: str
    is_pii_flagged: bool
    row_count: int | None
    depth: int = 0


class LineageGraph(BaseModel):
    """Full lineage graph for a given table."""

    root_table_id: UUID
    nodes: list[LineageNode]
    edges: list[LineageEdge]
    upstream_depth: int
    downstream_depth: int


class ImpactSummary(BaseModel):
    """Result of blast-radius analysis for a table."""

    table_id: UUID
    table_name: str
    direct_dependents: int
    total_downstream: int
    max_depth: int
    critical_path: list[str]
    affected_tables: list[LineageNode]
    blast_radius_score: float = Field(ge=0.0, le=10.0)
