"use client";

import { useParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { ArrowLeft } from "lucide-react";
import Link from "next/link";
import { lineage as lineageApi, tables as tablesApi } from "@/lib/api/client";
import LineageGraphView from "@/components/lineage/LineageGraph";
import { Skeleton } from "@/components/ui/Skeleton";

export default function LineagePage() {
  const { id } = useParams<{ id: string }>();

  const { data: table } = useQuery({
    queryKey: ["table", id],
    queryFn: () => tablesApi.get(id),
  });

  const { data: graph, isLoading } = useQuery({
    queryKey: ["lineage", id],
    queryFn: () =>
      lineageApi.get(id, { upstream_depth: 4, downstream_depth: 4 }),
  });

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      <div className="flex items-center gap-3">
        <Link
          href={`/tables/${id}`}
          className="flex items-center gap-1 text-sm text-slate-500 hover:text-slate-300 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to table
        </Link>
        {table && (
          <>
            <span className="text-slate-700">/</span>
            <span className="text-slate-300 font-mono text-sm">
              {table.schema_name}.{table.table_name}
            </span>
          </>
        )}
      </div>

      <div>
        <h1 className="text-xl font-semibold text-slate-100">Lineage Graph</h1>
        {graph && (
          <p className="text-sm text-slate-500 mt-1">
            {graph.nodes.length} nodes · {graph.edges.length} edges ·
            upstream depth {graph.upstream_depth} · downstream depth{" "}
            {graph.downstream_depth}
          </p>
        )}
      </div>

      <div className="card p-1">
        {isLoading ? (
          <Skeleton className="h-[500px] w-full" />
        ) : graph ? (
          <LineageGraphView data={graph} rootTableId={id} />
        ) : null}
      </div>

      {graph && graph.edges.length > 0 && (
        <div className="card p-5">
          <h3 className="text-sm font-medium text-slate-400 mb-3">
            Lineage Edges
          </h3>
          <div className="space-y-2">
            {graph.edges.map((edge) => (
              <div
                key={edge.id}
                className="flex items-center gap-2 text-sm text-slate-400"
              >
                <span className="font-mono text-slate-300">
                  {edge.source_table_name}
                </span>
                <span className="text-slate-600">→</span>
                <span className="font-mono text-slate-300">
                  {edge.target_table_name}
                </span>
                <span className="text-slate-600 text-xs ml-auto">
                  {edge.lineage_source} · {Math.round(edge.confidence * 100)}%
                  confidence
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
