"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { Telescope, Sparkles } from "lucide-react";
import { ResearchLauncher } from "@/components/startup-research/ResearchLauncher";
import { ResearchReport } from "@/components/startup-research/ResearchReport";
import { ResearchHistory } from "@/components/startup-research/ResearchHistory";
import { useStartupResearch } from "@/hooks/useStartupResearch";
import type { StartupResearchReport } from "@/lib/types";

export default function StartupResearchPage() {
  const [activeReport, setActiveReport] = useState<StartupResearchReport | null>(null);
  const { reports, loading, refetch } = useStartupResearch(30_000);

  return (
    <div className="relative min-h-screen">
      {/* Grid background */}
      <div className="fixed inset-0 grid-bg pointer-events-none opacity-50" />
      {/* Purple radial glow — unique to this page */}
      <div className="fixed top-0 left-1/2 -translate-x-1/2 w-[700px] h-[350px] bg-purple-500/4 rounded-full blur-3xl pointer-events-none" />

      <div className="relative px-6 pt-6 pb-16 space-y-6 max-w-7xl">
        {/* Page header */}
        <motion.div
          initial={{ opacity: 0, y: -8 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex items-start justify-between"
        >
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-purple-500/10 border border-purple-500/20 flex items-center justify-center">
              <Telescope className="w-5 h-5 text-purple-400" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-zinc-100 flex items-center gap-2">
                Startup Research
                <span className="text-[10px] font-semibold uppercase tracking-wide bg-purple-500/15 text-purple-300 px-2 py-0.5 rounded-full border border-purple-500/25">
                  Flagship
                </span>
              </h1>
              <p className="text-sm text-zinc-500 mt-0.5">
                Autonomous competitor discovery, pricing intelligence &amp; market analysis
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2 text-xs text-zinc-500">
            <Sparkles className="w-3.5 h-3.5 text-purple-400" />
            <span>Powered by Groq + Apify</span>
          </div>
        </motion.div>

        {/* Main layout: launcher left, report/history right */}
        <div className="grid grid-cols-1 xl:grid-cols-[380px_1fr] gap-6 items-start">
          {/* Left column — launcher + history */}
          <div className="space-y-6">
            <ResearchLauncher
              onReportReady={(report) => {
                setActiveReport(report);
                refetch();
              }}
            />
            <ResearchHistory
              reports={reports}
              loading={loading}
              activeReportId={activeReport?.id}
              onSelect={setActiveReport}
            />
          </div>

          {/* Right column — report viewer */}
          <div>
            {activeReport ? (
              <ResearchReport report={activeReport} />
            ) : (
              <EmptyReportState />
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

function EmptyReportState() {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="h-full min-h-[400px] flex items-center justify-center glass rounded-2xl border border-zinc-800/60"
    >
      <div className="text-center space-y-3 px-8">
        <div className="w-12 h-12 rounded-xl bg-purple-500/10 border border-purple-500/20 flex items-center justify-center mx-auto">
          <Telescope className="w-6 h-6 text-purple-400/60" />
        </div>
        <p className="text-sm font-medium text-zinc-400">No report selected</p>
        <p className="text-xs text-zinc-600 max-w-xs">
          Enter your startup idea and click Generate Research to launch the autonomous research pipeline.
        </p>
      </div>
    </motion.div>
  );
}
