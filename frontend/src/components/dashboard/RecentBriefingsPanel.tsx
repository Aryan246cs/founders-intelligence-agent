"use client";

import { motion } from "framer-motion";
import { Slack, ExternalLink, Clock } from "lucide-react";
import Link from "next/link";
import { Badge } from "@/components/ui/badge";
import { formatDate, priorityColor } from "@/lib/utils";
import type { Briefing } from "@/lib/types";

interface RecentBriefingsPanelProps {
  briefings: Briefing[];
}

export function RecentBriefingsPanel({ briefings }: RecentBriefingsPanelProps) {
  return (
    <div className="glass rounded-xl border border-zinc-800/60 overflow-hidden">
      <div className="px-6 py-4 border-b border-zinc-800/60 flex items-center justify-between">
        <div>
          <h3 className="text-sm font-semibold text-zinc-200">Recent Briefings</h3>
          <p className="text-xs text-zinc-500 mt-0.5">Latest executive intelligence reports</p>
        </div>
        <Link href="/briefings" className="text-xs text-brand-400 hover:text-brand-300 transition-colors flex items-center gap-1">
          View all <ExternalLink className="w-3 h-3" />
        </Link>
      </div>

      <div className="divide-y divide-zinc-800/40">
        {briefings.slice(0, 3).map((briefing, i) => (
          <motion.div
            key={briefing.id}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.08 }}
            className="px-6 py-4 hover:bg-zinc-800/20 transition-colors group cursor-pointer"
          >
            <div className="flex items-start justify-between gap-3">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1.5">
                  <Badge variant={priorityColor(briefing.priority) as any}>
                    {briefing.priority}
                  </Badge>
                  {briefing.sentToSlack && (
                    <Badge variant="success">
                      <Slack className="w-2.5 h-2.5" /> Slack
                    </Badge>
                  )}
                </div>
                <p className="text-sm font-medium text-zinc-200 leading-snug group-hover:text-white transition-colors line-clamp-2">
                  {briefing.title}
                </p>
                <p className="text-xs text-zinc-500 mt-1.5 line-clamp-1">
                  {briefing.keyChanges[0]}
                </p>
              </div>
            </div>

            <div className="flex items-center gap-3 mt-3">
              <div className="flex items-center gap-1 text-zinc-600">
                <Clock className="w-3 h-3" />
                <span className="text-[10px]">{formatDate(briefing.generatedAt)}</span>
              </div>
              <span className="text-zinc-700">·</span>
              <span className="text-[10px] text-zinc-600">{briefing.sourceCount} sources</span>
              <span className="text-zinc-700">·</span>
              <span className="text-[10px] text-zinc-600">{briefing.aiConfidence}% confidence</span>
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  );
}
