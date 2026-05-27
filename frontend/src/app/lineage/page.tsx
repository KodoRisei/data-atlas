"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { GitBranch } from "lucide-react";
import { tables as tablesApi } from "@/lib/api/client";
import { formatNumber } from "@/lib/utils";

export default function LineageIndexPage() {
  const { data } = useQuery({
    queryKey: ["tables", "all"],
    queryFn: () => tablesApi.list({ page_size: 100 }),
  });

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      <div className="flex items-center gap-3">
        <GitBranch className="w-6 h-6 text-emerald-400" />
        <div>
          <h1 className="text-xl font-semibold text-slate-100">Lineage</h1>
          <p className="text-sm text-slate-500">
            Select a table to explore its data lineage.
          </p>
        </div>
      </div>

      <div className="space-y-2">
        {data?.items.map((t) => (
          <Link
            key={t.id}
            href={`/lineage/${t.id}`}
            className="flex items-center justify-between p-3 card hover:border-slate-700 transition-all"
          >
            <div className="flex items-center gap-2">
              <GitBranch className="w-4 h-4 text-slate-500" />
              <span className="font-mono text-sm text-slate-300">
                {t.schema_name}.{t.table_name}
              </span>
            </div>
            {t.row_count != null && (
              <span className="text-xs text-slate-500">
                {formatNumber(t.row_count)} rows
              </span>
            )}
          </Link>
        ))}
      </div>
    </div>
  );
}
