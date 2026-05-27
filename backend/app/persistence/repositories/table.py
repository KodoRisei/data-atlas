from uuid import UUID

from sqlalchemy import func, or_, select

from app.persistence.models import TableModel
from app.persistence.repositories.base import BaseRepository


class TableRepository(BaseRepository[TableModel]):
    model_class = TableModel

    async def get_by_fqn(self, schema_name: str, table_name: str) -> TableModel | None:
        result = await self.session.execute(
            select(TableModel).where(
                TableModel.schema_name == schema_name,
                TableModel.table_name == table_name,
            )
        )
        return result.scalar_one_or_none()

    async def list_paginated(
        self,
        page: int = 1,
        page_size: int = 20,
        schema_filter: str | None = None,
        table_type_filter: str | None = None,
        pii_only: bool = False,
    ) -> tuple[list[TableModel], int]:
        query = select(TableModel)
        if schema_filter:
            query = query.where(TableModel.schema_name == schema_filter)
        if table_type_filter:
            query = query.where(TableModel.table_type == table_type_filter)
        if pii_only:
            query = query.where(TableModel.is_pii_flagged.is_(True))

        count_result = await self.session.execute(
            select(func.count()).select_from(query.subquery())
        )
        total = count_result.scalar_one()

        offset = (page - 1) * page_size
        result = await self.session.execute(
            query.order_by(TableModel.schema_name, TableModel.table_name)
            .limit(page_size)
            .offset(offset)
        )
        return list(result.scalars().all()), total

    async def search(self, query: str, limit: int = 20) -> list[TableModel]:
        pattern = f"%{query.lower()}%"
        result = await self.session.execute(
            select(TableModel)
            .where(
                or_(
                    func.lower(TableModel.table_name).like(pattern),
                    func.lower(TableModel.description).like(pattern),
                    func.lower(TableModel.schema_name).like(pattern),
                )
            )
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_ids_by_fqns(self, fqns: list[tuple[str, str]]) -> dict[str, UUID]:
        """Returns {schema.table -> id} for the given (schema, table) pairs."""
        if not fqns:
            return {}
        result = await self.session.execute(
            select(TableModel.id, TableModel.schema_name, TableModel.table_name).where(
                or_(
                    *[
                        (TableModel.schema_name == s) & (TableModel.table_name == t)
                        for s, t in fqns
                    ]
                )
            )
        )
        return {
            f"{row.schema_name}.{row.table_name}": row.id
            for row in result.all()
        }

    async def mark_pii(self, table_id: UUID) -> None:
        table = await self.get_by_id(table_id)
        if table:
            table.is_pii_flagged = True
            await self.session.flush()

    async def update_scan_timestamp(self, table_id: UUID) -> None:
        from datetime import datetime, timezone

        table = await self.get_by_id(table_id)
        if table:
            table.last_scanned_at = datetime.now(timezone.utc)
            await self.session.flush()
