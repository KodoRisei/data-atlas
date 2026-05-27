from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.core.logging import get_logger
from app.domain.schemas.lineage import ImpactSummary
from app.lineage.graph import LineageGraph as InMemoryGraph
from app.persistence.models import LineageEdgeModel, TableModel
from app.persistence.repositories.table import TableRepository

log = get_logger(__name__)


class ImpactService:
    def __init__(self, session: AsyncSession) -> None:
        self._tables = TableRepository(session)
        self._session = session

    async def analyze(self, table_id: UUID) -> ImpactSummary:
        """Compute blast radius for a given table."""
        table = await self._tables.get_by_id(table_id)
        if not table:
            raise NotFoundError(f"Table {table_id} not found.", table_id=str(table_id))

        graph = await self._build_graph()
        summary = graph.build_impact_summary(
            table_id, f"{table.schema_name}.{table.table_name}"
        )
        log.info(
            "impact_analysis_complete",
            table=f"{table.schema_name}.{table.table_name}",
            blast_radius=summary.blast_radius_score,
            dependents=summary.total_downstream,
        )
        return summary

    async def _build_graph(self) -> InMemoryGraph:
        edges_result = await self._session.execute(select(LineageEdgeModel))
        tables_result = await self._session.execute(select(TableModel))
        all_tables = {t.id: t for t in tables_result.scalars().all()}

        graph = InMemoryGraph()
        graph.load(list(edges_result.scalars().all()), all_tables)
        return graph
