"""
Catalog service: primary read/write interface for table and column metadata.
"""
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.core.logging import get_logger
from app.domain.schemas.column import ColumnDetail, ColumnSummary, ColumnUpdate
from app.domain.schemas.table import (
    TableDetail,
    TableListResponse,
    TableSummary,
    TableUpdate,
)
from app.persistence.models import ColumnModel, TableModel
from app.persistence.repositories.column import ColumnRepository
from app.persistence.repositories.table import TableRepository

log = get_logger(__name__)


def _table_to_summary(t: TableModel) -> TableSummary:
    return TableSummary(
        id=t.id,
        schema_name=t.schema_name,
        table_name=t.table_name,
        table_type=t.table_type,  # type: ignore[arg-type]
        description=t.description,
        row_count=t.row_count,
        owner=t.owner,
        is_pii_flagged=t.is_pii_flagged,
        tag_names=t.tag_names,
        last_scanned_at=t.last_scanned_at,
    )


def _table_to_detail(t: TableModel, column_count: int) -> TableDetail:
    return TableDetail(
        id=t.id,
        schema_name=t.schema_name,
        table_name=t.table_name,
        table_type=t.table_type,  # type: ignore[arg-type]
        description=t.description,
        row_count=t.row_count,
        size_bytes=t.size_bytes,
        owner=t.owner,
        source_database=t.source_database,
        is_pii_flagged=t.is_pii_flagged,
        tag_names=t.tag_names,
        last_scanned_at=t.last_scanned_at,
        business_purpose=t.business_purpose,
        usage_examples=t.usage_examples or [],
        related_tables=t.related_tables or [],
        column_count=column_count,
        created_at=t.created_at,
        updated_at=t.updated_at,
    )


def _column_to_summary(c: ColumnModel) -> ColumnSummary:
    return ColumnSummary(
        id=c.id,
        table_id=c.table_id,
        column_name=c.column_name,
        ordinal_position=c.ordinal_position,
        data_type=c.data_type,
        is_nullable=c.is_nullable,
        default_value=c.default_value,
        description=c.description,
        is_pii=c.is_pii,
        pii_type=c.pii_type,
    )


def _column_to_detail(c: ColumnModel) -> ColumnDetail:
    from app.domain.schemas.column import ColumnStatistics

    stats = None
    if c.statistics:
        stats = ColumnStatistics(**c.statistics)
    return ColumnDetail(
        id=c.id,
        table_id=c.table_id,
        column_name=c.column_name,
        ordinal_position=c.ordinal_position,
        data_type=c.data_type,
        is_nullable=c.is_nullable,
        default_value=c.default_value,
        description=c.description,
        is_pii=c.is_pii,
        pii_type=c.pii_type,
        statistics=stats,
        created_at=c.created_at,
        updated_at=c.updated_at,
    )


class CatalogService:
    def __init__(self, session: AsyncSession) -> None:
        self._tables = TableRepository(session)
        self._columns = ColumnRepository(session)

    async def list_tables(
        self,
        page: int = 1,
        page_size: int = 20,
        schema_filter: str | None = None,
        table_type_filter: str | None = None,
        pii_only: bool = False,
    ) -> TableListResponse:
        tables, total = await self._tables.list_paginated(
            page=page,
            page_size=page_size,
            schema_filter=schema_filter,
            table_type_filter=table_type_filter,
            pii_only=pii_only,
        )
        return TableListResponse(
            items=[_table_to_summary(t) for t in tables],
            total=total,
            page=page,
            page_size=page_size,
        )

    async def get_table(self, table_id: UUID) -> TableDetail:
        table = await self._tables.get_by_id(table_id)
        if not table:
            raise NotFoundError(f"Table {table_id} not found.", table_id=str(table_id))
        col_count = await self._columns.count_for_table(table_id)
        return _table_to_detail(table, col_count)

    async def get_table_by_fqn(self, schema: str, table: str) -> TableDetail:
        model = await self._tables.get_by_fqn(schema, table)
        if not model:
            raise NotFoundError(f"Table {schema}.{table} not found.")
        col_count = await self._columns.count_for_table(model.id)
        return _table_to_detail(model, col_count)

    async def update_table(self, table_id: UUID, update: TableUpdate) -> TableDetail:
        table = await self._tables.get_by_id(table_id)
        if not table:
            raise NotFoundError(f"Table {table_id} not found.")
        if update.description is not None:
            table.description = update.description
        if update.business_purpose is not None:
            table.business_purpose = update.business_purpose
        if update.usage_examples is not None:
            table.usage_examples = update.usage_examples
        if update.owner is not None:
            table.owner = update.owner
        if update.tag_names is not None:
            table.tags = {"names": update.tag_names}
        await self._tables.session.flush()
        col_count = await self._columns.count_for_table(table_id)
        return _table_to_detail(table, col_count)

    async def get_columns(self, table_id: UUID) -> list[ColumnSummary]:
        table = await self._tables.get_by_id(table_id)
        if not table:
            raise NotFoundError(f"Table {table_id} not found.")
        columns = await self._columns.get_by_table(table_id)
        return [_column_to_summary(c) for c in columns]

    async def get_column(self, column_id: UUID) -> ColumnDetail:
        col = await self._columns.get_by_id(column_id)
        if not col:
            raise NotFoundError(f"Column {column_id} not found.")
        return _column_to_detail(col)

    async def update_column(
        self, column_id: UUID, update: ColumnUpdate
    ) -> ColumnDetail:
        col = await self._columns.get_by_id(column_id)
        if not col:
            raise NotFoundError(f"Column {column_id} not found.")
        if update.description is not None:
            col.description = update.description
        if update.is_pii is not None:
            col.is_pii = update.is_pii
        if update.pii_type is not None:
            col.pii_type = update.pii_type
        await self._columns.session.flush()
        return _column_to_detail(col)

    async def search(self, query: str, limit: int = 20) -> list[TableSummary]:
        tables = await self._tables.search(query, limit=limit)
        return [_table_to_summary(t) for t in tables]
