"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  ChevronDown,
  CheckCircle2,
  XCircle,
  Loader2,
  Clock,
  Zap,
  Slack,
  Brain,
  Globe,
  Crosshair,
  FileText,
  Send,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { cn, formatDate, formatDuration } from "@/lib/utils";
import type { WorkflowExecution } from "@/lib/types";

const agentIcons: Record<string, React.ElementType> = {
  research: Globe,
  competitor_monitor: Crosshair,
  memory: Brain,
  briefing: FileText,
  slack: Send,
};

const statusConfig = {
  completed: { icon: CheckCircle2, color: "text-emerald-400", badge: "success" as const, label: "Completed" },
  running: { icon: Loader2, color: "text-brand-400", badge: "info" as const, label: "Running" },
  failed: { icon: XCircle, color: "text-rose-400", badge: "error" as const, label: "Failed" },
};

interface ExecutionCardProps {
  execution: WorkflowExecution;
}

export function ExecutionCard({ execution }: ExecutionCardProps) {
  const [expanded, setExpanded] = useState(false);
  const status = statusConfig[execution.status];
  const StatusIcon = status.icon;
  const progress = execution.stepsTotal > 0
    ? (execution.stepsCompleted / execution.stepsTotal) * 100
    : 0;

  return (
    <motion.div
      layout
      className="glass glass-hover rounded-xl border border-zinc-800/60 overflow-hidden"
    >
      <div
        className="px-6 py-5 cursor-pointer"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex items-start gap-4">
          {/* Status icon */}
          <div className={cn(
            "w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0 mt-0.5",
            execution.status === "completed" ? "bg-emerald-500/10 border border-emerald-500/20" :
            execution.status === "failed" ? "bg-rose-500/10 border border-rose-500/20" :
            "bg-brand-500/10 border border-brand-500/20"
          )}>
            <StatusIcon className={cn("w-4 h-4", status.color, execution.status === "running" && "animate-spin")} />
          </div>

          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1.5">
              <Badge variant={status.badge}>{status.label}</Badge>
              <Badge variant="outline">{execution.triggerSource}</Badge>
              {execution.slackDelivered && <Badge variant="success"><Slack className="w-2.5 h-2.5" /> Slack</Badge>}
              {execution.hasCompetitorChanges && <Badge variant="warning">Changes detected</Badge>}
            </div>

            <p className="text-sm font-medium text-zinc-200 leading-snug">{execution.requestSummary}</p>
            <p className="text-xs text-zinc-500 mt-1">{execution.planSummary}</p>

            <div className="flex flex-wrap items-center gap-3 mt-3">
              <div className="flex items-center gap-1.5 text-zinc-500">
                <Clock className="w-3 h-3" />
                <span className="text-xs">{formatDate(execution.startedAt)}</span>
              </div>
              <span className="text-zinc-700">·</span>
              <div className="flex items-center gap-1.5 text-zinc-500">
                <Zap className="w-3 h-3" />
                <span className="text-xs">{formatDuration(execution.durationMs)}</span>
              </div>
              <span className="text-zinc-700">·</span>
              <span className="text-xs text-zinc-500">{execution.stepsCompleted}/{execution.stepsTotal} steps</span>
              <span className="text-xs font-mono text-zinc-600">{execution.executionId}</span>
            </div>

            {/* Progress bar */}
            <div className="mt-3 h-1 bg-zinc-800 rounded-full overflow-hidden">
              <motion.div
                className={cn(
                  "h-full rounded-full",
                  execution.status === "completed" ? "bg-emerald-500" :
                  execution.status === "failed" ? "bg-rose-500" : "bg-brand-500"
                )}
                initial={{ width: 0 }}
                animate={{ width: `${progress}%` }}
                transition={{ duration: 0.8, ease: "easeOut" }}
              />
            </div>
          </div>

          <motion.div animate={{ rotate: expanded ? 180 : 0 }} transition={{ duration: 0.2 }} className="flex-shrink-0 mt-1">
            <ChevronDown className="w-4 h-4 text-zinc-500" />
          </motion.div>
        </div>
      </div>

      {/* Expanded: step timeline */}
      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.25 }}
            className="overflow-hidden"
          >
            <div className="px-6 pb-6 border-t border-zinc-800/40 pt-5">
              {execution.error && (
                <div className="mb-4 rounded-lg bg-rose-500/5 border border-rose-500/20 px-4 py-3">
                  <p className="text-xs font-semibold text-rose-400 mb-1">Error</p>
                  <p className="text-xs text-zinc-400 font-mono">{execution.error}</p>
                </div>
              )}

              {execution.steps && (
                <div>
                  <p className="text-xs font-semibold text-zinc-500 uppercase tracking-wider mb-4">Execution Timeline</p>
                  <div className="relative">
                    {/* Vertical line */}
                    <div className="absolute left-4 top-0 bottom-0 w-px bg-zinc-800" />

                    <div className="space-y-3">
                      {execution.steps.map((step, i) => {
                        const StepIcon = agentIcons[step.agentType] ?? Zap;
                        const stepStatus = statusConfig[step.status];
                        const StepStatusIcon = stepStatus.icon;
                        return (
                          <motion.div
                            key={i}
                            initial={{ opacity: 0, x: -8 }}
                            animate={{ opacity: 1, x: 0 }}
                            transition={{ delay: i * 0.06 }}
                            className="flex items-center gap-4 pl-10 relative"
                          >
                            {/* Node */}
                            <div className={cn(
                              "absolute left-2 w-5 h-5 rounded-full border-2 flex items-center justify-center",
                              step.status === "completed" ? "border-emerald-500 bg-emerald-500/10" :
                              step.status === "failed" ? "border-rose-500 bg-rose-500/10" :
                              "border-brand-500 bg-brand-500/10"
                            )}>
                              <StepStatusIcon className={cn("w-2.5 h-2.5", stepStatus.color)} />
                            </div>

                            <div className="flex-1 flex items-center justify-between glass rounded-lg px-4 py-2.5 border border-zinc-800/40">
                              <div className="flex items-center gap-2.5">
                                <StepIcon className="w-3.5 h-3.5 text-zinc-500" />
                                <span className="text-xs font-medium text-zinc-300 capitalize">
                                  {step.agentType.replace("_", " ")} Agent
                                </span>
                                {step.output && (
                                  <span className="text-xs text-zinc-600">— {step.output}</span>
                                )}
                              </div>
                              <span className="text-xs text-zinc-600 tabular-nums">{formatDuration(step.durationMs)}</span>
                            </div>
                          </motion.div>
                        );
                      })}
                    </div>
                  </div>
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}
