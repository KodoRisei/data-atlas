"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { Zap } from "lucide-react";
import { tables as tablesApi } from "@/lib/api/client";

export default function ImpactIndexPage() {
  const { data } = useQuery({
    queryKey: ["tables", "all"],
    queryFn: () => tablesApi.list({ page_size: 100 }),
  });

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      <div className="flex items-center gap-3">
        <Zap className="w-6 h-6 text-purple-400" />
        <div>
          <h1 className="text-xl font-semibold text-slate-100">
            Impact Analysis
          </h1>
          <p className="text-sm text-slate-500">
            Select a table to run blast-radius analysis.
          </p>
        </div>
      </div>

      <div className="space-y-2">
        {data?.items.map((t) => (
          <Link
            key={t.id}
            href={`/impact/${t.id}`}
            className="flex items-center justify-between p-3 card hover:border-slate-700 transition-all"
          >
            <span className="font-mono text-sm text-slate-300">
              {t.schema_name}.{t.table_name}
            </span>
            <Zap className="w-4 h-4 text-slate-600" />
          </Link>
        ))}
      </div>
    </div>
  );
}
