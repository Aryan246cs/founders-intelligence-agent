"use client";

import { motion } from "framer-motion";
import { Zap, CheckCircle2, XCircle, Clock } from "lucide-react";
import { ExecutionCard } from "@/components/executions/ExecutionCard";
import { Badge } from "@/components/ui/badge";
import { mockExecutions, executionChartData } from "@/lib/mock-data";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from "recharts";

const stats = [
  { label: "Total Executions", value: "47", icon: Zap, color: "text-brand-400" },
  { label: "Completed", value: "44", icon: CheckCircle2, color: "text-emerald-400" },
  { label: "Failed", value: "3", icon: XCircle, color: "text-rose-400" },
  { label: "Avg Duration", value: "2m 18s", icon: Clock, color: "text-amber-400" },
];

export default function ExecutionsPage() {
  return (
    <div className="relative min-h-screen">
      <div className="fixed inset-0 grid-bg pointer-events-none opacity-40" />

      <div className="relative px-8 py-8 space-y-8">
        {/* Header */}
        <motion.div initial={{ opacity: 0, y: -8 }} animate={{ opacity: 1, y: 0 }}>
          <div className="flex items-center gap-2 mb-1">
            <Zap className="w-5 h-5 text-brand-400" />
            <h1 className="text-2xl font-bold text-zinc-100">Workflow Executions</h1>
          </div>
          <p className="text-zinc-500 text-sm">
            AI operations control center — full execution history, agent runs, and orchestration logs.
          </p>
        </motion.div>

        {/* Stats row */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {stats.map((stat, i) => {
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
              <BarChart data={executionChartData} barGap={4}>
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
            <Badge variant="outline">{mockExecutions.length} runs</Badge>
          </div>
          <div className="space-y-4">
            {mockExecutions.map((execution, i) => (
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
