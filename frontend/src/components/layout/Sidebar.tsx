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
  Slack,
  Database,
  Activity,
  ChevronRight,
  Telescope,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useHealth } from "@/hooks/useHealth";

const navItems = [
  { href: "/", label: "Dashboard", icon: LayoutDashboard },
  { href: "/briefings", label: "Briefings", icon: FileText },
  { href: "/executions", label: "Executions", icon: Zap },
  { href: "/memory", label: "Memory History", icon: Brain },
  {
    href: "/startup-research",
    label: "Startup Research",
    icon: Telescope,
    highlight: true,
  },
  { href: "/settings", label: "Settings", icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();
  // Real probe results, refreshed every minute — not a decorative row of dots.
  const { health, loading: healthLoading } = useHealth(60_000);

  return (
    <aside className="fixed left-0 top-0 h-screen w-60 flex flex-col border-r border-zinc-800/60 bg-zinc-950/80 backdrop-blur-xl z-40">
      {/* Logo */}
      <div className="px-5 py-5 border-b border-zinc-800/60">
        <div className="flex items-center gap-2.5">
          <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-brand-500 to-purple-600 flex items-center justify-center shadow-glow-sm">
            <Activity className="w-4 h-4 text-white" />
          </div>
          <div>
            <p className="text-sm font-semibold text-zinc-100 leading-none">Founder Intel</p>
            <p className="text-[10px] text-zinc-500 mt-0.5">Agent Platform</p>
          </div>
        </div>
      </div>

      {/* Nav */}
      <nav className="flex-1 px-3 py-4 space-y-0.5 overflow-y-auto">
        {navItems.map((item) => {
          const Icon = item.icon;
          const active = pathname === item.href;
          const isHighlight = (item as { highlight?: boolean }).highlight;
          return (
            <Link key={item.href} href={item.href}>
              <motion.div
                whileHover={{ x: 2 }}
                className={cn(
                  "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-150 group relative",
                  active
                    ? "bg-brand-500/10 text-brand-400 border border-brand-500/20"
                    : isHighlight
                    ? "text-purple-300 hover:text-purple-200 hover:bg-purple-500/10 border border-purple-500/20 bg-purple-500/5"
                    : "text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800/50"
                )}
              >
                {active && (
                  <motion.div
                    layoutId="sidebar-active"
                    className="absolute inset-0 rounded-lg bg-brand-500/5"
                  />
                )}
                <Icon
                  className={cn(
                    "w-4 h-4 flex-shrink-0",
                    active
                      ? "text-brand-400"
                      : isHighlight
                      ? "text-purple-400"
                      : "text-zinc-500 group-hover:text-zinc-300"
                  )}
                />
                <span className="relative flex-1">{item.label}</span>
                {isHighlight && !active && (
                  <span className="text-[9px] font-bold uppercase tracking-wide bg-purple-500/20 text-purple-300 px-1.5 py-0.5 rounded-full border border-purple-500/30">
                    New
                  </span>
                )}
                {active && <ChevronRight className="w-3 h-3 ml-auto text-brand-400/60" />}
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
        <div className="pt-2 border-t border-zinc-800/40">
          <div className="flex items-center gap-2 px-1">
            <div className="w-6 h-6 rounded-full bg-gradient-to-br from-brand-500 to-purple-600 flex items-center justify-center text-[10px] font-bold text-white">F</div>
            <div>
              <p className="text-xs font-medium text-zinc-300">Founder</p>
              <p className="text-[10px] text-zinc-600">Pro Plan</p>
            </div>
          </div>
        </div>
      </div>
    </aside>
  );
}
