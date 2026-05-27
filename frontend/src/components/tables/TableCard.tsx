import Link from "next/link";
import { Database, Eye, ShieldAlert, Table2 } from "lucide-react";
import type { TableSummary } from "@/lib/api/types";
import { formatNumber, tableTypeLabel, timeAgo } from "@/lib/utils";
import Badge from "@/components/ui/Badge";

interface TableCardProps {
  table: TableSummary;
}

const TYPE_ICONS: Record<string, React.ReactNode> = {
  table: <Table2 className="w-4 h-4" />,
  view: <Eye className="w-4 h-4" />,
  materialized_view: <Database className="w-4 h-4" />,
};

export default function TableCard({ table }: TableCardProps) {
  return (
    <Link href={`/tables/${table.id}`}>
      <div className="card p-4 hover:border-slate-700 hover:bg-slate-900/80 transition-all cursor-pointer group">
        {/* Header row */}
        <div className="flex items-start justify-between gap-2 mb-2">
          <div className="flex items-center gap-2 min-w-0">
            <span className="text-slate-500 shrink-0">
              {TYPE_ICONS[table.table_type] ?? <Database className="w-4 h-4" />}
            </span>
            <div className="min-w-0">
              <p className="text-xs text-slate-500 font-mono truncate">
                {table.schema_name}
              </p>
              <p className="font-medium text-slate-100 truncate group-hover:text-brand-400 transition-colors">
                {table.table_name}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-1 shrink-0">
            {table.is_pii_flagged && (
              <span title="Contains PII">
                <ShieldAlert className="w-4 h-4 text-amber-400" />
              </span>
            )}
            <Badge variant="slate">{tableTypeLabel(table.table_type)}</Badge>
          </div>
        </div>

        {/* Description */}
        <p className="text-sm text-slate-400 line-clamp-2 mb-3 min-h-[2.5rem]">
          {table.description ?? (
            <span className="italic text-slate-600">No description yet</span>
          )}
        </p>

        {/* Footer */}
        <div className="flex items-center justify-between text-xs text-slate-500">
          <div className="flex items-center gap-3">
            {table.row_count != null && (
              <span>{formatNumber(table.row_count)} rows</span>
            )}
            {table.owner && <span>@{table.owner}</span>}
          </div>
          <span>{timeAgo(table.last_scanned_at)}</span>
        </div>

        {/* Tags */}
        {table.tag_names.length > 0 && (
          <div className="flex flex-wrap gap-1 mt-2">
            {table.tag_names.slice(0, 4).map((tag) => (
              <Badge key={tag} variant="blue" className="text-xs">
                {tag}
              </Badge>
            ))}
          </div>
        )}
      </div>
    </Link>
  );
}
