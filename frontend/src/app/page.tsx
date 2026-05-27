"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { Zap, Play } from "lucide-react";
import { KpiCard } from "@/components/dashboard/KpiCard";
import { PipelineViz } from "@/components/dashboard/PipelineViz";
import { AgentStatusGrid } from "@/components/dashboard/AgentStatusGrid";
import { ActivityFeed } from "@/components/dashboard/ActivityFeed";
import { ArchitecturePanel } from "@/components/dashboard/ArchitecturePanel";
import { RecentBriefingsPanel } from "@/components/dashboard/RecentBriefingsPanel";
import { GenerateBriefingModal } from "@/components/dashboard/GenerateBriefingModal";
import { useDashboardStats, useActivityFeed } from "@/hooks/useDashboard";
import { useAgents } from "@/hooks/useAgents";
import { useBriefings } from "@/hooks/useBriefings";

export default function Dashboard() {
  const [briefingModalOpen, setBriefingModalOpen] = useState(false);
  const { kpis, chartData, loading: statsLoading } = useDashboardStats(30_000);
  const { events } = useActivityFeed(10_000);
  const { agents } = useAgents(15_000);
  const { briefings, refetch: refetchBriefings } = useBriefings(5, 30_000);

  return (
    <div className="relative min-h-screen">
      {/* Grid background */}
      <div className="fixed inset-0 grid-bg pointer-events-none opacity-50" />

      {/* Radial glow */}
      <div className="fixed top-0 left-1/2 -translate-x-1/2 w-[600px] h-[300px] bg-brand-500/5 rounded-full blur-3xl pointer-events-none" />

      <div className="relative px-8 py-8 space-y-8">
        {/* Hero */}
        <motion.div
          initial={{ opacity: 0, y: -12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="flex items-start justify-between"
        >
          <div>
            <div className="flex items-center gap-2 mb-2">
              <motion.div
                animate={{ scale: [1, 1.2, 1] }}
                transition={{ duration: 2, repeat: Infinity }}
                className="w-2 h-2 rounded-full bg-emerald-400"
                style={{ boxShadow: "0 0 8px rgba(52,211,153,0.8)" }}
              />
              <span className="text-xs font-medium text-emerald-400 uppercase tracking-wider">System Operational</span>
            </div>
            <h1 className="text-3xl font-bold text-zinc-100 tracking-tight">
              Founder Intelligence Agent
            </h1>
            <p className="text-zinc-500 mt-1.5 text-sm max-w-lg">
              Autonomous competitive intelligence and execution platform. Monitoring, analyzing, and briefing — continuously.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <button className="flex items-center gap-2 px-4 py-2 rounded-lg bg-zinc-800/60 border border-zinc-700/60 text-sm font-medium text-zinc-300 hover:bg-zinc-800 hover:text-zinc-100 transition-all">
              <Zap className="w-4 h-4" />
              Run Workflow
            </button>
            <button
              onClick={() => setBriefingModalOpen(true)}
              className="flex items-center gap-2 px-4 py-2 rounded-lg bg-brand-500 text-sm font-semibold text-white hover:bg-brand-400 transition-all shadow-glow-sm"
            >
              <Play className="w-4 h-4" />
              Generate Briefing
            </button>
          </div>
        </motion.div>

        {/* KPI Grid */}
        <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-6 gap-4">
          {kpis.map((kpi, i) => (
            <KpiCard key={kpi.label} {...kpi} index={i} />
          ))}
        </div>

        {/* Pipeline */}
        <PipelineViz />

        {/* Main content grid */}
        <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
          {/* Left: Agents + Briefings */}
          <div className="xl:col-span-2 space-y-6">
            <AgentStatusGrid agents={agents} />
            <RecentBriefingsPanel briefings={briefings} />
          </div>

          {/* Right: Architecture + Activity */}
          <div className="space-y-6">
            <ActivityFeed events={events} />
            <ArchitecturePanel />
          </div>
        </div>
      </div>

      {/* Generate Briefing Modal */}
      <GenerateBriefingModal
        open={briefingModalOpen}
        onClose={() => setBriefingModalOpen(false)}
        onComplete={() => {
          setBriefingModalOpen(false);
          // Refresh briefings after a short delay to let DB write complete
          setTimeout(refetchBriefings, 2000);
        }}
      />
    </div>
  );
}
