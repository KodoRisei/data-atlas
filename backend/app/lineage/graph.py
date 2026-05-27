"""
In-memory lineage graph built on NetworkX DiGraph.

Nodes represent tables (identified by UUID).
Edges represent data flow: source → target (reads-from relationship).
"""
from dataclasses import dataclass
from uuid import UUID

import networkx as nx

from app.core.logging import get_logger
from app.domain.schemas.lineage import ImpactSummary, LineageNode
from app.persistence.models import LineageEdgeModel, TableModel

log = get_logger(__name__)


@dataclass
class GraphNode:
    table_id: UUID
    schema_name: str
    table_name: str
    is_pii_flagged: bool
    row_count: int | None


class LineageGraph:
    """
    Wraps a directed graph for lineage traversal.

    Direction convention:
        source → target  means "target is derived from source"
        (data flows source → target)

    Upstream of X  = ancestors in graph  (what X reads from)
    Downstream of X = descendants in graph (what reads from X)
    """

    def __init__(self) -> None:
        self._graph: nx.DiGraph = nx.DiGraph()

    def load(
        self,
        edges: list[LineageEdgeModel],
        tables: dict[UUID, TableModel],
    ) -> None:
        self._graph.clear()

        # Add all known table nodes first
        for table in tables.values():
            self._graph.add_node(
                str(table.id),
                table_id=table.id,
                schema_name=table.schema_name,
                table_name=table.table_name,
                is_pii_flagged=table.is_pii_flagged,
                row_count=table.row_count,
            )

        for edge in edges:
            src = str(edge.source_table_id)
            tgt = str(edge.target_table_id)
            if src not in self._graph:
                self._graph.add_node(src)
            if tgt not in self._graph:
                self._graph.add_node(tgt)
            self._graph.add_edge(src, tgt, edge_id=str(edge.id))

        log.debug(
            "lineage_graph_loaded",
            nodes=self._graph.number_of_nodes(),
            edges=self._graph.number_of_edges(),
        )

    def get_upstream(
        self, table_id: UUID, max_depth: int = 5
    ) -> list[tuple[UUID, int]]:
        """Returns [(ancestor_table_id, depth)] for all upstream ancestors."""
        node_id = str(table_id)
        if node_id not in self._graph:
            return []
        result: list[tuple[UUID, int]] = []
        for ancestor, data in nx.bfs_successors(self._graph.reverse(), node_id):
            _ = ancestor
            _ = data
        # Use BFS on reversed graph to find predecessors
        for node, depth in self._bfs_reverse(node_id, max_depth):
            result.append((UUID(node), depth))
        return result

    def get_downstream(
        self, table_id: UUID, max_depth: int = 10
    ) -> list[tuple[UUID, int]]:
        """Returns [(descendant_table_id, depth)] for all downstream dependents."""
        node_id = str(table_id)
        if node_id not in self._graph:
            return []
        return [
            (UUID(node), depth)
            for node, depth in self._bfs_forward(node_id, max_depth)
        ]

    def compute_blast_radius(self, table_id: UUID) -> float:
        """
        Blast radius score 0–10. Factors:
        - Number of downstream dependents (weight 0.5)
        - Max dependency depth (weight 0.3)
        - Whether any downstream node is PII-flagged (weight 0.2)
        """
        downstream = self.get_downstream(table_id)
        if not downstream:
            return 0.0

        dep_count = len(downstream)
        max_depth = max((d for _, d in downstream), default=0)

        pii_penalty = any(
            self._graph.nodes.get(str(uid), {}).get("is_pii_flagged", False)
            for uid, _ in downstream
        )

        raw_score = (
            min(dep_count / 20, 1.0) * 5.0
            + min(max_depth / 10, 1.0) * 3.0
            + (2.0 if pii_penalty else 0.0)
        )
        return round(min(raw_score, 10.0), 2)

    def get_critical_path(self, table_id: UUID) -> list[str]:
        """Returns the longest downstream path as a list of table FQNs."""
        node_id = str(table_id)
        if node_id not in self._graph:
            return []
        try:
            paths = list(nx.all_simple_paths(self._graph, node_id, cutoff=20))
            if not paths:
                return []
            longest = max(paths, key=len)
            return [
                f"{self._graph.nodes[n].get('schema_name', '?')}"
                f".{self._graph.nodes[n].get('table_name', n)}"
                for n in longest
            ]
        except nx.NetworkXError:
            return []

    def _to_lineage_node(self, node_id: str, depth: int) -> LineageNode:
        data = self._graph.nodes.get(node_id, {})
        uid = UUID(node_id)
        schema = data.get("schema_name", "unknown")
        table = data.get("table_name", node_id)
        return LineageNode(
            id=node_id,
            table_id=uid,
            schema_name=schema,
            table_name=table,
            full_name=f"{schema}.{table}",
            is_pii_flagged=data.get("is_pii_flagged", False),
            row_count=data.get("row_count"),
            depth=depth,
        )

    def build_impact_summary(
        self, table_id: UUID, table_name: str
    ) -> ImpactSummary:
        downstream = self.get_downstream(table_id)
        direct = [uid for uid, depth in downstream if depth == 1]
        critical_path = self.get_critical_path(table_id)
        blast_score = self.compute_blast_radius(table_id)

        return ImpactSummary(
            table_id=table_id,
            table_name=table_name,
            direct_dependents=len(direct),
            total_downstream=len(downstream),
            max_depth=max((d for _, d in downstream), default=0),
            critical_path=critical_path,
            affected_tables=[
                self._to_lineage_node(str(uid), depth) for uid, depth in downstream
            ],
            blast_radius_score=blast_score,
        )

    def _bfs_forward(
        self, start: str, max_depth: int
    ) -> list[tuple[str, int]]:
        visited: list[tuple[str, int]] = []
        queue = [(start, 0)]
        seen = {start}
        while queue:
            node, depth = queue.pop(0)
            if depth > 0:
                visited.append((node, depth))
            if depth >= max_depth:
                continue
            for neighbor in self._graph.successors(node):
                if neighbor not in seen:
                    seen.add(neighbor)
                    queue.append((neighbor, depth + 1))
        return visited

    def _bfs_reverse(
        self, start: str, max_depth: int
    ) -> list[tuple[str, int]]:
        visited: list[tuple[str, int]] = []
        queue = [(start, 0)]
        seen = {start}
        while queue:
            node, depth = queue.pop(0)
            if depth > 0:
                visited.append((node, depth))
            if depth >= max_depth:
                continue
            for neighbor in self._graph.predecessors(node):
                if neighbor not in seen:
                    seen.add(neighbor)
                    queue.append((neighbor, depth + 1))
        return visited
