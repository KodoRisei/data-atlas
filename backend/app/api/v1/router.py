from fastapi import APIRouter

from app.api.v1 import columns, impact, ingestion, lineage, tables

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(tables.router)
api_router.include_router(columns.router)
api_router.include_router(lineage.router)
api_router.include_router(impact.router)
api_router.include_router(ingestion.router)
