from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class PIIType(str):
    pass


PII_TYPES = {
    "email",
    "phone",
    "address",
    "birth_date",
    "ssn",
    "credit_card",
    "token",
    "password",
    "ip_address",
    "name",
    "generic_pii",
}


class ColumnStatistics(BaseModel):
    null_count: int | None = None
    null_percentage: float | None = None
    distinct_count: int | None = None
    min_value: str | None = None
    max_value: str | None = None
    avg_value: float | None = None
    sample_values: list[str] = Field(default_factory=list)


class ColumnSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    table_id: UUID
    column_name: str
    ordinal_position: int
    data_type: str
    is_nullable: bool
    default_value: str | None
    description: str | None
    is_pii: bool
    pii_type: str | None


class ColumnDetail(ColumnSummary):
    statistics: ColumnStatistics | None = None
    created_at: datetime
    updated_at: datetime


class ColumnCreate(BaseModel):
    table_id: UUID
    column_name: str
    ordinal_position: int
    data_type: str
    is_nullable: bool = True
    default_value: str | None = None
    is_pii: bool = False
    pii_type: str | None = None


class ColumnUpdate(BaseModel):
    description: str | None = None
    is_pii: bool | None = None
    pii_type: str | None = None
