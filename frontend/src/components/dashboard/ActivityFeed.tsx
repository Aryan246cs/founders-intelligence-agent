"use client";

import { motion, AnimatePresence } from "framer-motion";
import { CheckCircle2, AlertTriangle, Info, XCircle } from "lucide-react";
import { cn } from "@/lib/utils";
import type { ActivityEvent } from "@/lib/types";

const typeConfig = {
  success: { icon: CheckCircle2, color: "text-emerald-400", bg: "bg-emerald-500/10" },
  warning: { icon: AlertTriangle, color: "text-amber-400", bg: "bg-amber-500/10" },
  info: { icon: Info, color: "text-brand-400", bg: "bg-brand-500/10" },
  error: { icon: XCircle, color: "text-rose-400", bg: "bg-rose-500/10" },
};

interface ActivityFeedProps {
  events: ActivityEvent[];
}

export function ActivityFeed({ events }: ActivityFeedProps) {
  return (
    <div className="glass rounded-xl border border-zinc-800/60 overflow-hidden">
      <div className="px-5 py-4 border-b border-zinc-800/60 flex items-center justify-between">
        <div>
          <h3 className="text-sm font-semibold text-zinc-200">Live Activity</h3>
          <p className="text-xs text-zinc-500 mt-0.5">Real-time agent execution log</p>
        </div>
        <motion.div
          animate={{ opacity: [0.4, 1, 0.4] }}
          transition={{ duration: 1.5, repeat: Infinity }}
          className="flex items-center gap-1.5"
        >
          <div className="w-1.5 h-1.5 rounded-full bg-emerald-400" style={{ boxShadow: "0 0 6px rgba(52,211,153,0.8)" }} />
          <span className="text-[10px] text-emerald-400 font-medium">LIVE</span>
        </motion.div>
      </div>

      <div className="divide-y divide-zinc-800/30 max-h-80 overflow-y-auto">
        <AnimatePresence>
          {events.map((event, i) => {
            const config = typeConfig[event.type];
            const Icon = config.icon;
            return (
              <motion.div
                key={event.id}
                initial={{ opacity: 0, x: -8 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.04 }}
                className="flex items-start gap-3 px-5 py-3 hover:bg-zinc-800/20 transition-colors"
              >
                <div className={cn("w-6 h-6 rounded-md flex items-center justify-center flex-shrink-0 mt-0.5", config.bg)}>
                  <Icon className={cn("w-3.5 h-3.5", config.color)} />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-xs text-zinc-300 leading-relaxed">{event.message}</p>
                  <div className="flex items-center gap-2 mt-1">
                    <span className="text-[10px] text-zinc-600">{event.timestamp}</span>
                    {event.agent && (
                      <>
                        <span className="text-zinc-700">·</span>
                        <span className="text-[10px] text-zinc-600">{event.agent}</span>
                      </>
                    )}
                  </div>
                </div>
              </motion.div>
            );
          })}
        </AnimatePresence>
      </div>
    </div>
  );
}
