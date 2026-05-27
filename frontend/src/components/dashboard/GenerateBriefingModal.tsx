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
  Slack,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { executionsService } from "@/services/executions";
import type { WorkflowExecution } from "@/lib/types";

interface Props {
  open: boolean;
  onClose: () => void;
  onComplete?: (execution: WorkflowExecution) => void;
}

const WORKFLOW_STEPS = [
  { id: "research", label: "Collecting competitor signals", icon: Globe, color: "text-brand-400" },
  { id: "competitor_monitor", label: "Running competitor analysis", icon: Crosshair, color: "text-amber-400" },
  { id: "memory", label: "Running memory comparison", icon: Brain, color: "text-purple-400" },
  { id: "briefing", label: "Generating strategic insights", icon: FileText, color: "text-emerald-400" },
  { id: "slack", label: "Delivering executive briefing to Slack", icon: Send, color: "text-rose-400" },
];

type StepStatus = "pending" | "running" | "done" | "failed";

interface StepState {
  id: string;
  status: StepStatus;
  output?: string;
  durationMs?: number;
}

export function GenerateBriefingModal({ open, onClose, onComplete }: Props) {
  const [phase, setPhase] = useState<"idle" | "running" | "done" | "failed">("idle");
  const [steps, setSteps] = useState<StepState[]>(
    WORKFLOW_STEPS.map((s) => ({ id: s.id, status: "pending" }))
  );
  const [currentStepIdx, setCurrentStepIdx] = useState(-1);
  const [elapsedMs, setElapsedMs] = useState(0);
  const [result, setResult] = useState<WorkflowExecution | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [sendToSlack, setSendToSlack] = useState(false);
  const [request, setRequest] = useState("");

  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const startTimeRef = useRef<number>(0);

  // Reset when modal opens
  useEffect(() => {
    if (open) {
      setPhase("idle");
      setSteps(WORKFLOW_STEPS.map((s) => ({ id: s.id, status: "pending" })));
      setCurrentStepIdx(-1);
      setElapsedMs(0);
      setResult(null);
      setError(null);
      setRequest("");
    }
  }, [open]);

  // Elapsed timer
  useEffect(() => {
    if (phase === "running") {
      startTimeRef.current = Date.now();
      timerRef.current = setInterval(() => {
        setElapsedMs(Date.now() - startTimeRef.current);
      }, 100);
    } else {
      if (timerRef.current) clearInterval(timerRef.current);
    }
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [phase]);

  // Simulate step progression while polling
  const simulateStepProgress = (totalSteps: number, completedSteps: number) => {
    setSteps((prev) =>
      prev.map((s, i) => {
        if (i < completedSteps) return { ...s, status: "done" };
        if (i === completedSteps) return { ...s, status: "running" };
        return { ...s, status: "pending" };
      })
    );
    setCurrentStepIdx(Math.min(completedSteps, totalSteps - 1));
  };

  const handleGenerate = async () => {
    setPhase("running");
    setCurrentStepIdx(0);
    setSteps((prev) =>
      prev.map((s, i) => ({ ...s, status: i === 0 ? "running" : "pending" }))
    );

    try {
      // Trigger the workflow
      const execution = await executionsService.run({
        request: request.trim() || "Monitor OpenAI, Anthropic, Google DeepMind and generate founder intelligence briefing",
        send_to_slack: sendToSlack,
        trigger_source: "manual",
      });

      const execId = (execution as Record<string, unknown>).execution_id as string
        ?? (execution as Record<string, unknown>).id as string;

      if (!execId) {
        throw new Error("No execution ID returned");
      }

      // Poll for completion
      const final = await executionsService.poll(
        execId,
        (updated) => {
          const raw = updated as Record<string, unknown>;
          const total = (raw.steps_total as number) || WORKFLOW_STEPS.length;
          const completed = (raw.steps_completed as number) || 0;
          simulateStepProgress(total, completed);
        },
        2000,
        300_000
      );

      // Mark all steps done
      setSteps((prev) => prev.map((s) => ({ ...s, status: "done" })));
      setCurrentStepIdx(WORKFLOW_STEPS.length - 1);
      setResult(final);
      setPhase("done");
      onComplete?.(final);
    } catch (e) {
      const msg = e instanceof Error ? e.message : "Workflow failed";
      setError(msg);
      setPhase("failed");
      setSteps((prev) =>
        prev.map((s) => (s.status === "running" ? { ...s, status: "failed" } : s))
      );
    }
  };

  const formatElapsed = (ms: number) => {
    if (ms < 1000) return `${(ms / 1000).toFixed(1)}s`;
    const s = Math.floor(ms / 1000);
    if (s < 60) return `${s}s`;
    return `${Math.floor(s / 60)}m ${s % 60}s`;
  };

  return (
    <AnimatePresence>
      {open && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50"
            onClick={phase === "idle" || phase === "done" || phase === "failed" ? onClose : undefined}
          />

          {/* Modal */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            transition={{ duration: 0.2 }}
            className="fixed left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 z-50 w-full max-w-lg"
          >
            <div className="glass rounded-2xl border border-zinc-800/60 shadow-glass overflow-hidden">
              {/* Header */}
              <div className="px-6 py-5 border-b border-zinc-800/60 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-lg bg-brand-500/10 border border-brand-500/20 flex items-center justify-center">
                    <Zap className="w-4 h-4 text-brand-400" />
                  </div>
                  <div>
                    <h2 className="text-sm font-semibold text-zinc-100">Generate Intelligence Briefing</h2>
                    <p className="text-xs text-zinc-500">Autonomous AI workflow</p>
                  </div>
                </div>
                {(phase === "idle" || phase === "done" || phase === "failed") && (
                  <button
                    onClick={onClose}
                    className="w-7 h-7 rounded-lg bg-zinc-800/60 flex items-center justify-center hover:bg-zinc-700/60 transition-colors"
                  >
                    <X className="w-3.5 h-3.5 text-zinc-400" />
                  </button>
                )}
              </div>

              {/* Body */}
              <div className="px-6 py-5 space-y-5">
                {/* Elapsed timer */}
                {phase === "running" && (
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <motion.div
                        animate={{ opacity: [0.4, 1, 0.4] }}
                        transition={{ duration: 1, repeat: Infinity }}
                        className="w-1.5 h-1.5 rounded-full bg-brand-400"
                        style={{ boxShadow: "0 0 6px rgba(99,102,241,0.8)" }}
                      />
                      <span className="text-xs font-medium text-brand-400">Operation in progress</span>
                    </div>
                    <span className="text-xs font-mono text-zinc-500 tabular-nums">
                      {formatElapsed(elapsedMs)}
                    </span>
                  </div>
                )}

                {/* Step timeline */}
                <div className="space-y-2">
                  {WORKFLOW_STEPS.map((step, i) => {
                    const stepState = steps[i];
                    const Icon = step.icon;
                    const isRunning = stepState.status === "running";
                    const isDone = stepState.status === "done";
                    const isFailed = stepState.status === "failed";
                    const isPending = stepState.status === "pending";

                    return (
                      <motion.div
                        key={step.id}
                        initial={{ opacity: 0.4 }}
                        animate={{
                          opacity: isPending ? 0.35 : 1,
                        }}
                        className={cn(
                          "flex items-center gap-3 rounded-lg px-4 py-3 border transition-all",
                          isRunning && "bg-brand-500/5 border-brand-500/20",
                          isDone && "bg-emerald-500/5 border-emerald-500/15",
                          isFailed && "bg-rose-500/5 border-rose-500/20",
                          isPending && "bg-zinc-800/20 border-zinc-800/40"
                        )}
                      >
                        {/* Status indicator */}
                        <div className="flex-shrink-0">
                          {isRunning && (
                            <Loader2 className="w-4 h-4 text-brand-400 animate-spin" />
                          )}
                          {isDone && (
                            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                          )}
                          {isFailed && (
                            <XCircle className="w-4 h-4 text-rose-400" />
                          )}
                          {isPending && (
                            <div className="w-4 h-4 rounded-full border border-zinc-700 flex items-center justify-center">
                              <div className="w-1.5 h-1.5 rounded-full bg-zinc-700" />
                            </div>
                          )}
                        </div>

                        <Icon
                          className={cn(
                            "w-3.5 h-3.5 flex-shrink-0",
                            isRunning ? step.color : isDone ? "text-emerald-400" : "text-zinc-600"
                          )}
                        />

                        <span
                          className={cn(
                            "text-xs font-medium flex-1",
                            isRunning ? "text-zinc-200" : isDone ? "text-zinc-300" : "text-zinc-600"
                          )}
                        >
                          {step.label}
                          {isRunning && (
                            <motion.span
                              animate={{ opacity: [0, 1, 0] }}
                              transition={{ duration: 1.2, repeat: Infinity }}
                            >
                              …
                            </motion.span>
                          )}
                        </span>

                        {isDone && (
                          <span className="text-[10px] text-emerald-500 font-medium">Done</span>
                        )}
                      </motion.div>
                    );
                  })}
                </div>

                {/* Result */}
                {phase === "done" && result && (
                  <motion.div
                    initial={{ opacity: 0, y: 8 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="rounded-lg bg-emerald-500/5 border border-emerald-500/20 px-4 py-4 space-y-2"
                  >
                    <div className="flex items-center gap-2">
                      <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                      <p className="text-sm font-semibold text-emerald-400">Briefing Generated</p>
                    </div>
                    <p className="text-xs text-zinc-400">
                      Completed in {formatElapsed(elapsedMs)} · Intelligence briefing is now available.
                    </p>
                    {(result as Record<string, unknown>).slack_delivered && (
                      <div className="flex items-center gap-1.5 text-xs text-zinc-400">
                        <Slack className="w-3.5 h-3.5 text-emerald-400" />
                        Delivered to Slack
                      </div>
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
                    <p className="text-xs font-semibold text-rose-400 mb-1">Workflow Failed</p>
                    <p className="text-xs text-zinc-500 font-mono">{error}</p>
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
                      <p className="text-[10px] text-zinc-600 mt-1">Leave blank to run the default intelligence sweep.</p>
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
                      <Slack className="w-3.5 h-3.5" />
                      {sendToSlack ? "Will deliver to Slack" : "Also deliver to Slack"}
                    </button>
                  </div>
                )}
              </div>

              {/* Footer */}
              <div className="px-6 py-4 border-t border-zinc-800/60 flex items-center justify-end gap-3">
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
                    Running autonomous workflow…
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
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
