"use client";

import { motion } from "framer-motion";
import { Clock, ChevronRight, Loader2, Telescope } from "lucide-react";
import { cn } from "@/lib/utils";
import { startupResearchService } from "@/services/startupResearch";
import type { StartupResearchListItem, StartupResearchReport } from "@/lib/types";

interface Props {
  reports: StartupResearchListItem[];
  loading: boolean;
  activeReportId?: string;
  onSelect: (report: StartupResearchReport) => void;
}

export function ResearchHistory({ reports, loading, activeReportId, onSelect }: Props) {
  const handleSelect = async (item: StartupResearchListItem) => {
    const full = await startupResearchService.get(item.id);
    onSelect(full);
  };

  const formatDate = (iso: string) => {
    const d = new Date(iso);
    return d.toLocaleDateString("en-US", { month: "short", day: "numeric" });
  };

  const scoreColor = (score: number) => {
    if (score >= 80) return "text-emerald-400";
    if (score >= 50) return "text-amber-400";
    return "text-rose-400";
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.1 }}
      className="glass rounded-2xl border border-zinc-800/60 overflow-hidden"
    >
      <div className="px-5 py-4 border-b border-zinc-800/60 flex items-center gap-2">
        <Clock className="w-4 h-4 text-zinc-500" />
        <p className="text-sm font-semibold text-zinc-300">Research History</p>
        {!loading && (
          <span className="ml-auto text-xs text-zinc-600">{reports.length} reports</span>
        )}
      </div>

      <div className="divide-y divide-zinc-800/40">
        {loading && (
          <div className="flex items-center gap-2 px-5 py-4 text-zinc-600">
            <Loader2 className="w-4 h-4 animate-spin" />
            <span className="text-xs">Loading history…</span>
          </div>
        )}

        {!loading && reports.length === 0 && (
          <div className="px-5 py-8 text-center">
            <Telescope className="w-6 h-6 text-zinc-700 mx-auto mb-2" />
            <p className="text-xs text-zinc-600">No research reports yet</p>
          </div>
        )}

        {reports.map((item, i) => (
          <motion.button
            key={item.id}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: i * 0.04 }}
            onClick={() => handleSelect(item)}
            className={cn(
              "w-full px-5 py-3.5 text-left flex items-start gap-3 hover:bg-zinc-800/30 transition-all group",
              activeReportId === item.id && "bg-purple-500/5 border-l-2 border-purple-500/50"
            )}
          >
            <div className="flex-1 min-w-0">
              <p className="text-xs font-medium text-zinc-300 truncate leading-snug">
                {item.startup_name ? `${item.startup_name} — ` : ""}
                {item.startup_idea}
              </p>
              <div className="flex items-center gap-3 mt-1">
                <span className="text-[10px] text-zinc-600">{formatDate(item.created_at)}</span>
                <span className="text-[10px] text-zinc-600">
                  {item.industry}
                </span>
                <span className="text-[10px] text-zinc-600">
                  {item.competitors_found} competitors
                </span>
              </div>
            </div>
            <div className="flex items-center gap-2 flex-shrink-0">
              <span className={cn("text-xs font-semibold tabular-nums", scoreColor(item.research_score))}>
                {item.research_score}
              </span>
              <ChevronRight className="w-3.5 h-3.5 text-zinc-700 group-hover:text-zinc-400 transition-colors" />
            </div>
          </motion.button>
        ))}
      </div>
    </motion.div>
  );
}
