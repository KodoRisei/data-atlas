from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.base import BaseAIProvider
from app.ai.registry import get_ai_provider
from app.persistence.database import get_db_session
from app.services.ai_enrichment import AIEnrichmentService
from app.services.catalog import CatalogService
from app.services.impact import ImpactService
from app.services.ingestion import IngestionService
from app.services.lineage import LineageService


async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async for session in get_db_session():
        yield session


DBSession = Annotated[AsyncSession, Depends(db_session)]


def get_catalog_service(session: DBSession) -> CatalogService:
    return CatalogService(session)


def get_lineage_service(session: DBSession) -> LineageService:
    return LineageService(session)


def get_impact_service(session: DBSession) -> ImpactService:
    return ImpactService(session)


def get_ingestion_service(session: DBSession) -> IngestionService:
    return IngestionService(session)


def get_ai_enrichment_service(session: DBSession) -> AIEnrichmentService:
    provider: BaseAIProvider = get_ai_provider()
    return AIEnrichmentService(session, provider)


CatalogDep = Annotated[CatalogService, Depends(get_catalog_service)]
LineageDep = Annotated[LineageService, Depends(get_lineage_service)]
ImpactDep = Annotated[ImpactService, Depends(get_impact_service)]
IngestionDep = Annotated[IngestionService, Depends(get_ingestion_service)]
AIDep = Annotated[AIEnrichmentService, Depends(get_ai_enrichment_service)]
