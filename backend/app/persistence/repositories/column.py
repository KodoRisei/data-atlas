from uuid import UUID

from sqlalchemy import func, or_, select

from app.persistence.models import ColumnModel
from app.persistence.repositories.base import BaseRepository


class ColumnRepository(BaseRepository[ColumnModel]):
    model_class = ColumnModel

    async def get_by_table(self, table_id: UUID) -> list[ColumnModel]:
        result = await self.session.execute(
            select(ColumnModel)
            .where(ColumnModel.table_id == table_id)
            .order_by(ColumnModel.ordinal_position)
        )
        return list(result.scalars().all())

    async def get_by_table_and_name(
        self, table_id: UUID, column_name: str
    ) -> ColumnModel | None:
        result = await self.session.execute(
            select(ColumnModel).where(
                ColumnModel.table_id == table_id,
                ColumnModel.column_name == column_name,
            )
        )
        return result.scalar_one_or_none()

    async def search(self, query: str, limit: int = 20) -> list[ColumnModel]:
        pattern = f"%{query.lower()}%"
        result = await self.session.execute(
            select(ColumnModel)
            .where(
                or_(
                    func.lower(ColumnModel.column_name).like(pattern),
                    func.lower(ColumnModel.description).like(pattern),
                )
            )
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_pii_columns_for_table(self, table_id: UUID) -> list[ColumnModel]:
        result = await self.session.execute(
            select(ColumnModel).where(
                ColumnModel.table_id == table_id,
                ColumnModel.is_pii.is_(True),
            )
        )
        return list(result.scalars().all())

    async def count_for_table(self, table_id: UUID) -> int:
        result = await self.session.execute(
            select(func.count())
            .select_from(ColumnModel)
            .where(ColumnModel.table_id == table_id)
        )
        return result.scalar_one()

    async def delete_for_table(self, table_id: UUID) -> int:
        from sqlalchemy import delete

        result = await self.session.execute(
            delete(ColumnModel).where(ColumnModel.table_id == table_id)
        )
        return result.rowcount  # type: ignore[return-value]
