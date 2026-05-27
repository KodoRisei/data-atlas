from uuid import UUID

from fastapi import APIRouter

from app.api.deps import ImpactDep
from app.domain.schemas.lineage import ImpactSummary

router = APIRouter(prefix="/impact", tags=["impact"])


@router.get("/{table_id}", response_model=ImpactSummary)
async def analyze_impact(table_id: UUID, impact: ImpactDep) -> ImpactSummary:
    """
    Returns blast-radius analysis for a table.
    Answers: "what breaks if this table changes?"
    """
    return await impact.analyze(table_id)
