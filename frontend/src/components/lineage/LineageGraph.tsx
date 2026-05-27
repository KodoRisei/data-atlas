"use client";

import { useCallback } from "react";
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  addEdge,
  type Node,
  type Edge,
  type Connection,
  BackgroundVariant,
  MarkerType,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import type { LineageGraph as LineageGraphData, LineageNode } from "@/lib/api/types";
import { ShieldAlert } from "lucide-react";

interface LineageGraphProps {
  data: LineageGraphData;
  rootTableId: string;
}

function buildFlowNodes(
  nodes: LineageNode[],
  rootTableId: string
): Node[] {
  const LEVEL_WIDTH = 280;
  const NODE_HEIGHT = 70;
  const VERTICAL_GAP = 90;

  // Group by depth
  const depthGroups = new Map<number, LineageNode[]>();
  nodes.forEach((n) => {
    const d = n.depth;
    if (!depthGroups.has(d)) depthGroups.set(d, []);
    depthGroups.get(d)!.push(n);
  });

  const flowNodes: Node[] = [];
  depthGroups.forEach((group, depth) => {
    group.forEach((node, i) => {
      const isRoot = node.table_id === rootTableId;
      flowNodes.push({
        id: node.table_id,
        type: "default",
        position: {
          x: depth * LEVEL_WIDTH,
          y: i * VERTICAL_GAP - ((group.length - 1) * VERTICAL_GAP) / 2,
        },
        data: { label: buildNodeLabel(node, isRoot) },
        style: {
          background: isRoot ? "#4361ee22" : "#1e293b",
          border: `1px solid ${isRoot ? "#4361ee" : node.is_pii_flagged ? "#f59e0b44" : "#334155"}`,
          borderRadius: "8px",
          padding: "8px 12px",
          minWidth: "200px",
          color: "#f1f5f9",
          fontSize: "12px",
        },
      });
    });
  });

  return flowNodes;
}

function buildNodeLabel(node: LineageNode, isRoot: boolean): React.ReactNode {
  return (
    <div className="flex flex-col gap-0.5">
      <div className="flex items-center gap-1">
        <span className="text-xs text-slate-500 font-mono">{node.schema_name}</span>
        {node.is_pii_flagged && (
          <ShieldAlert className="w-3 h-3 text-amber-400 shrink-0" />
        )}
      </div>
      <span
        className={`font-medium ${isRoot ? "text-brand-400" : "text-slate-100"}`}
      >
        {node.table_name}
      </span>
      {node.row_count != null && (
        <span className="text-xs text-slate-500">
          {new Intl.NumberFormat().format(node.row_count)} rows
        </span>
      )}
    </div>
  );
}

export default function LineageGraphView({
  data,
  rootTableId,
}: LineageGraphProps) {
  const initialNodes = buildFlowNodes(data.nodes, rootTableId);

  const initialEdges: Edge[] = data.edges.map((e) => ({
    id: e.id,
    source: e.source_table_id,
    target: e.target_table_id,
    animated: false,
    style: { stroke: "#475569", strokeWidth: 1.5 },
    markerEnd: { type: MarkerType.ArrowClosed, color: "#475569", width: 16, height: 16 },
    label: e.confidence < 1.0 ? `${Math.round(e.confidence * 100)}%` : undefined,
    labelStyle: { fill: "#64748b", fontSize: 10 },
  }));

  const [nodes, , onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

  const onConnect = useCallback(
    (params: Connection) => setEdges((eds) => addEdge(params, eds)),
    [setEdges]
  );

  if (data.nodes.length === 0) {
    return (
      <div className="flex items-center justify-center h-64 text-slate-500 text-sm">
        No lineage data available for this table.
      </div>
    );
  }

  return (
    <div className="h-[500px] rounded-lg overflow-hidden border border-slate-800">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        fitView
        fitViewOptions={{ padding: 0.2 }}
        minZoom={0.3}
        maxZoom={2}
        colorMode="dark"
      >
        <Background
          variant={BackgroundVariant.Dots}
          gap={20}
          size={1}
          color="#1e293b"
        />
        <Controls showInteractive={false} />
        <MiniMap
          nodeColor={(node) =>
            (node.style as { background?: string })?.background === "#4361ee22"
              ? "#4361ee"
              : "#334155"
          }
          maskColor="rgba(15, 23, 42, 0.8)"
        />
      </ReactFlow>
    </div>
  );
}
