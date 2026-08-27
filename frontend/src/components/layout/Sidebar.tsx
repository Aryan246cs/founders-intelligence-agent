"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { motion } from "framer-motion";
import {
  LayoutDashboard,
  FileText,
  Zap,
  Brain,
  Settings,
  Telescope,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useHealth } from "@/hooks/useHealth";
import { Logomark } from "@/components/brand/Logomark";
import { Avatar } from "@/components/brand/Avatar";
import { WORKSPACE } from "@/lib/workspace";

const navItems = [
  { href: "/", label: "Dashboard", icon: LayoutDashboard },
  { href: "/briefings", label: "Briefings", icon: FileText },
  { href: "/executions", label: "Executions", icon: Zap },
  { href: "/memory", label: "Memory History", icon: Brain },
  { href: "/startup-research", label: "Startup Research", icon: Telescope },
  { href: "/settings", label: "Settings", icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();
  // Real probe results, refreshed every minute — not a decorative row of dots.
  const { health, loading: healthLoading } = useHealth(60_000);

  return (
    <aside className="fixed left-0 top-0 h-screen w-60 flex flex-col border-r border-zinc-800/60 bg-zinc-950/80 backdrop-blur-xl z-40">
      {/* Wordmark */}
      <div className="px-5 h-14 flex items-center border-b border-zinc-800/60">
        <div className="flex items-center gap-2.5">
          <Logomark className="w-[18px] h-[18px] text-zinc-200" />
          <div className="flex items-baseline gap-1.5">
            <p className="text-[13px] font-semibold text-zinc-100 leading-none tracking-tight">
              {WORKSPACE.productName}
            </p>
            <span className="text-[10px] font-mono text-zinc-600 leading-none">
              {WORKSPACE.version}
            </span>
          </div>
        </div>
      </div>

      {/* Nav */}
      <nav className="flex-1 px-3 py-4 space-y-0.5 overflow-y-auto">
        {navItems.map((item) => {
          const Icon = item.icon;
          const active = pathname === item.href;
          return (
            <Link key={item.href} href={item.href}>
              <motion.div
                whileHover={{ x: 2 }}
                className={cn(
                  "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-150 group relative",
                  active
                    ? "bg-zinc-800/70 text-zinc-100"
                    : "text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800/40"
                )}
              >
                {active && (
                  <motion.span
                    layoutId="sidebar-active"
                    className="absolute left-0 top-1.5 bottom-1.5 w-0.5 rounded-full bg-zinc-300"
                  />
                )}
                <Icon
                  className={cn(
                    "w-4 h-4 flex-shrink-0",
                    active ? "text-zinc-200" : "text-zinc-500 group-hover:text-zinc-300"
                  )}
                />
                <span className="relative flex-1">{item.label}</span>
              </motion.div>
            </Link>
          );
        })}
      </nav>

      {/* Status footer — live dependency health */}
      <div className="px-4 py-4 border-t border-zinc-800/60 space-y-2.5">
        <p className="text-[10px] font-semibold text-zinc-600 uppercase tracking-wider px-1">Integrations</p>
        {healthLoading && !health && (
          <p className="text-xs text-zinc-600 px-1">Checking…</p>
        )}
        {health?.services.map((service) => (
          <div
            key={service.name}
            className="flex items-center gap-2.5 px-1"
            title={service.detail}
          >
            <span
              className={cn(
                "flex-shrink-0",
                service.ok
                  ? "status-dot-green"
                  : service.configured
                  ? "status-dot-red"
                  : "status-dot-amber"
              )}
              style={{ width: 6, height: 6, borderRadius: "50%", display: "inline-block" }}
            />
            <span
              className={cn(
                "text-xs truncate",
                service.ok ? "text-zinc-400" : "text-zinc-500"
              )}
            >
              {service.name}
            </span>
            {!service.ok && (
              <span
                className={cn(
                  "text-[9px] ml-auto flex-shrink-0",
                  service.configured ? "text-rose-400" : "text-amber-400/70"
                )}
              >
                {service.configured ? "error" : "off"}
              </span>
            )}
          </div>
        ))}
        <div className="pt-3 mt-1 border-t border-zinc-800/40">
          <div className="flex items-center gap-2.5 px-1">
            <Avatar name={WORKSPACE.userName} className="w-6 h-6 text-[10px]" />
            <div className="min-w-0">
              <p className="text-xs font-medium text-zinc-300 truncate">
                {WORKSPACE.userName}
              </p>
              <p className="text-[10px] text-zinc-600 truncate">
                {WORKSPACE.workspaceName}
              </p>
            </div>
          </div>
        </div>
      </div>
    </aside>
  );
}
