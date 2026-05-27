from fastapi import APIRouter, Body

from app.api.deps import AIDep, IngestionDep
from app.domain.schemas.governance import IngestionRunStatus
from pydantic import BaseModel, Field


class IngestionRequest(BaseModel):
    db_url: str = Field(description="Connection string of the database to scan")
    schemas: list[str] | None = Field(
        default=None,
        description="Schemas to include. Scans all if omitted.",
    )
    exclude_schemas: list[str] | None = Field(
        default=None,
        description="Schemas to skip.",
    )
    infer_view_lineage: bool = Field(
        default=True,
        description="Automatically extract lineage from view definitions.",
    )


class EnrichRequest(BaseModel):
    table_id: str
    force: bool = False


router = APIRouter(prefix="/ingestion", tags=["ingestion"])


@router.post("/scan", response_model=IngestionRunStatus)
async def trigger_scan(
    request: IngestionRequest,
    ingestion: IngestionDep,
) -> IngestionRunStatus:
    """
    Scan a target database and ingest its metadata into the catalog.
    This is a synchronous call — for large databases, consider running async via a worker.
    """
    return await ingestion.run(
        db_url=request.db_url,
        schemas=request.schemas,
        exclude_schemas=request.exclude_schemas,
        infer_view_lineage=request.infer_view_lineage,
    )


@router.post("/enrich/{table_id}", response_model=dict)
async def enrich_table(
    table_id: str,
    ai: AIDep,
    force: bool = False,
) -> dict:
    """
    Trigger AI enrichment for a specific table.
    Generates: description, business purpose, usage examples, column descriptions.
    """
    from uuid import UUID

    return await ai.enrich_all(UUID(table_id), force=force)
