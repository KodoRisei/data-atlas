"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Database,
  GitBranch,
  Home,
  Search,
  Shield,
  Zap,
} from "lucide-react";
import { cn } from "@/lib/utils";

const NAV = [
  { href: "/", label: "Overview", icon: Home },
  { href: "/tables", label: "Table Explorer", icon: Database },
  { href: "/search", label: "Search", icon: Search },
  { href: "/lineage", label: "Lineage", icon: GitBranch },
  { href: "/governance", label: "Governance", icon: Shield },
  { href: "/impact", label: "Impact", icon: Zap },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-56 shrink-0 bg-slate-900 border-r border-slate-800 flex flex-col">
      {/* Logo */}
      <div className="h-14 flex items-center px-4 border-b border-slate-800">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded bg-brand-500 flex items-center justify-center">
            <Database className="w-4 h-4 text-white" />
          </div>
          <span className="font-semibold text-slate-100">DataAtlas</span>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-2 py-3 space-y-0.5">
        {NAV.map(({ href, label, icon: Icon }) => {
          const active =
            href === "/" ? pathname === "/" : pathname.startsWith(href);
          return (
            <Link
              key={href}
              href={href}
              className={cn(
                "flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors",
                active
                  ? "bg-brand-500/15 text-brand-400 font-medium"
                  : "text-slate-400 hover:text-slate-100 hover:bg-slate-800"
              )}
            >
              <Icon className="w-4 h-4 shrink-0" />
              {label}
            </Link>
          );
        })}
      </nav>

      {/* Footer */}
      <div className="p-4 border-t border-slate-800">
        <p className="text-xs text-slate-600">DataAtlas v0.1.0</p>
      </div>
    </aside>
  );
}
