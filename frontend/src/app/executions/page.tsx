"use client";

import { useMemo } from "react";
import { motion } from "framer-motion";
import { Zap, CheckCircle2, XCircle, Clock, RefreshCw } from "lucide-react";
import { ExecutionCard } from "@/components/executions/ExecutionCard";
import { Badge } from "@/components/ui/badge";
import { useExecutions } from "@/hooks/useExecutions";
import { formatDuration } from "@/lib/utils";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from "recharts";
import { useDashboardStats } from "@/hooks/useDashboard";

export default function ExecutionsPage() {
  const { executions, loading, error, refetch } = useExecutions(20, 15_000);
  const { chartData } = useDashboardStats(60_000);

  const stats = useMemo(() => {
    const total = executions.length;
    const completed = executions.filter((e) => e.status === "completed").length;
    const failed = executions.filter((e) => e.status === "failed").length;
    const durations = executions
      .filter((e) => e.durationMs > 0)
      .map((e) => e.durationMs);
    const avgMs = durations.length
      ? durations.reduce((a, b) => a + b, 0) / durations.length
      : 0;
    return { total, completed, failed, avgMs };
  }, [executions]);

  const statCards = [
    { label: "Total Executions", value: String(stats.total), icon: Zap, color: "text-brand-400" },
    { label: "Completed", value: String(stats.completed), icon: CheckCircle2, color: "text-emerald-400" },
    { label: "Failed", value: String(stats.failed), icon: XCircle, color: "text-rose-400" },
    { label: "Avg Duration", value: stats.avgMs > 0 ? formatDuration(stats.avgMs) : "—", icon: Clock, color: "text-amber-400" },
  ];

  return (
    <div className="relative min-h-screen">
      <div className="fixed inset-0 grid-bg pointer-events-none opacity-40" />

      <div className="relative px-8 py-8 space-y-8">
        {/* Header */}
        <motion.div initial={{ opacity: 0, y: -8 }} animate={{ opacity: 1, y: 0 }} className="flex items-start justify-between">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <Zap className="w-5 h-5 text-brand-400" />
              <h1 className="text-2xl font-bold text-zinc-100">Workflow Executions</h1>
            </div>
            <p className="text-zinc-500 text-sm">
              AI operations control center — full execution history, agent runs, and orchestration logs.
            </p>
          </div>
          <button
            onClick={refetch}
            className="w-8 h-8 rounded-lg bg-zinc-800/60 border border-zinc-700/40 flex items-center justify-center hover:bg-zinc-700/60 transition-colors"
            title="Refresh"
          >
            <RefreshCw className={`w-3.5 h-3.5 text-zinc-400 ${loading ? "animate-spin" : ""}`} />
          </button>
        </motion.div>

        {/* Error banner */}
        {error && (
          <div className="rounded-lg bg-amber-500/5 border border-amber-500/20 px-4 py-3 text-xs text-amber-400">
            Showing cached data — {error}
          </div>
        )}

        {/* Stats row */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {statCards.map((stat, i) => {
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

        {/* Chart */}
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="glass rounded-xl border border-zinc-800/60 p-6"
        >
          <div className="mb-5">
            <h3 className="text-sm font-semibold text-zinc-200">Execution History — Last 7 Days</h3>
            <p className="text-xs text-zinc-500 mt-0.5">Completed vs failed workflow runs</p>
          </div>
          <div className="h-40" suppressHydrationWarning>
            <ResponsiveContainer width="100%" height="100%" minHeight={0}>
              <BarChart data={chartData} barGap={4}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" vertical={false} />
                <XAxis dataKey="day" tick={{ fill: "#71717a", fontSize: 11 }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fill: "#71717a", fontSize: 11 }} axisLine={false} tickLine={false} width={24} />
                <Tooltip
                  contentStyle={{ background: "#18181b", border: "1px solid rgba(255,255,255,0.08)", borderRadius: 8, fontSize: 12 }}
                  labelStyle={{ color: "#a1a1aa" }}
                  cursor={{ fill: "rgba(255,255,255,0.03)" }}
                />
                <Bar dataKey="completed" fill="#10b981" radius={[3, 3, 0, 0]} name="Completed" />
                <Bar dataKey="failed" fill="#f43f5e" radius={[3, 3, 0, 0]} name="Failed" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </motion.div>

        {/* Execution list */}
        <div>
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold text-zinc-300">Recent Executions</h3>
            <Badge variant="outline">{executions.length} runs</Badge>
          </div>

          {/* Loading skeleton */}
          {loading && executions.length === 0 && (
            <div className="space-y-4">
              {[1, 2, 3].map((i) => (
                <div key={i} className="glass rounded-xl border border-zinc-800/60 p-6 animate-pulse">
                  <div className="h-4 bg-zinc-800 rounded w-2/3 mb-3" />
                  <div className="h-3 bg-zinc-800/60 rounded w-1/2" />
                </div>
              ))}
            </div>
          )}

          <div className="space-y-4">
            {executions.map((execution, i) => (
              <motion.div
                key={execution.id}
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.3 + i * 0.07 }}
              >
                <ExecutionCard execution={execution} />
              </motion.div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
