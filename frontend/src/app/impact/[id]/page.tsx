"use client";

import { useParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { ArrowLeft, AlertTriangle, CheckCircle2, Zap } from "lucide-react";
import Link from "next/link";
import { impact as impactApi, tables as tablesApi } from "@/lib/api/client";
import { blastRadiusColor, formatNumber } from "@/lib/utils";
import { Skeleton } from "@/components/ui/Skeleton";
import Badge from "@/components/ui/Badge";

export default function ImpactPage() {
  const { id } = useParams<{ id: string }>();

  const { data: table } = useQuery({
    queryKey: ["table", id],
    queryFn: () => tablesApi.get(id),
  });

  const { data: summary, isLoading } = useQuery({
    queryKey: ["impact", id],
    queryFn: () => impactApi.analyze(id),
  });

  const scoreColor = summary
    ? blastRadiusColor(summary.blast_radius_score)
    : "text-slate-400";

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
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

      <div className="flex items-center gap-3">
        <Zap className="w-6 h-6 text-purple-400" />
        <h1 className="text-xl font-semibold text-slate-100">Impact Analysis</h1>
      </div>

      {isLoading && <Skeleton className="h-64 w-full" />}

      {summary && (
        <div className="space-y-5">
          {/* Blast radius score */}
          <div className="card p-6">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-sm font-medium text-slate-400">
                  Blast Radius Score
                </h2>
                <p className="text-xs text-slate-600 mt-0.5">
                  Higher score = more downstream impact if this table changes
                </p>
              </div>
              <div className={`text-5xl font-bold ${scoreColor}`}>
                {summary.blast_radius_score.toFixed(1)}
                <span className="text-xl text-slate-600">/10</span>
              </div>
            </div>
          </div>

          {/* Metrics */}
          <div className="grid grid-cols-3 gap-4">
            {[
              {
                label: "Direct Dependents",
                value: formatNumber(summary.direct_dependents),
                icon: AlertTriangle,
              },
              {
                label: "Total Downstream",
                value: formatNumber(summary.total_downstream),
                icon: Zap,
              },
              {
                label: "Max Depth",
                value: summary.max_depth.toString(),
                icon: CheckCircle2,
              },
            ].map(({ label, value, icon: Icon }) => (
              <div key={label} className="card p-4">
                <p className="text-xs text-slate-500">{label}</p>
                <p className="text-2xl font-semibold text-slate-100 mt-1">
                  {value}
                </p>
              </div>
            ))}
          </div>

          {/* Critical path */}
          {summary.critical_path.length > 0 && (
            <div className="card p-5">
              <h3 className="text-sm font-medium text-slate-400 mb-3">
                Critical Path (longest dependency chain)
              </h3>
              <div className="flex items-center flex-wrap gap-2">
                {summary.critical_path.map((node, i) => (
                  <span key={i} className="flex items-center gap-2">
                    <code className="bg-slate-950 border border-slate-800 px-2 py-0.5 rounded text-xs font-mono text-slate-300">
                      {node}
                    </code>
                    {i < summary.critical_path.length - 1 && (
                      <span className="text-slate-600 text-xs">→</span>
                    )}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Affected tables */}
          {summary.affected_tables.length > 0 && (
            <div className="card p-5">
              <h3 className="text-sm font-medium text-slate-400 mb-3">
                Affected Tables ({summary.affected_tables.length})
              </h3>
              <div className="space-y-2">
                {summary.affected_tables.map((t) => (
                  <div
                    key={t.table_id}
                    className="flex items-center justify-between text-sm py-1.5 border-b border-slate-800 last:border-0"
                  >
                    <div className="flex items-center gap-2">
                      <Link
                        href={`/tables/${t.table_id}`}
                        className="font-mono text-slate-300 hover:text-brand-400 transition-colors"
                      >
                        {t.full_name}
                      </Link>
                      {t.is_pii_flagged && (
                        <Badge variant="amber">PII</Badge>
                      )}
                    </div>
                    <div className="flex items-center gap-3 text-slate-500 text-xs">
                      {t.row_count != null && (
                        <span>{formatNumber(t.row_count)} rows</span>
                      )}
                      <span>depth {t.depth}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {summary.total_downstream === 0 && (
            <div className="card p-8 text-center">
              <CheckCircle2 className="w-8 h-8 text-emerald-400 mx-auto mb-2" />
              <p className="text-slate-300 font-medium">No downstream dependents</p>
              <p className="text-sm text-slate-500 mt-1">
                Changing this table has no known downstream impact.
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
