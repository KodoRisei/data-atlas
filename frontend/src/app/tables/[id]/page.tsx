"use client";

import { useParams, useRouter } from "next/navigation";
import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  ArrowLeft,
  Database,
  GitBranch,
  ShieldAlert,
  Sparkles,
  Zap,
} from "lucide-react";
import Link from "next/link";
import { tables as tablesApi, columns as columnsApi, ingestion as ingestionApi } from "@/lib/api/client";
import { formatNumber, formatBytes, timeAgo, tableTypeLabel } from "@/lib/utils";
import ColumnList from "@/components/tables/ColumnList";
import Badge from "@/components/ui/Badge";
import { Skeleton } from "@/components/ui/Skeleton";

type Tab = "overview" | "columns" | "lineage" | "impact";

export default function TableDetailPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const qc = useQueryClient();
  const [activeTab, setActiveTab] = useState<Tab>("overview");

  const { data: table, isLoading } = useQuery({
    queryKey: ["table", id],
    queryFn: () => tablesApi.get(id),
  });

  const { data: cols } = useQuery({
    queryKey: ["columns", id],
    queryFn: () => columnsApi.list(id),
    enabled: activeTab === "columns" || activeTab === "overview",
  });

  const enrichMutation = useMutation({
    mutationFn: () => ingestionApi.enrich(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["table", id] });
      qc.invalidateQueries({ queryKey: ["columns", id] });
    },
  });

  const TABS: { id: Tab; label: string }[] = [
    { id: "overview", label: "Overview" },
    { id: "columns", label: `Columns${cols ? ` (${cols.length})` : ""}` },
    { id: "lineage", label: "Lineage" },
    { id: "impact", label: "Impact" },
  ];

  if (isLoading) {
    return (
      <div className="space-y-4 max-w-5xl mx-auto">
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-4 w-full" />
        <Skeleton className="h-4 w-3/4" />
      </div>
    );
  }

  if (!table) return null;

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      {/* Breadcrumb */}
      <div className="flex items-center gap-2 text-sm text-slate-500">
        <button
          onClick={() => router.back()}
          className="flex items-center gap-1 hover:text-slate-300 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          Back
        </button>
        <span>/</span>
        <span className="font-mono">{table.schema_name}</span>
        <span>/</span>
        <span className="text-slate-200 font-mono">{table.table_name}</span>
      </div>

      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div className="flex items-start gap-3">
          <div className="p-2 bg-slate-800 rounded-lg mt-1">
            <Database className="w-5 h-5 text-brand-400" />
          </div>
          <div>
            <div className="flex items-center gap-2 flex-wrap">
              <h1 className="text-xl font-semibold text-slate-100 font-mono">
                {table.table_name}
              </h1>
              <Badge variant="slate">{tableTypeLabel(table.table_type)}</Badge>
              {table.is_pii_flagged && (
                <Badge variant="amber">
                  <ShieldAlert className="w-3 h-3" />
                  PII
                </Badge>
              )}
            </div>
            <p className="text-sm text-slate-500 font-mono mt-0.5">
              {table.schema_name}.{table.table_name}
            </p>
          </div>
        </div>

        <button
          onClick={() => enrichMutation.mutate()}
          disabled={enrichMutation.isPending}
          className="btn-primary shrink-0"
        >
          <Sparkles className="w-4 h-4" />
          {enrichMutation.isPending ? "Enriching…" : "AI Enrich"}
        </button>
      </div>

      {/* Stats row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {[
          { label: "Rows", value: formatNumber(table.row_count) },
          { label: "Size", value: formatBytes(table.size_bytes) },
          { label: "Columns", value: formatNumber(table.column_count) },
          { label: "Scanned", value: timeAgo(table.last_scanned_at) },
        ].map(({ label, value }) => (
          <div key={label} className="card p-3">
            <p className="text-xs text-slate-500">{label}</p>
            <p className="text-lg font-semibold text-slate-100 mt-0.5">{value}</p>
          </div>
        ))}
      </div>

      {/* Tabs */}
      <div className="border-b border-slate-800">
        <div className="flex gap-4">
          {TABS.map(({ id: tabId, label }) => (
            <button
              key={tabId}
              onClick={() => setActiveTab(tabId)}
              className={`pb-3 text-sm font-medium border-b-2 transition-colors ${
                activeTab === tabId
                  ? "border-brand-500 text-brand-400"
                  : "border-transparent text-slate-500 hover:text-slate-300"
              }`}
            >
              {label}
            </button>
          ))}
        </div>
      </div>

      {/* Tab content */}
      {activeTab === "overview" && (
        <div className="grid md:grid-cols-3 gap-6">
          <div className="md:col-span-2 space-y-6">
            <div className="card p-5">
              <h3 className="text-sm font-medium text-slate-400 mb-3">Description</h3>
              <p className="text-slate-200">
                {table.description ?? (
                  <span className="italic text-slate-500">
                    No description yet. Click "AI Enrich" to generate one.
                  </span>
                )}
              </p>
              {table.business_purpose && (
                <div className="mt-4 pt-4 border-t border-slate-800">
                  <h4 className="text-xs font-medium text-slate-500 mb-2">
                    Business Purpose
                  </h4>
                  <p className="text-slate-300 text-sm">{table.business_purpose}</p>
                </div>
              )}
            </div>

            {table.usage_examples.length > 0 && (
              <div className="card p-5">
                <h3 className="text-sm font-medium text-slate-400 mb-3">
                  Usage Examples
                </h3>
                <div className="space-y-3">
                  {table.usage_examples.map((ex, i) => (
                    <pre
                      key={i}
                      className="bg-slate-950 border border-slate-800 rounded-lg p-3 text-xs font-mono text-slate-300 overflow-x-auto whitespace-pre-wrap"
                    >
                      {ex}
                    </pre>
                  ))}
                </div>
              </div>
            )}
          </div>

          <div className="space-y-4">
            <div className="card p-4">
              <h3 className="text-xs font-medium text-slate-500 mb-3">Metadata</h3>
              <dl className="space-y-2 text-sm">
                {[
                  { label: "Owner", value: table.owner ?? "—" },
                  { label: "Source DB", value: table.source_database ?? "—" },
                  { label: "Table type", value: tableTypeLabel(table.table_type) },
                ].map(({ label, value }) => (
                  <div key={label} className="flex justify-between gap-2">
                    <dt className="text-slate-500">{label}</dt>
                    <dd className="text-slate-300 text-right truncate max-w-[150px]">
                      {value}
                    </dd>
                  </div>
                ))}
              </dl>
            </div>

            {table.tag_names.length > 0 && (
              <div className="card p-4">
                <h3 className="text-xs font-medium text-slate-500 mb-3">Tags</h3>
                <div className="flex flex-wrap gap-1">
                  {table.tag_names.map((tag) => (
                    <Badge key={tag} variant="blue">
                      {tag}
                    </Badge>
                  ))}
                </div>
              </div>
            )}

            <div className="card p-4 space-y-2">
              <Link
                href={`/lineage/${id}`}
                className="flex items-center gap-2 text-sm text-slate-400 hover:text-brand-400 transition-colors"
              >
                <GitBranch className="w-4 h-4" />
                View lineage graph
              </Link>
              <Link
                href={`/impact/${id}`}
                className="flex items-center gap-2 text-sm text-slate-400 hover:text-brand-400 transition-colors"
              >
                <Zap className="w-4 h-4" />
                Impact analysis
              </Link>
            </div>
          </div>
        </div>
      )}

      {activeTab === "columns" && cols && (
        <div className="card overflow-hidden">
          <ColumnList columns={cols} />
        </div>
      )}

      {activeTab === "lineage" && (
        <div className="card p-6 flex items-center justify-center h-48 text-slate-500">
          <Link href={`/lineage/${id}`} className="btn-primary">
            <GitBranch className="w-4 h-4" />
            Open Lineage Graph
          </Link>
        </div>
      )}

      {activeTab === "impact" && (
        <div className="card p-6 flex items-center justify-center h-48 text-slate-500">
          <Link href={`/impact/${id}`} className="btn-primary">
            <Zap className="w-4 h-4" />
            Run Impact Analysis
          </Link>
        </div>
      )}
    </div>
  );
}
