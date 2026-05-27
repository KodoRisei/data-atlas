"""
Lineage service: builds the in-memory graph from persisted edges and
resolves SQL view definitions into lineage.
"""
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import LineageParseError, NotFoundError
from app.core.logging import get_logger
from app.domain.schemas.lineage import (
    LineageEdge,
    LineageEdgeCreate,
    LineageGraph,
    LineageNode,
    RelationshipType,
)
from app.lineage.graph import LineageGraph as InMemoryGraph
from app.lineage.sql_parser import extract_lineage_from_sql
from app.persistence.models import LineageEdgeModel, TableModel
from app.persistence.repositories.lineage import LineageRepository
from app.persistence.repositories.table import TableRepository

log = get_logger(__name__)


def _edge_to_schema(edge: LineageEdgeModel) -> LineageEdge:
    src = edge.source_table
    tgt = edge.target_table
    return LineageEdge(
        id=edge.id,
        source_table_id=edge.source_table_id,
        target_table_id=edge.target_table_id,
        source_table_name=f"{src.schema_name}.{src.table_name}" if src else "unknown",
        target_table_name=f"{tgt.schema_name}.{tgt.table_name}" if tgt else "unknown",
        relationship_type=edge.relationship_type,  # type: ignore[arg-type]
        lineage_source=edge.lineage_source,  # type: ignore[arg-type]
        sql_snippet=edge.sql_snippet,
        confidence=edge.confidence,
        source_file=edge.source_file,
        created_at=edge.created_at,
    )


class LineageService:
    def __init__(self, session: AsyncSession) -> None:
        self._edges = LineageRepository(session)
        self._tables = TableRepository(session)
        self._session = session

    async def add_edge(self, payload: LineageEdgeCreate) -> LineageEdge:
        if await self._edges.edge_exists(payload.source_table_id, payload.target_table_id):
            # Return existing edge rather than raising a conflict error
            result = await self._session.execute(
                select(LineageEdgeModel).where(
                    LineageEdgeModel.source_table_id == payload.source_table_id,
                    LineageEdgeModel.target_table_id == payload.target_table_id,
                )
            )
            edge = result.scalar_one()
            return _edge_to_schema(edge)

        model = LineageEdgeModel(
            source_table_id=payload.source_table_id,
            target_table_id=payload.target_table_id,
            relationship_type=payload.relationship_type,
            lineage_source=payload.lineage_source,
            sql_snippet=payload.sql_snippet,
            confidence=payload.confidence,
            source_file=payload.source_file,
        )
        saved = await self._edges.save(model)
        # Reload with joined tables
        result = await self._session.execute(
            select(LineageEdgeModel)
            .where(LineageEdgeModel.id == saved.id)
        )
        loaded = result.scalar_one()
        return _edge_to_schema(loaded)

    async def get_lineage_graph(
        self,
        table_id: UUID,
        upstream_depth: int = 3,
        downstream_depth: int = 3,
    ) -> LineageGraph:
        table = await self._tables.get_by_id(table_id)
        if not table:
            raise NotFoundError(f"Table {table_id} not found.")

        graph = await self._build_in_memory_graph()

        upstream = graph.get_upstream(table_id, max_depth=upstream_depth)
        downstream = graph.get_downstream(table_id, max_depth=downstream_depth)

        # Collect all node IDs in the subgraph
        all_node_ids = {str(table_id)} | {str(uid) for uid, _ in upstream + downstream}

        # Build edge list for subgraph
        all_edges_raw = await self._edges.get_all_edges()
        relevant_edges = [
            _edge_to_schema(e)
            for e in all_edges_raw
            if str(e.source_table_id) in all_node_ids
            or str(e.target_table_id) in all_node_ids
        ]

        # Build node list
        nodes: list[LineageNode] = []
        root_node = LineageNode(
            id=str(table_id),
            table_id=table_id,
            schema_name=table.schema_name,
            table_name=table.table_name,
            full_name=f"{table.schema_name}.{table.table_name}",
            is_pii_flagged=table.is_pii_flagged,
            row_count=table.row_count,
            depth=0,
        )
        nodes.append(root_node)

        depth_map = {uid: depth for uid, depth in upstream + downstream}
        for uid, depth in depth_map.items():
            nodes.append(graph._to_lineage_node(str(uid), depth))

        return LineageGraph(
            root_table_id=table_id,
            nodes=nodes,
            edges=relevant_edges,
            upstream_depth=max((d for _, d in upstream), default=0),
            downstream_depth=max((d for _, d in downstream), default=0),
        )

    async def parse_and_register_view_lineage(
        self,
        table_id: UUID,
        view_sql: str,
        schema: str = "public",
    ) -> list[LineageEdge]:
        """
        Parse a view definition and automatically create lineage edges.
        """
        try:
            parsed = extract_lineage_from_sql(
                view_sql, default_schema=schema, dialect="postgres"
            )
        except LineageParseError as exc:
            log.warning("view_lineage_parse_failed", error=str(exc))
            return []

        created_edges: list[LineageEdge] = []
        for source_fqn in parsed.sources:
            parts = source_fqn.split(".", 1)
            src_schema, src_table = (parts[0], parts[1]) if len(parts) == 2 else (schema, parts[0])

            source_model = await self._tables.get_by_fqn(src_schema, src_table)
            if not source_model:
                log.debug("lineage_source_not_in_catalog", fqn=source_fqn)
                continue

            edge = await self.add_edge(
                LineageEdgeCreate(
                    source_table_id=source_model.id,
                    target_table_id=table_id,
                    relationship_type=RelationshipType.DERIVED_FROM,
                    lineage_source="sql_view",  # type: ignore[arg-type]
                    sql_snippet=view_sql[:500],
                    confidence=0.9,
                )
            )
            created_edges.append(edge)

        return created_edges

    async def _build_in_memory_graph(self) -> InMemoryGraph:
        all_edges = await self._edges.get_all_edges()
        all_tables_result = await self._session.execute(select(TableModel))
        all_tables = {t.id: t for t in all_tables_result.scalars().all()}

        graph = InMemoryGraph()
        graph.load(all_edges, all_tables)
        return graph
