from uuid import UUID

from fastapi import APIRouter

from app.api.deps import CatalogDep
from app.domain.schemas.column import ColumnDetail, ColumnSummary, ColumnUpdate

router = APIRouter(prefix="/tables", tags=["columns"])


@router.get("/{table_id}/columns", response_model=list[ColumnSummary])
async def list_columns(table_id: UUID, catalog: CatalogDep) -> list[ColumnSummary]:
    return await catalog.get_columns(table_id)


@router.get("/columns/{column_id}", response_model=ColumnDetail)
async def get_column(column_id: UUID, catalog: CatalogDep) -> ColumnDetail:
    return await catalog.get_column(column_id)


@router.patch("/columns/{column_id}", response_model=ColumnDetail)
async def update_column(
    column_id: UUID, update: ColumnUpdate, catalog: CatalogDep
) -> ColumnDetail:
    return await catalog.update_column(column_id, update)
