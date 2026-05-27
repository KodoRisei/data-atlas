"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { tables as tablesApi } from "@/lib/api/client";
import TableCard from "@/components/tables/TableCard";
import { TableCardSkeleton } from "@/components/ui/Skeleton";
import type { TableType } from "@/lib/api/types";

const TABLE_TYPES: { label: string; value: TableType | "" }[] = [
  { label: "All", value: "" },
  { label: "Tables", value: "table" },
  { label: "Views", value: "view" },
  { label: "Mat. Views", value: "materialized_view" },
];

export default function TablesPage() {
  const [page, setPage] = useState(1);
  const [typeFilter, setTypeFilter] = useState<TableType | "">("");
  const [piiOnly, setPiiOnly] = useState(false);
  const PAGE_SIZE = 21;

  const { data, isLoading } = useQuery({
    queryKey: ["tables", { page, typeFilter, piiOnly }],
    queryFn: () =>
      tablesApi.list({
        page,
        page_size: PAGE_SIZE,
        table_type: typeFilter || undefined,
        pii_only: piiOnly,
      }),
  });

  const totalPages = data ? Math.ceil(data.total / PAGE_SIZE) : 1;

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-slate-100">Table Explorer</h1>
          <p className="text-sm text-slate-500 mt-0.5">
            {data?.total != null ? `${data.total} tables` : "Loading…"}
          </p>
        </div>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-1 bg-slate-900 border border-slate-800 rounded-lg p-1">
          {TABLE_TYPES.map(({ label, value }) => (
            <button
              key={label}
              onClick={() => { setTypeFilter(value); setPage(1); }}
              className={`px-3 py-1.5 rounded text-sm font-medium transition-colors ${
                typeFilter === value
                  ? "bg-brand-500 text-white"
                  : "text-slate-400 hover:text-slate-100"
              }`}
            >
              {label}
            </button>
          ))}
        </div>

        <label className="flex items-center gap-2 text-sm text-slate-400 cursor-pointer">
          <input
            type="checkbox"
            checked={piiOnly}
            onChange={(e) => { setPiiOnly(e.target.checked); setPage(1); }}
            className="rounded border-slate-700 bg-slate-800 text-brand-500"
          />
          PII only
        </label>
      </div>

      {/* Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
        {isLoading
          ? Array.from({ length: 9 }).map((_, i) => <TableCardSkeleton key={i} />)
          : data?.items.map((t) => <TableCard key={t.id} table={t} />)}
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-center gap-2">
          <button
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={page === 1}
            className="btn-ghost disabled:opacity-40"
          >
            Previous
          </button>
          <span className="text-sm text-slate-500">
            {page} / {totalPages}
          </span>
          <button
            onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
            disabled={page === totalPages}
            className="btn-ghost disabled:opacity-40"
          >
            Next
          </button>
        </div>
      )}
    </div>
  );
}
