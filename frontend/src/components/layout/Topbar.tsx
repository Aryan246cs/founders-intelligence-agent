"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Search, Bell, Zap, ChevronDown } from "lucide-react";
import { useActivityFeed } from "@/hooks/useDashboard";
import { useAgents } from "@/hooks/useAgents";

export function Topbar() {
  const [showNotifs, setShowNotifs] = useState(false);
  const { events } = useActivityFeed(10_000);
  const { agents } = useAgents(15_000);

  const activeCount = agents.filter((a) => a.status === "active" || a.status === "running").length;
  const hasRunning = agents.some((a) => a.status === "running");
  const unread = Math.min(events.filter((e) => e.type === "warning" || e.type === "error").length, 9);

  return (
    <header className="fixed top-0 left-60 right-0 h-14 border-b border-zinc-800/60 bg-zinc-950/80 backdrop-blur-xl z-30 flex items-center px-6 gap-4">
      {/* Search */}
      <div className="flex-1 max-w-sm">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-zinc-500" />
          <input
            type="text"
            placeholder="Search briefings, executions..."
            className="w-full bg-zinc-900/60 border border-zinc-800 rounded-lg pl-9 pr-4 py-1.5 text-sm text-zinc-300 placeholder:text-zinc-600 focus:outline-none focus:border-brand-500/50 focus:bg-zinc-900 transition-all"
          />
        </div>
      </div>

      <div className="flex items-center gap-3 ml-auto">
        {/* AI Status */}
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-emerald-500/5 border border-emerald-500/15">
          <motion.div
            animate={{ scale: [1, 1.3, 1] }}
            transition={{ duration: 2, repeat: Infinity }}
            className="w-1.5 h-1.5 rounded-full bg-emerald-400"
            style={{ boxShadow: "0 0 6px rgba(52,211,153,0.8)" }}
          />
          <span className="text-xs font-medium text-emerald-400">
            {activeCount > 0 ? `${activeCount} Agents Active` : "Agents Idle"}
          </span>
        </div>

        {/* Agent pulse — only when something is running */}
        {hasRunning && (
          <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-brand-500/5 border border-brand-500/15">
            <Zap className="w-3.5 h-3.5 text-brand-400" />
            <span className="text-xs font-medium text-brand-400">Running</span>
          </div>
        )}

        {/* Notifications */}
        <div className="relative">
          <button
            onClick={() => setShowNotifs(!showNotifs)}
            className="relative w-8 h-8 rounded-lg bg-zinc-900 border border-zinc-800 flex items-center justify-center hover:border-zinc-700 transition-colors"
          >
            <Bell className="w-4 h-4 text-zinc-400" />
            {unread > 0 && (
              <span className="absolute -top-1 -right-1 w-4 h-4 rounded-full bg-brand-500 text-[9px] font-bold text-white flex items-center justify-center">
                {unread}
              </span>
            )}
          </button>

          <AnimatePresence>
            {showNotifs && (
              <motion.div
                initial={{ opacity: 0, y: 8, scale: 0.95 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, y: 8, scale: 0.95 }}
                transition={{ duration: 0.15 }}
                className="absolute right-0 top-10 w-80 glass rounded-xl shadow-glass border border-zinc-800/60 overflow-hidden"
              >
                <div className="px-4 py-3 border-b border-zinc-800/60">
                  <p className="text-sm font-semibold text-zinc-200">Recent Activity</p>
                </div>
                <div className="max-h-72 overflow-y-auto">
                  {events.slice(0, 6).map((event) => (
                    <div key={event.id} className="px-4 py-3 border-b border-zinc-800/30 hover:bg-zinc-800/20 transition-colors">
                      <p className="text-xs text-zinc-300">{event.message}</p>
                      <p className="text-[10px] text-zinc-600 mt-1">{event.timestamp} · {event.agent}</p>
                    </div>
                  ))}
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* Profile */}
        <button className="flex items-center gap-2 px-2 py-1.5 rounded-lg hover:bg-zinc-800/50 transition-colors">
          <div className="w-6 h-6 rounded-full bg-gradient-to-br from-brand-500 to-purple-600 flex items-center justify-center text-[10px] font-bold text-white">F</div>
          <span className="text-xs font-medium text-zinc-300">Founder</span>
          <ChevronDown className="w-3 h-3 text-zinc-500" />
        </button>
      </div>
    </header>
  );
}
