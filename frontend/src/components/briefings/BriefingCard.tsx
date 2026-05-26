"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  ChevronDown,
  Slack,
  Share2,
  Download,
  Clock,
  TrendingUp,
  AlertTriangle,
  Lightbulb,
  Building2,
  BarChart3,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { cn, formatDate, priorityColor } from "@/lib/utils";
import type { Briefing } from "@/lib/types";

interface BriefingCardProps {
  briefing: Briefing;
}

const riskColors = {
  critical: "text-rose-400",
  high: "text-amber-400",
  medium: "text-brand-400",
  low: "text-emerald-400",
};

export function BriefingCard({ briefing }: BriefingCardProps) {
  const [expanded, setExpanded] = useState(false);

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      className="glass glass-hover rounded-xl border border-zinc-800/60 overflow-hidden"
    >
      {/* Header */}
      <div
        className="px-6 py-5 cursor-pointer"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1 min-w-0">
            <div className="flex flex-wrap items-center gap-2 mb-2.5">
              <Badge variant={priorityColor(briefing.priority) as any}>
                {briefing.priority.toUpperCase()}
              </Badge>
              {briefing.sentToSlack && (
                <Badge variant="success">
                  <Slack className="w-2.5 h-2.5" /> Delivered to Slack
                </Badge>
              )}
              <Badge variant="outline">
                <BarChart3 className="w-2.5 h-2.5" /> {briefing.aiConfidence}% confidence
              </Badge>
            </div>

            <h3 className="text-base font-semibold text-zinc-100 leading-snug">
              {briefing.title}
            </h3>

            <div className="flex flex-wrap items-center gap-3 mt-2.5">
              <div className="flex items-center gap-1.5 text-zinc-500">
                <Clock className="w-3 h-3" />
                <span className="text-xs">{formatDate(briefing.generatedAt)}</span>
              </div>
              <span className="text-zinc-700">·</span>
              <span className="text-xs text-zinc-500">{briefing.sourceCount} sources analyzed</span>
              <span className="text-zinc-700">·</span>
              <div className="flex items-center gap-1">
                {briefing.companiesMentioned.slice(0, 3).map((c) => (
                  <span key={c} className="text-xs bg-zinc-800/60 text-zinc-400 px-1.5 py-0.5 rounded border border-zinc-700/40">{c}</span>
                ))}
                {briefing.companiesMentioned.length > 3 && (
                  <span className="text-xs text-zinc-600">+{briefing.companiesMentioned.length - 3}</span>
                )}
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2 flex-shrink-0">
            <button
              onClick={(e) => e.stopPropagation()}
              className="w-8 h-8 rounded-lg bg-zinc-800/60 border border-zinc-700/40 flex items-center justify-center hover:bg-zinc-700/60 transition-colors"
            >
              <Share2 className="w-3.5 h-3.5 text-zinc-400" />
            </button>
            <button
              onClick={(e) => e.stopPropagation()}
              className="w-8 h-8 rounded-lg bg-zinc-800/60 border border-zinc-700/40 flex items-center justify-center hover:bg-zinc-700/60 transition-colors"
            >
              <Download className="w-3.5 h-3.5 text-zinc-400" />
            </button>
            <motion.div animate={{ rotate: expanded ? 180 : 0 }} transition={{ duration: 0.2 }}>
              <ChevronDown className="w-4 h-4 text-zinc-500" />
            </motion.div>
          </div>
        </div>

        {/* Key changes preview */}
        <div className="mt-4 space-y-1.5">
          {briefing.keyChanges.slice(0, expanded ? undefined : 2).map((change, i) => (
            <div key={i} className="flex items-start gap-2">
              <div className="w-1 h-1 rounded-full bg-brand-400/60 mt-1.5 flex-shrink-0" />
              <p className="text-xs text-zinc-400 leading-relaxed">{change}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Expanded content */}
      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.25 }}
            className="overflow-hidden"
          >
            <div className="px-6 pb-6 border-t border-zinc-800/40 pt-5 space-y-5">
              {/* Strategic Insight */}
              <div className="rounded-lg bg-brand-500/5 border border-brand-500/15 p-4">
                <div className="flex items-center gap-2 mb-2">
                  <Lightbulb className="w-4 h-4 text-brand-400" />
                  <p className="text-xs font-semibold text-brand-400 uppercase tracking-wider">Strategic Insight</p>
                </div>
                <p className="text-sm text-zinc-300 leading-relaxed">{briefing.strategicInsight}</p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Risk Level */}
                <div className="rounded-lg bg-zinc-800/30 border border-zinc-700/30 p-4">
                  <div className="flex items-center gap-2 mb-3">
                    <AlertTriangle className="w-4 h-4 text-amber-400" />
                    <p className="text-xs font-semibold text-zinc-400 uppercase tracking-wider">Risk Level</p>
                  </div>
                  <p className={cn("text-lg font-bold capitalize", riskColors[briefing.riskLevel])}>
                    {briefing.riskLevel}
                  </p>
                </div>

                {/* Companies */}
                <div className="rounded-lg bg-zinc-800/30 border border-zinc-700/30 p-4">
                  <div className="flex items-center gap-2 mb-3">
                    <Building2 className="w-4 h-4 text-zinc-400" />
                    <p className="text-xs font-semibold text-zinc-400 uppercase tracking-wider">Companies</p>
                  </div>
                  <div className="flex flex-wrap gap-1.5">
                    {briefing.companiesMentioned.map((c) => (
                      <span key={c} className="text-xs bg-zinc-700/50 text-zinc-300 px-2 py-0.5 rounded border border-zinc-600/30">{c}</span>
                    ))}
                  </div>
                </div>
              </div>

              {/* Opportunity Signals */}
              <div className="rounded-lg bg-emerald-500/5 border border-emerald-500/15 p-4">
                <div className="flex items-center gap-2 mb-3">
                  <TrendingUp className="w-4 h-4 text-emerald-400" />
                  <p className="text-xs font-semibold text-emerald-400 uppercase tracking-wider">Opportunity Signals</p>
                </div>
                <div className="space-y-2">
                  {briefing.opportunitySignals.map((signal, i) => (
                    <div key={i} className="flex items-start gap-2">
                      <div className="w-1 h-1 rounded-full bg-emerald-400/60 mt-1.5 flex-shrink-0" />
                      <p className="text-xs text-zinc-300 leading-relaxed">{signal}</p>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}
