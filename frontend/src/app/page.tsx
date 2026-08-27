"use client";

import { useState } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import { Telescope, Play } from "lucide-react";
import { KpiCard } from "@/components/dashboard/KpiCard";
import { PipelineViz } from "@/components/dashboard/PipelineViz";
import { AgentStatusGrid } from "@/components/dashboard/AgentStatusGrid";
import { ActivityFeed } from "@/components/dashboard/ActivityFeed";
import { ArchitecturePanel } from "@/components/dashboard/ArchitecturePanel";
import { RecentBriefingsPanel } from "@/components/dashboard/RecentBriefingsPanel";
import { GenerateBriefingModal } from "@/components/dashboard/GenerateBriefingModal";
import { SystemStatusBanner } from "@/components/dashboard/SystemStatusBanner";
import { useDashboardStats, useActivityFeed } from "@/hooks/useDashboard";
import { useAgents } from "@/hooks/useAgents";
import { useBriefings } from "@/hooks/useBriefings";
import { useHealth } from "@/hooks/useHealth";

export default function Dashboard() {
  const [briefingModalOpen, setBriefingModalOpen] = useState(false);
  const { kpis } = useDashboardStats(30_000);
  const { events } = useActivityFeed(10_000);
  const { agents } = useAgents(15_000);
  const { briefings, refetch: refetchBriefings } = useBriefings(5, 30_000);
  const { health, loading: healthLoading, online } = useHealth(60_000);

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
                animate={{ scale: online ? [1, 1.2, 1] : 1 }}
                transition={{ duration: 2, repeat: Infinity }}
                className={`w-2 h-2 rounded-full ${
                  online ? "bg-emerald-400" : "bg-rose-400"
                }`}
                style={{
                  boxShadow: online
                    ? "0 0 8px rgba(52,211,153,0.8)"
                    : "0 0 8px rgba(251,113,133,0.8)",
                }}
              />
              <span
                className={`text-xs font-medium uppercase tracking-wider ${
                  online ? "text-emerald-400" : "text-rose-400"
                }`}
              >
                {healthLoading
                  ? "Checking system"
                  : online
                  ? `System ${health?.status ?? "operational"}`
                  : "Backend offline"}
              </span>
            </div>
            <h1 className="text-3xl font-bold text-zinc-100 tracking-tight">
              Founder Intelligence Agent
            </h1>
            <p className="text-zinc-500 mt-1.5 text-sm max-w-lg">
              Autonomous competitive intelligence and execution platform. Monitoring,
              analyzing, and briefing — continuously.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <Link
              href="/startup-research"
              className="flex items-center gap-2 px-4 py-2 rounded-lg bg-zinc-800/60 border border-zinc-700/60 text-sm font-medium text-zinc-300 hover:bg-zinc-800 hover:text-zinc-100 transition-all"
            >
              <Telescope className="w-4 h-4" />
              Research a Startup
            </Link>
            <button
              onClick={() => setBriefingModalOpen(true)}
              className="flex items-center gap-2 px-4 py-2 rounded-lg bg-brand-500 text-sm font-semibold text-white hover:bg-brand-400 transition-all shadow-glow-sm"
            >
              <Play className="w-4 h-4" />
              Generate Briefing
            </button>
          </div>
        </motion.div>

        <SystemStatusBanner health={health} loading={healthLoading} />

        {/* KPI Grid */}
        {kpis.length > 0 ? (
          <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-6 gap-4">
            {kpis.map((kpi, i) => (
              <KpiCard key={kpi.label} {...kpi} index={i} />
            ))}
          </div>
        ) : (
          <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-6 gap-4">
            {Array.from({ length: 6 }).map((_, i) => (
              <div
                key={i}
                className="rounded-xl border border-zinc-800/60 bg-zinc-900/30 p-5 h-[118px] animate-pulse"
              >
                <div className="h-2.5 bg-zinc-800 rounded w-2/3" />
                <div className="h-7 bg-zinc-800/70 rounded w-1/2 mt-3" />
              </div>
            ))}
          </div>
        )}

        {/* Pipeline */}
        <PipelineViz />

        {/* Main content grid */}
        <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
          {/* Left: Agents + Briefings */}
          <div className="xl:col-span-2 min-w-0 space-y-6">
            <AgentStatusGrid agents={agents} />
            <RecentBriefingsPanel briefings={briefings} />
          </div>

          {/* Right: Architecture + Activity */}
          <div className="min-w-0 space-y-6">
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
          // The briefing row is written before the workflow response returns,
          // so an immediate refetch is enough — no artificial delay needed.
          refetchBriefings();
        }}
      />
    </div>
  );
}
