"use client";

import { useSearchParams, useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { useState, Suspense } from "react";
import { Search } from "lucide-react";
import { tables as tablesApi } from "@/lib/api/client";
import TableCard from "@/components/tables/TableCard";
import { Skeleton } from "@/components/ui/Skeleton";

function SearchContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const initialQuery = searchParams.get("q") ?? "";
  const [input, setInput] = useState(initialQuery);

  const { data, isLoading } = useQuery({
    queryKey: ["search", initialQuery],
    queryFn: () => tablesApi.search(initialQuery, 30),
    enabled: initialQuery.length > 0,
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (input.trim()) {
      router.push(`/search?q=${encodeURIComponent(input.trim())}`);
    }
  };

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      <h1 className="text-xl font-semibold text-slate-100">Search</h1>

      <form onSubmit={handleSubmit}>
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-500" />
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Search tables, descriptions, columns…"
            className="input w-full pl-10 text-base py-3"
            autoFocus
          />
        </div>
      </form>

      {initialQuery && (
        <div>
          <p className="text-sm text-slate-500 mb-4">
            {isLoading
              ? "Searching…"
              : `${data?.length ?? 0} results for "${initialQuery}"`}
          </p>

          {isLoading ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {Array.from({ length: 4 }).map((_, i) => (
                <Skeleton key={i} className="h-32" />
              ))}
            </div>
          ) : data?.length === 0 ? (
            <div className="text-center py-16 text-slate-500">
              <Search className="w-10 h-10 mx-auto mb-3 opacity-30" />
              <p>No tables found matching "{initialQuery}"</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {data?.map((t) => <TableCard key={t.id} table={t} />)}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default function SearchPage() {
  return (
    <Suspense>
      <SearchContent />
    </Suspense>
  );
}
