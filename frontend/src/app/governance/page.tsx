"use client";

import { useQuery } from "@tanstack/react-query";
import { Shield, ShieldAlert } from "lucide-react";
import { tables as tablesApi } from "@/lib/api/client";
import TableCard from "@/components/tables/TableCard";
import { TableCardSkeleton } from "@/components/ui/Skeleton";

export default function GovernancePage() {
  const { data, isLoading } = useQuery({
    queryKey: ["tables", "pii"],
    queryFn: () => tablesApi.list({ pii_only: true, page_size: 50 }),
  });

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      <div className="flex items-center gap-3">
        <Shield className="w-6 h-6 text-amber-400" />
        <div>
          <h1 className="text-xl font-semibold text-slate-100">
            Data Governance
          </h1>
          <p className="text-sm text-slate-500">
            Tables flagged as containing personally identifiable information.
          </p>
        </div>
      </div>

      {!isLoading && data?.total === 0 && (
        <div className="card p-12 text-center">
          <Shield className="w-10 h-10 text-emerald-400 mx-auto mb-3" />
          <p className="text-slate-300 font-medium">No PII detected</p>
          <p className="text-sm text-slate-500 mt-1">
            No tables have been flagged for PII. Run an ingestion scan to detect
            sensitive columns automatically.
          </p>
        </div>
      )}

      {data && data.total > 0 && (
        <>
          <div className="card p-4 flex items-center gap-3 border-amber-500/20 bg-amber-500/5">
            <ShieldAlert className="w-5 h-5 text-amber-400 shrink-0" />
            <p className="text-sm text-amber-200">
              <strong>{data.total} tables</strong> contain columns matching PII
              naming patterns. Review and classify these tables appropriately.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
            {data.items.map((t) => (
              <TableCard key={t.id} table={t} />
            ))}
          </div>
        </>
      )}

      {isLoading && (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {Array.from({ length: 6 }).map((_, i) => (
            <TableCardSkeleton key={i} />
          ))}
        </div>
      )}
    </div>
  );
}
