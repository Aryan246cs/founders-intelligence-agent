"use client";

import { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  X,
  Play,
  CheckCircle2,
  XCircle,
  Loader2,
  Globe,
  Crosshair,
  Brain,
  FileText,
  Send,
  Zap,
  MinusCircle,
  ClipboardList,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { executionsService } from "@/services/executions";
import { useJobProgress } from "@/hooks/useJobProgress";
import type { JobStep, WorkflowExecution } from "@/lib/types";

interface Props {
  open: boolean;
  onClose: () => void;
  onComplete?: (execution: WorkflowExecution) => void;
}

/**
 * Icons are matched on the agent named in the step label, because the plan —
 * and therefore the step list — is generated at runtime by the PlannerAgent.
 */
function iconForStep(step: JobStep): React.ElementType {
  const label = step.label.toLowerCase();
  if (step.key === "plan") return ClipboardList;
  if (label.includes("competitor")) return Crosshair;
  if (label.includes("search") || label.includes("web")) return Globe;
  if (label.includes("memory")) return Brain;
  if (label.includes("briefing")) return FileText;
  if (label.includes("slack") || label.includes("deliver")) return Send;
  return Zap;
}

export function GenerateBriefingModal({ open, onClose, onComplete }: Props) {
  const [phase, setPhase] = useState<"idle" | "running" | "done" | "failed">("idle");
  const [elapsedMs, setElapsedMs] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [sendToSlack, setSendToSlack] = useState(false);
  const [request, setRequest] = useState("");
  const [pollPath, setPollPath] = useState<string | null>(null);

  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const startTimeRef = useRef<number>(0);
  const completedRef = useRef(false);

  const { progress, error: pollError, reset } = useJobProgress(pollPath);

  // Reset when modal opens
  useEffect(() => {
    if (open) {
      setPhase("idle");
      setElapsedMs(0);
      setError(null);
      setRequest("");
      setPollPath(null);
      completedRef.current = false;
      reset();
    }
  }, [open, reset]);

  // Elapsed timer
  useEffect(() => {
    if (phase === "running") {
      startTimeRef.current = Date.now();
      timerRef.current = setInterval(
        () => setElapsedMs(Date.now() - startTimeRef.current),
        100
      );
    } else if (timerRef.current) {
      clearInterval(timerRef.current);
    }
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [phase]);

  // React to terminal job states
  useEffect(() => {
    if (!progress) return;

    if (progress.status === "failed") {
      setError(progress.error ?? "Workflow failed");
      setPhase("failed");
      setPollPath(null);
      return;
    }

    if (progress.status === "completed" && !completedRef.current) {
      completedRef.current = true;
      setPhase("done");
      setPollPath(null);
      const raw = (progress.result ?? {}) as Record<string, unknown>;
      onComplete?.({
        id: (raw.id as string) ?? "",
        executionId: (raw.execution_id as string) ?? "",
        status: "completed",
        triggerSource: (raw.trigger_source as string) ?? "manual",
        requestSummary: (raw.request_summary as string) ?? "",
        planSummary: (raw.plan_summary as string) ?? "",
        stepsTotal: (raw.steps_total as number) ?? 0,
        stepsCompleted: (raw.steps_completed as number) ?? 0,
        briefingAvailable: (raw.briefing_available as boolean) ?? false,
        slackDelivered: (raw.slack_delivered as boolean) ?? false,
        comparisonRan: (raw.comparison_ran as boolean) ?? false,
        hasCompetitorChanges: (raw.has_competitor_changes as boolean) ?? false,
        startedAt: (raw.started_at as string) ?? "",
        completedAt: (raw.completed_at as string) ?? "",
        durationMs: (raw.duration_ms as number) ?? 0,
      });
    }
  }, [progress, onComplete]);

  useEffect(() => {
    if (pollError) {
      setError(pollError);
      setPhase("failed");
      setPollPath(null);
    }
  }, [pollError]);

  const handleGenerate = async () => {
    setPhase("running");
    setError(null);
    setElapsedMs(0);
    completedRef.current = false;
    reset();

    try {
      const { poll_url } = await executionsService.run({
        request:
          request.trim() ||
          "Monitor OpenAI, Anthropic, Google DeepMind and generate founder intelligence briefing",
        send_to_slack: sendToSlack,
        trigger_source: "manual",
      });
      setPollPath(poll_url);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not start the workflow");
      setPhase("failed");
    }
  };

  const steps = progress?.steps ?? [];
  const briefingDelivered = Boolean(
    (progress?.result as Record<string, unknown> | null)?.slack_delivered
  );

  const dismissable = phase === "idle" || phase === "done" || phase === "failed";

  return (
    <AnimatePresence>
      {open && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4"
          onClick={dismissable ? onClose : undefined}
        >
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 16 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 16 }}
            transition={{ duration: 0.2 }}
            onClick={(e) => e.stopPropagation()}
            className="w-full max-w-lg flex flex-col glass rounded-2xl border border-zinc-800/60 shadow-glass"
            style={{ maxHeight: "min(640px, calc(100vh - 32px))" }}
          >
            {/* Header */}
            <div className="px-6 py-4 border-b border-zinc-800/60 flex items-center justify-between flex-shrink-0">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-lg bg-brand-500/10 border border-brand-500/20 flex items-center justify-center">
                  <Zap className="w-4 h-4 text-brand-400" />
                </div>
                <div>
                  <h2 className="text-sm font-semibold text-zinc-100">
                    Generate Intelligence Briefing
                  </h2>
                  <p className="text-xs text-zinc-500">Autonomous AI workflow</p>
                </div>
              </div>
              {dismissable && (
                <button
                  onClick={onClose}
                  className="w-7 h-7 rounded-lg bg-zinc-800/60 flex items-center justify-center hover:bg-zinc-700/60 transition-colors"
                >
                  <X className="w-3.5 h-3.5 text-zinc-400" />
                </button>
              )}
            </div>

            {/* Body */}
            <div className="px-6 py-5 space-y-4 overflow-y-auto flex-1 min-h-0">
              {phase === "running" && (
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <motion.div
                      animate={{ opacity: [0.4, 1, 0.4] }}
                      transition={{ duration: 1, repeat: Infinity }}
                      className="w-1.5 h-1.5 rounded-full bg-brand-400"
                      style={{ boxShadow: "0 0 6px rgba(99,102,241,0.8)" }}
                    />
                    <span className="text-xs font-medium text-brand-400">
                      {progress?.current_step_label ?? "Planning workflow"}
                    </span>
                  </div>
                  <span className="text-xs font-mono text-zinc-500 tabular-nums">
                    {formatElapsed(elapsedMs)}
                  </span>
                </div>
              )}

              {/* Live step timeline — the plan is built at runtime, so the list
                  grows once the planner decides what to run */}
              {phase !== "idle" && (
                <div className="space-y-2">
                  {steps.length === 0 && (
                    <div className="flex items-center gap-2 text-xs text-zinc-500 px-4 py-2.5">
                      <Loader2 className="w-3.5 h-3.5 animate-spin text-brand-400" />
                      Starting workflow…
                    </div>
                  )}
                  {steps.map((step) => (
                    <StepRow key={step.key} step={step} />
                  ))}
                </div>
              )}

              {/* Result */}
              {phase === "done" && (
                <motion.div
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="rounded-lg bg-emerald-500/5 border border-emerald-500/20 px-4 py-3 space-y-1.5"
                >
                  <div className="flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                    <p className="text-sm font-semibold text-emerald-400">
                      Briefing Generated
                    </p>
                  </div>
                  <p className="text-xs text-zinc-400">
                    Completed in {formatElapsed(progress?.duration_ms ?? elapsedMs)} ·
                    Intelligence briefing is now available.
                  </p>
                  {briefingDelivered && (
                    <p className="text-xs text-zinc-400">✓ Delivered to Slack</p>
                  )}
                </motion.div>
              )}

              {/* Error */}
              {phase === "failed" && error && (
                <motion.div
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="rounded-lg bg-rose-500/5 border border-rose-500/20 px-4 py-3"
                >
                  <p className="text-xs font-semibold text-rose-400 mb-1">
                    Workflow Failed
                  </p>
                  <p className="text-xs text-zinc-500 font-mono break-words">{error}</p>
                </motion.div>
              )}

              {/* Request input + Slack toggle (idle only) */}
              {phase === "idle" && (
                <div className="space-y-3">
                  <div>
                    <label className="text-xs font-medium text-zinc-400 mb-1.5 block">
                      What should the AI research?
                    </label>
                    <textarea
                      value={request}
                      onChange={(e) => setRequest(e.target.value)}
                      placeholder="e.g. Monitor OpenAI, Anthropic and generate a founder briefing on enterprise AI trends…"
                      rows={3}
                      className="w-full bg-zinc-900/60 border border-zinc-800 rounded-lg px-3 py-2.5 text-sm text-zinc-300 placeholder:text-zinc-600 focus:outline-none focus:border-brand-500/50 transition-all resize-none"
                    />
                    <p className="text-[10px] text-zinc-600 mt-1">
                      Leave blank to run the default intelligence sweep.
                    </p>
                  </div>
                  <button
                    onClick={() => setSendToSlack(!sendToSlack)}
                    className={cn(
                      "flex items-center gap-2 px-3 py-2 rounded-lg text-xs font-medium transition-all border w-full",
                      sendToSlack
                        ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                        : "bg-zinc-800/30 text-zinc-500 border-zinc-700/30 hover:text-zinc-300"
                    )}
                  >
                    <Send className="w-3.5 h-3.5" />
                    {sendToSlack ? "Will deliver to Slack" : "Also deliver to Slack"}
                  </button>
                </div>
              )}
            </div>

            {/* Footer */}
            <div className="px-6 py-4 border-t border-zinc-800/60 flex items-center justify-end gap-3 flex-shrink-0">
              {phase === "idle" && (
                <>
                  <button
                    onClick={onClose}
                    className="px-4 py-2 rounded-lg text-sm text-zinc-400 hover:text-zinc-200 transition-colors"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleGenerate}
                    className="flex items-center gap-2 px-5 py-2 rounded-lg bg-brand-500 text-sm font-semibold text-white hover:bg-brand-400 transition-all shadow-glow-sm"
                  >
                    <Play className="w-3.5 h-3.5" />
                    Launch Operation
                  </button>
                </>
              )}
              {phase === "running" && (
                <div className="flex items-center gap-2 text-xs text-zinc-500">
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  {progress
                    ? `Step ${progress.steps_completed + 1} of ${progress.steps_total}`
                    : "Running autonomous workflow…"}
                </div>
              )}
              {(phase === "done" || phase === "failed") && (
                <button
                  onClick={onClose}
                  className="px-5 py-2 rounded-lg bg-zinc-800 text-sm font-medium text-zinc-200 hover:bg-zinc-700 transition-colors"
                >
                  Close
                </button>
              )}
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

function StepRow({ step }: { step: JobStep }) {
  const Icon = iconForStep(step);
  const { status } = step;
  const isRunning = status === "running";
  const isDone = status === "done";
  const isFailed = status === "failed";
  const isSkipped = status === "skipped";
  const isPending = status === "pending";

  return (
    <motion.div
      initial={{ opacity: 0, y: 4 }}
      animate={{ opacity: isPending ? 0.35 : isSkipped ? 0.55 : 1, y: 0 }}
      className={cn(
        "flex items-center gap-3 rounded-lg px-4 py-2.5 border transition-all",
        isRunning && "bg-brand-500/5 border-brand-500/20",
        isDone && "bg-emerald-500/5 border-emerald-500/15",
        isFailed && "bg-rose-500/5 border-rose-500/20",
        (isSkipped || isPending) && "bg-zinc-800/20 border-zinc-800/40"
      )}
    >
      <div className="flex-shrink-0">
        {isRunning && <Loader2 className="w-4 h-4 text-brand-400 animate-spin" />}
        {isDone && <CheckCircle2 className="w-4 h-4 text-emerald-400" />}
        {isFailed && <XCircle className="w-4 h-4 text-rose-400" />}
        {isSkipped && <MinusCircle className="w-4 h-4 text-zinc-600" />}
        {isPending && (
          <div className="w-4 h-4 rounded-full border border-zinc-700 flex items-center justify-center">
            <div className="w-1.5 h-1.5 rounded-full bg-zinc-700" />
          </div>
        )}
      </div>
      <Icon
        className={cn(
          "w-3.5 h-3.5 flex-shrink-0",
          isRunning ? "text-brand-400" : isDone ? "text-emerald-400" : "text-zinc-600"
        )}
      />
      <div className="flex-1 min-w-0">
        <span
          className={cn(
            "text-xs font-medium block truncate",
            isRunning ? "text-zinc-200" : isDone ? "text-zinc-300" : "text-zinc-600"
          )}
        >
          {step.label}
        </span>
        {step.detail && !isPending && (
          <span className="text-[10px] text-zinc-600 block truncate">{step.detail}</span>
        )}
      </div>
      {(isDone || isFailed) && step.duration_ms !== null && (
        <span className="text-[10px] text-zinc-600 font-mono tabular-nums flex-shrink-0">
          {formatElapsed(step.duration_ms)}
        </span>
      )}
    </motion.div>
  );
}

function formatElapsed(ms: number): string {
  if (ms < 1000) return `${(ms / 1000).toFixed(1)}s`;
  const s = Math.floor(ms / 1000);
  if (s < 60) return `${s}s`;
  return `${Math.floor(s / 60)}m ${s % 60}s`;
}
