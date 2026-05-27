from uuid import UUID

from pydantic import BaseModel


class PIIFinding(BaseModel):
    column_id: UUID
    column_name: str
    table_id: UUID
    table_name: str
    pii_type: str
    confidence: float
    detection_reason: str


class GovernanceSummary(BaseModel):
    table_id: UUID
    table_name: str
    pii_column_count: int
    pii_findings: list[PIIFinding]
    risk_level: str  # low | medium | high | critical
    recommendations: list[str]


class IngestionRunStatus(BaseModel):
    id: UUID
    source_name: str
    status: str  # running | completed | failed
    tables_scanned: int
    columns_scanned: int
    started_at: str
    completed_at: str | None
    error_message: str | None
    duration_seconds: float | None
