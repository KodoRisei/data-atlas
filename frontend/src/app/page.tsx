"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { Database, GitBranch, Shield, Zap } from "lucide-react";
import { tables as tablesApi } from "@/lib/api/client";
import { formatNumber } from "@/lib/utils";
import TableCard from "@/components/tables/TableCard";
import { TableCardSkeleton } from "@/components/ui/Skeleton";

export default function OverviewPage() {
  const { data, isLoading } = useQuery({
    queryKey: ["tables", "recent"],
    queryFn: () => tablesApi.list({ page: 1, page_size: 6 }),
  });

  const { data: piiData } = useQuery({
    queryKey: ["tables", "pii"],
    queryFn: () => tablesApi.list({ pii_only: true, page_size: 1 }),
  });

  const stats = [
    {
      label: "Total Tables",
      value: formatNumber(data?.total),
      icon: Database,
      href: "/tables",
      color: "text-blue-400",
    },
    {
      label: "PII Tables",
      value: formatNumber(piiData?.total),
      icon: Shield,
      href: "/governance",
      color: "text-amber-400",
    },
    {
      label: "Lineage Graph",
      value: "Explore",
      icon: GitBranch,
      href: "/lineage",
      color: "text-emerald-400",
    },
    {
      label: "Impact Analysis",
      value: "Analyze",
      icon: Zap,
      href: "/impact",
      color: "text-purple-400",
    },
  ];

  return (
    <div className="space-y-8 max-w-7xl mx-auto">
      {/* Hero */}
      <div>
        <h1 className="text-2xl font-semibold text-slate-100">DataAtlas</h1>
        <p className="text-slate-400 mt-1">
          AI-powered enterprise data catalog — discover, understand, and trust your data.
        </p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {stats.map(({ label, value, icon: Icon, href, color }) => (
          <Link key={label} href={href}>
            <div className="card p-4 hover:border-slate-700 transition-all cursor-pointer">
              <div className="flex items-center gap-3">
                <div className={`p-2 rounded-lg bg-slate-800 ${color}`}>
                  <Icon className="w-5 h-5" />
                </div>
                <div>
                  <p className="text-xs text-slate-500">{label}</p>
                  <p className="text-xl font-semibold text-slate-100">{value}</p>
                </div>
              </div>
            </div>
          </Link>
        ))}
      </div>

      {/* Recent tables */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="font-medium text-slate-200">Recently Scanned Tables</h2>
          <Link href="/tables" className="text-sm text-brand-400 hover:text-brand-300">
            View all →
          </Link>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {isLoading
            ? Array.from({ length: 6 }).map((_, i) => (
                <TableCardSkeleton key={i} />
              ))
            : data?.items.map((t) => <TableCard key={t.id} table={t} />)}
        </div>
      </div>
    </div>
  );
}
