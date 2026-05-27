from pydantic import BaseModel, Field

from app.domain.schemas.table import TableType


class SearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=500)
    schema_filter: str | None = None
    table_type_filter: TableType | None = None
    pii_only: bool = False
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


class SearchHit(BaseModel):
    entity_type: str  # table | column
    entity_id: str
    table_name: str
    schema_name: str
    column_name: str | None = None
    snippet: str
    score: float


class SearchResponse(BaseModel):
    query: str
    hits: list[SearchHit]
    total: int
    page: int
    page_size: int
