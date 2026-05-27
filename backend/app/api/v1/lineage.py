from uuid import UUID

from fastapi import APIRouter, Query

from app.api.deps import LineageDep
from app.domain.schemas.lineage import (
    LineageEdge,
    LineageEdgeCreate,
    LineageGraph,
)

router = APIRouter(prefix="/lineage", tags=["lineage"])


@router.get("/{table_id}", response_model=LineageGraph)
async def get_lineage(
    table_id: UUID,
    lineage: LineageDep,
    upstream_depth: int = Query(default=3, ge=1, le=10),
    downstream_depth: int = Query(default=3, ge=1, le=10),
) -> LineageGraph:
    return await lineage.get_lineage_graph(
        table_id,
        upstream_depth=upstream_depth,
        downstream_depth=downstream_depth,
    )


@router.post("/edges", response_model=LineageEdge, status_code=201)
async def create_lineage_edge(
    payload: LineageEdgeCreate, lineage: LineageDep
) -> LineageEdge:
    return await lineage.add_edge(payload)


@router.post("/{table_id}/parse-view", response_model=list[LineageEdge])
async def parse_view_lineage(
    table_id: UUID,
    lineage: LineageDep,
    view_sql: str = Query(description="SQL definition of the view"),
    schema: str = Query(default="public"),
) -> list[LineageEdge]:
    """
    Parse a view definition and register upstream lineage edges automatically.
    """
    return await lineage.parse_and_register_view_lineage(table_id, view_sql, schema)
