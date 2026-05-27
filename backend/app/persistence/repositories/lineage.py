from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.persistence.models import LineageEdgeModel
from app.persistence.repositories.base import BaseRepository


class LineageRepository(BaseRepository[LineageEdgeModel]):
    model_class = LineageEdgeModel

    async def get_upstream(self, table_id: UUID) -> list[LineageEdgeModel]:
        """All edges pointing INTO this table (sources)."""
        result = await self.session.execute(
            select(LineageEdgeModel)
            .options(
                selectinload(LineageEdgeModel.source_table),
                selectinload(LineageEdgeModel.target_table),
            )
            .where(LineageEdgeModel.target_table_id == table_id)
        )
        return list(result.scalars().all())

    async def get_downstream(self, table_id: UUID) -> list[LineageEdgeModel]:
        """All edges going OUT from this table (dependents)."""
        result = await self.session.execute(
            select(LineageEdgeModel)
            .options(
                selectinload(LineageEdgeModel.source_table),
                selectinload(LineageEdgeModel.target_table),
            )
            .where(LineageEdgeModel.source_table_id == table_id)
        )
        return list(result.scalars().all())

    async def get_all_edges(self) -> list[LineageEdgeModel]:
        result = await self.session.execute(
            select(LineageEdgeModel).options(
                selectinload(LineageEdgeModel.source_table),
                selectinload(LineageEdgeModel.target_table),
            )
        )
        return list(result.scalars().all())

    async def edge_exists(self, source_id: UUID, target_id: UUID) -> bool:
        result = await self.session.execute(
            select(LineageEdgeModel).where(
                LineageEdgeModel.source_table_id == source_id,
                LineageEdgeModel.target_table_id == target_id,
            )
        )
        return result.scalar_one_or_none() is not None

    async def delete_by_source_file(self, source_file: str) -> int:
        from sqlalchemy import delete

        result = await self.session.execute(
            delete(LineageEdgeModel).where(
                LineageEdgeModel.source_file == source_file
            )
        )
        return result.rowcount  # type: ignore[return-value]
