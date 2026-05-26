"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ChevronDown, Brain, TrendingUp, Plus, Minus, ArrowRight, Zap } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { cn, formatDate } from "@/lib/utils";
import type { MemoryComparison } from "@/lib/types";

const changeTypeColors: Record<string, string> = {
  pricing: "text-amber-400 bg-amber-500/10 border-amber-500/20",
  product_launch: "text-brand-400 bg-brand-500/10 border-brand-500/20",
  model_release: "text-purple-400 bg-purple-500/10 border-purple-500/20",
  partnership: "text-emerald-400 bg-emerald-500/10 border-emerald-500/20",
  enterprise: "text-violet-400 bg-violet-500/10 border-violet-500/20",
  funding: "text-rose-400 bg-rose-500/10 border-rose-500/20",
  general: "text-zinc-400 bg-zinc-500/10 border-zinc-500/20",
};

interface MemoryDiffCardProps {
  comparison: MemoryComparison;
  index: number;
}

export function MemoryDiffCard({ comparison, index }: MemoryDiffCardProps) {
  const [expanded, setExpanded] = useState(index === 0);

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.1 }}
      className="glass glass-hover rounded-xl border border-zinc-800/60 overflow-hidden"
    >
      {/* Header */}
      <div
        className="px-6 py-5 cursor-pointer"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex items-start justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-purple-500/10 border border-purple-500/20 flex items-center justify-center flex-shrink-0">
              <Brain className="w-4 h-4 text-purple-400" />
            </div>
            <div>
              <div className="flex items-center gap-2 mb-1">
                <h3 className="text-sm font-semibold text-zinc-200">{comparison.competitor}</h3>
                <Badge variant="warning">{comparison.changes.length} changes</Badge>
              </div>
              <p className="text-xs text-zinc-500">{formatDate(comparison.comparedAt)}</p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {/* Change type badges */}
            <div className="hidden md:flex gap-1.5">
              {[...new Set(comparison.changes.map((c) => c.type))].map((type) => (
                <span
                  key={type}
                  className={cn("text-[10px] font-medium px-2 py-0.5 rounded border capitalize", changeTypeColors[type] ?? changeTypeColors.general)}
                >
                  {type.replace("_", " ")}
                </span>
              ))}
            </div>
            <motion.div animate={{ rotate: expanded ? 180 : 0 }} transition={{ duration: 0.2 }}>
              <ChevronDown className="w-4 h-4 text-zinc-500" />
            </motion.div>
          </div>
        </div>

        {/* Detected signal — always visible */}
        <div className="mt-4 flex items-start gap-2 rounded-lg bg-amber-500/5 border border-amber-500/15 px-4 py-3">
          <Zap className="w-3.5 h-3.5 text-amber-400 flex-shrink-0 mt-0.5" />
          <div>
            <p className="text-[10px] font-semibold text-amber-400 uppercase tracking-wider mb-1">Detected Signal</p>
            <p className="text-xs text-zinc-300 leading-relaxed">{comparison.detectedSignal}</p>
          </div>
        </div>
      </div>

      {/* Expanded: diff view */}
      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.3 }}
            className="overflow-hidden"
          >
            <div className="px-6 pb-6 border-t border-zinc-800/40 pt-5 space-y-5">
              {/* Memory diff visualization */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Previous */}
                <div className="rounded-xl bg-zinc-900/60 border border-zinc-700/40 overflow-hidden">
                  <div className="px-4 py-2.5 border-b border-zinc-700/40 flex items-center gap-2 bg-zinc-800/30">
                    <Minus className="w-3.5 h-3.5 text-rose-400" />
                    <span className="text-xs font-semibold text-zinc-400">Previous Memory</span>
                    <span className="text-[10px] text-zinc-600 ml-auto">{formatDate(comparison.previousSnapshot.capturedAt)}</span>
                  </div>
                  <div className="p-4 space-y-2">
                    <p className="text-xs text-zinc-400 leading-relaxed">{comparison.previousSnapshot.summary}</p>
                    <div className="space-y-1 mt-3">
                      {comparison.previousSnapshot.keyPoints.map((point, i) => (
                        <div key={i} className="flex items-start gap-2">
                          <div className="w-1 h-1 rounded-full bg-zinc-600 mt-1.5 flex-shrink-0" />
                          <p className="text-[11px] text-zinc-500">{point}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>

                {/* Arrow */}
                <div className="hidden md:flex items-center justify-center absolute left-1/2 -translate-x-1/2 mt-12">
                  <ArrowRight className="w-5 h-5 text-zinc-700" />
                </div>

                {/* Current */}
                <div className="rounded-xl bg-zinc-900/60 border border-emerald-500/20 overflow-hidden">
                  <div className="px-4 py-2.5 border-b border-emerald-500/15 flex items-center gap-2 bg-emerald-500/5">
                    <Plus className="w-3.5 h-3.5 text-emerald-400" />
                    <span className="text-xs font-semibold text-emerald-400">Current Memory</span>
                    <span className="text-[10px] text-zinc-600 ml-auto">{formatDate(comparison.currentSnapshot.capturedAt)}</span>
                  </div>
                  <div className="p-4 space-y-2">
                    <p className="text-xs text-zinc-300 leading-relaxed">{comparison.currentSnapshot.summary}</p>
                    <div className="space-y-1 mt-3">
                      {comparison.currentSnapshot.keyPoints.map((point, i) => {
                        const isNew = !comparison.previousSnapshot.keyPoints.includes(point);
                        return (
                          <div key={i} className={cn("flex items-start gap-2 rounded px-1.5 py-0.5", isNew && "bg-emerald-500/5")}>
                            <div className={cn("w-1 h-1 rounded-full mt-1.5 flex-shrink-0", isNew ? "bg-emerald-400" : "bg-zinc-600")} />
                            <p className={cn("text-[11px]", isNew ? "text-emerald-300" : "text-zinc-500")}>{point}</p>
                            {isNew && <span className="text-[9px] text-emerald-500 font-semibold ml-auto flex-shrink-0">NEW</span>}
                          </div>
                        );
                      })}
                    </div>
                  </div>
                </div>
              </div>

              {/* Change breakdown */}
              <div>
                <p className="text-xs font-semibold text-zinc-500 uppercase tracking-wider mb-3">Change Breakdown</p>
                <div className="space-y-2">
                  {comparison.changes.map((change, i) => (
                    <motion.div
                      key={i}
                      initial={{ opacity: 0, x: -8 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: i * 0.06 }}
                      className="flex items-start gap-3 rounded-lg bg-zinc-800/30 border border-zinc-700/30 px-4 py-3"
                    >
                      <span className={cn("text-[10px] font-semibold px-2 py-0.5 rounded border capitalize flex-shrink-0 mt-0.5", changeTypeColors[change.type] ?? changeTypeColors.general)}>
                        {change.type.replace("_", " ")}
                      </span>
                      <p className="text-xs text-zinc-300 leading-relaxed">{change.summary}</p>
                    </motion.div>
                  ))}
                </div>
              </div>

              {/* Delta summary */}
              <div className="rounded-lg bg-brand-500/5 border border-brand-500/15 px-4 py-3">
                <div className="flex items-center gap-2 mb-1.5">
                  <TrendingUp className="w-3.5 h-3.5 text-brand-400" />
                  <p className="text-[10px] font-semibold text-brand-400 uppercase tracking-wider">Delta Summary</p>
                </div>
                <p className="text-xs text-zinc-300 leading-relaxed font-mono">{comparison.deltaSummary}</p>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}
