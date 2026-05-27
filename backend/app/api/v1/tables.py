from uuid import UUID

from fastapi import APIRouter, Query

from app.api.deps import CatalogDep
from app.domain.schemas.table import (
    TableDetail,
    TableListResponse,
    TableSummary,
    TableType,
    TableUpdate,
)

router = APIRouter(prefix="/tables", tags=["tables"])


@router.get("", response_model=TableListResponse)
async def list_tables(
    catalog: CatalogDep,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    schema: str | None = Query(default=None),
    table_type: TableType | None = Query(default=None),
    pii_only: bool = Query(default=False),
) -> TableListResponse:
    return await catalog.list_tables(
        page=page,
        page_size=page_size,
        schema_filter=schema,
        table_type_filter=table_type,
        pii_only=pii_only,
    )


@router.get("/search", response_model=list[TableSummary])
async def search_tables(
    catalog: CatalogDep,
    q: str = Query(min_length=1, max_length=200),
    limit: int = Query(default=20, ge=1, le=50),
) -> list[TableSummary]:
    return await catalog.search(q, limit=limit)


@router.get("/{table_id}", response_model=TableDetail)
async def get_table(table_id: UUID, catalog: CatalogDep) -> TableDetail:
    return await catalog.get_table(table_id)


@router.patch("/{table_id}", response_model=TableDetail)
async def update_table(
    table_id: UUID, update: TableUpdate, catalog: CatalogDep
) -> TableDetail:
    return await catalog.update_table(table_id, update)
