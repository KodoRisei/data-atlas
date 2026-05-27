from typing import Any, Generic, TypeVar
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.persistence.database import Base

ModelT = TypeVar("ModelT", bound=Base)


class BaseRepository(Generic[ModelT]):
    model_class: type[ModelT]

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, entity_id: UUID) -> ModelT | None:
        return await self.session.get(self.model_class, entity_id)

    async def get_all(self, limit: int = 100, offset: int = 0) -> list[ModelT]:
        result = await self.session.execute(
            select(self.model_class).limit(limit).offset(offset)
        )
        return list(result.scalars().all())

    async def count(self) -> int:
        from sqlalchemy import func, select

        result = await self.session.execute(
            select(func.count()).select_from(self.model_class)
        )
        return result.scalar_one()

    async def save(self, instance: ModelT) -> ModelT:
        self.session.add(instance)
        await self.session.flush()
        await self.session.refresh(instance)
        return instance

    async def delete(self, instance: ModelT) -> None:
        await self.session.delete(instance)
        await self.session.flush()

    async def upsert(self, instance: ModelT, **lookup: Any) -> tuple[ModelT, bool]:
        """Returns (instance, created). Merges if exists."""
        filters = [
            getattr(self.model_class, k) == v for k, v in lookup.items()
        ]
        result = await self.session.execute(
            select(self.model_class).where(*filters)
        )
        existing = result.scalar_one_or_none()
        if existing is not None:
            return existing, False
        return await self.save(instance), True
