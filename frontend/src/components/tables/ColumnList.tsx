"use client";

import { ShieldAlert } from "lucide-react";
import type { ColumnSummary } from "@/lib/api/types";
import Badge from "@/components/ui/Badge";

interface ColumnListProps {
  columns: ColumnSummary[];
}

export default function ColumnList({ columns }: ColumnListProps) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-slate-800">
            <th className="text-left py-2 px-3 text-xs font-medium text-slate-500 w-6">
              #
            </th>
            <th className="text-left py-2 px-3 text-xs font-medium text-slate-500">
              Column
            </th>
            <th className="text-left py-2 px-3 text-xs font-medium text-slate-500">
              Type
            </th>
            <th className="text-left py-2 px-3 text-xs font-medium text-slate-500">
              Nullable
            </th>
            <th className="text-left py-2 px-3 text-xs font-medium text-slate-500">
              Description
            </th>
            <th className="text-left py-2 px-3 text-xs font-medium text-slate-500">
              Flags
            </th>
          </tr>
        </thead>
        <tbody>
          {columns.map((col) => (
            <tr
              key={col.id}
              className="border-b border-slate-800/50 hover:bg-slate-800/30 transition-colors"
            >
              <td className="py-2 px-3 text-slate-600 font-mono text-xs">
                {col.ordinal_position}
              </td>
              <td className="py-2 px-3">
                <span className="font-mono text-slate-200">{col.column_name}</span>
              </td>
              <td className="py-2 px-3">
                <Badge variant="slate" className="font-mono">
                  {col.data_type}
                </Badge>
              </td>
              <td className="py-2 px-3 text-slate-500">
                {col.is_nullable ? "yes" : (
                  <span className="text-slate-300">no</span>
                )}
              </td>
              <td className="py-2 px-3 text-slate-400 max-w-xs truncate">
                {col.description ?? (
                  <span className="italic text-slate-600 text-xs">—</span>
                )}
              </td>
              <td className="py-2 px-3">
                {col.is_pii && (
                  <span className="flex items-center gap-1 text-amber-400 text-xs">
                    <ShieldAlert className="w-3 h-3" />
                    {col.pii_type ?? "PII"}
                  </span>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
