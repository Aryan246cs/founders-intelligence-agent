"use client";

import { motion } from "framer-motion";
import { Brain, Zap, TrendingUp, Database, RefreshCw } from "lucide-react";
import { MemoryDiffCard } from "@/components/memory/MemoryDiffCard";
import { Badge } from "@/components/ui/badge";
import { useMemoryComparisons } from "@/hooks/useMemory";

export default function MemoryPage() {
  const { comparisons, stats, loading } = useMemoryComparisons(30_000);

  const withChanges = comparisons.filter((c) => c.hasChanges);

  const memoryStats = [
    { label: "Total Snapshots", value: stats.totalSnapshots > 0 ? stats.totalSnapshots.toLocaleString() : "—", icon: Database, color: "text-purple-400" },
    { label: "Comparisons Run", value: stats.comparisonsRun > 0 ? stats.comparisonsRun.toLocaleString() : "—", icon: Brain, color: "text-brand-400" },
    { label: "Signals Detected", value: stats.signalsDetected > 0 ? stats.signalsDetected.toLocaleString() : "—", icon: Zap, color: "text-amber-400" },
    { label: "Competitors Tracked", value: stats.competitorsTracked > 0 ? stats.competitorsTracked.toLocaleString() : "—", icon: TrendingUp, color: "text-emerald-400" },
  ];

  return (
    <div className="relative min-h-screen">
      <div className="fixed inset-0 grid-bg pointer-events-none opacity-40" />

      {/* Purple glow for memory page */}
      <div className="fixed top-0 right-0 w-[400px] h-[400px] bg-purple-500/5 rounded-full blur-3xl pointer-events-none" />

      <div className="relative px-8 py-8 space-y-8">
        {/* Header */}
        <motion.div initial={{ opacity: 0, y: -8 }} animate={{ opacity: 1, y: 0 }} className="flex items-start justify-between">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <Brain className="w-5 h-5 text-purple-400" />
              <h1 className="text-2xl font-bold text-zinc-100">Memory History</h1>
            </div>
            <p className="text-zinc-500 text-sm max-w-xl">
              The AI remembers, compares, and detects meaningful changes over time. Only high-signal intelligence is surfaced.
            </p>
          </div>
          {loading && (
            <RefreshCw className="w-4 h-4 text-zinc-600 animate-spin" />
          )}
        </motion.div>

        {/* Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {memoryStats.map((stat, i) => {
            const Icon = stat.icon;
            return (
              <motion.div
                key={stat.label}
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.07 }}
                className="glass rounded-xl border border-zinc-800/60 p-5"
              >
                <Icon className={`w-5 h-5 ${stat.color} mb-3`} />
                <p className="text-2xl font-bold text-zinc-100 tabular-nums">{stat.value}</p>
                <p className="text-xs text-zinc-500 mt-1">{stat.label}</p>
              </motion.div>
            );
          })}
        </div>

        {/* Intelligence note */}
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="rounded-xl bg-purple-500/5 border border-purple-500/15 px-5 py-4 flex items-start gap-3"
        >
          <Brain className="w-4 h-4 text-purple-400 flex-shrink-0 mt-0.5" />
          <div>
            <p className="text-xs font-semibold text-purple-400 mb-1">Memory Intelligence System</p>
            <p className="text-xs text-zinc-400 leading-relaxed">
              Only meaningful intelligence changes are surfaced. Low-signal comparisons (no significant changes) are suppressed automatically.
              The system uses semantic similarity, keyword grouping, and fuzzy matching to detect what actually matters.
            </p>
          </div>
        </motion.div>

        {/* Comparisons */}
        <div>
          <div className="flex items-center justify-between mb-5">
            <div>
              <h3 className="text-sm font-semibold text-zinc-200">Intelligence Comparisons</h3>
              <p className="text-xs text-zinc-500 mt-0.5">Showing only runs with detected changes</p>
            </div>
            <Badge variant="warning">{withChanges.length} with changes</Badge>
          </div>

          {/* Loading skeleton */}
          {loading && comparisons.length === 0 && (
            <div className="space-y-4">
              {[1, 2].map((i) => (
                <div key={i} className="glass rounded-xl border border-zinc-800/60 p-6 animate-pulse">
                  <div className="h-4 bg-zinc-800 rounded w-1/3 mb-3" />
                  <div className="h-3 bg-zinc-800/60 rounded w-2/3" />
                </div>
              ))}
            </div>
          )}

          {withChanges.length === 0 && !loading ? (
            <div className="glass rounded-xl border border-zinc-800/60 p-12 text-center">
              <Brain className="w-8 h-8 text-zinc-700 mx-auto mb-3" />
              <p className="text-zinc-500 text-sm">No high-signal changes detected yet.</p>
              <p className="text-zinc-600 text-xs mt-1">Run a workflow to start building memory history.</p>
            </div>
          ) : (
            <div className="space-y-4">
              {withChanges.map((comparison, i) => (
                <MemoryDiffCard key={comparison.id} comparison={comparison} index={i} />
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
