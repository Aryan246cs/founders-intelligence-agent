"use client";

import { useState, useEffect, useRef } from "react";
import { motion } from "framer-motion";
import {
  Telescope,
  Play,
  CheckCircle2,
  XCircle,
  Loader2,
  Lightbulb,
  Globe,
  Search,
  BarChart2,
  Tag,
  FileText,
  Brain,
  Star,
  Send,
  MinusCircle,
  Database,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { startupResearchService } from "@/services/startupResearch";
import type { StartupResearchResult } from "@/services/startupResearch";
import { useJobProgress } from "@/hooks/useJobProgress";
import type { JobStep, StartupResearchReport } from "@/lib/types";

interface Props {
  onReportReady: (report: StartupResearchReport) => void;
}

/**
 * Icons keyed by the step keys the backend emits (see RESEARCH_STEPS in
 * backend/agents/startup_research_agent.py). The labels themselves come from
 * the backend, so the two can never disagree about what is running.
 */
const STEP_ICONS: Record<string, React.ElementType> = {
  parse: Lightbulb,
  strategy: Tag,
  search: Search,
  scrape: Globe,
  pricing: BarChart2,
  recover: FileText,
  matrix: Brain,
  insights: Star,
  persist: Database,
  deliver: Send,
};

const EXAMPLE_IDEAS = [
  "AI-powered interview preparation platform",
  "Voice AI receptionist for healthcare clinics",
  "Autonomous social media content generator",
  "AI-powered legal document assistant",
  "No-code workflow automation for SMBs",
];

type Phase = "idle" | "running" | "done" | "failed";

export function ResearchLauncher({ onReportReady }: Props) {
  const [phase, setPhase] = useState<Phase>("idle");
  const [startupIdea, setStartupIdea] = useState("");
  const [startupName, setStartupName] = useState("");
  const [sendToSlack, setSendToSlack] = useState(false);
  const [pollPath, setPollPath] = useState<string | null>(null);
  const [elapsedMs, setElapsedMs] = useState(0);
  const [error, setError] = useState<string | null>(null);

  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const startTimeRef = useRef<number>(0);
  const deliveredRef = useRef<string | null>(null);

  const { progress, error: pollError, reset } = useJobProgress(pollPath);

  // Elapsed timer — cosmetic only; the authoritative duration comes from the job.
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

  // React to terminal job states.
  useEffect(() => {
    if (!progress) return;

    if (progress.status === "failed") {
      setError(progress.error ?? "Research pipeline failed");
      setPhase("failed");
      setPollPath(null);
      return;
    }

    if (progress.status === "completed") {
      const result = progress.result as unknown as StartupResearchResult | null;
      setPhase("done");
      setPollPath(null);
      // The job can report completed on more than one render; only fetch once.
      if (result?.report_id && deliveredRef.current !== result.report_id) {
        deliveredRef.current = result.report_id;
        startupResearchService
          .get(result.report_id)
          .then(onReportReady)
          .catch(() => setError("Report saved but could not be loaded — check history"));
      }
    }
  }, [progress, onReportReady]);

  useEffect(() => {
    if (pollError) {
      setError(pollError);
      setPhase("failed");
      setPollPath(null);
    }
  }, [pollError]);

  const handleGenerate = async () => {
    if (!startupIdea.trim()) return;
    setPhase("running");
    setError(null);
    setElapsedMs(0);
    deliveredRef.current = null;
    reset();

    try {
      const { poll_url } = await startupResearchService.run({
        startup_idea: startupIdea.trim(),
        startup_name: startupName.trim() || undefined,
        send_to_slack: sendToSlack,
      });
      setPollPath(poll_url);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not start the pipeline");
      setPhase("failed");
    }
  };

  const handleReset = () => {
    setPhase("idle");
    setError(null);
    setElapsedMs(0);
    setPollPath(null);
    deliveredRef.current = null;
    reset();
  };

  const result = progress?.result as unknown as StartupResearchResult | null;
  const steps = progress?.steps ?? [];

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      className="glass rounded-2xl border border-zinc-800/60 overflow-hidden"
    >
      {/* Header */}
      <div className="px-5 py-4 border-b border-zinc-800/60 flex items-center gap-3">
        <div className="w-8 h-8 rounded-lg bg-purple-500/10 border border-purple-500/20 flex items-center justify-center">
          <Telescope className="w-4 h-4 text-purple-400" />
        </div>
        <div>
          <p className="text-sm font-semibold text-zinc-100">Generate Research</p>
          <p className="text-xs text-zinc-500">Autonomous 10-step pipeline</p>
        </div>
        {phase === "running" && (
          <div className="ml-auto flex items-center gap-2">
            <motion.div
              animate={{ opacity: [0.4, 1, 0.4] }}
              transition={{ duration: 1, repeat: Infinity }}
              className="w-1.5 h-1.5 rounded-full bg-purple-400"
              style={{ boxShadow: "0 0 6px rgba(168,85,247,0.8)" }}
            />
            <span className="text-xs font-mono text-zinc-500 tabular-nums">
              {formatElapsed(elapsedMs)}
            </span>
          </div>
        )}
      </div>

      <div className="px-5 py-5 space-y-4">
        {/* Input form — only in idle */}
        {phase === "idle" && (
          <div className="space-y-3">
            <div>
              <label className="text-xs font-medium text-zinc-400 mb-1.5 block">
                Startup Idea <span className="text-rose-400">*</span>
              </label>
              <textarea
                value={startupIdea}
                onChange={(e) => setStartupIdea(e.target.value)}
                placeholder="e.g. AI-powered interview preparation platform"
                rows={3}
                className="w-full bg-zinc-900/60 border border-zinc-800 rounded-lg px-3 py-2.5 text-sm text-zinc-300 placeholder:text-zinc-600 focus:outline-none focus:border-purple-500/50 transition-all resize-none"
              />
              <div className="mt-2 flex flex-wrap gap-1.5">
                {EXAMPLE_IDEAS.slice(0, 3).map((idea) => (
                  <button
                    key={idea}
                    onClick={() => setStartupIdea(idea)}
                    className="text-[10px] px-2 py-0.5 rounded-full bg-zinc-800/60 border border-zinc-700/50 text-zinc-500 hover:text-zinc-300 hover:border-purple-500/30 transition-all"
                  >
                    {idea}
                  </button>
                ))}
              </div>
            </div>

            <div>
              <label className="text-xs font-medium text-zinc-400 mb-1.5 block">
                Startup Name{" "}
                <span className="text-zinc-600 font-normal">(optional)</span>
              </label>
              <input
                type="text"
                value={startupName}
                onChange={(e) => setStartupName(e.target.value)}
                placeholder="e.g. InterviewIQ"
                className="w-full bg-zinc-900/60 border border-zinc-800 rounded-lg px-3 py-2 text-sm text-zinc-300 placeholder:text-zinc-600 focus:outline-none focus:border-purple-500/50 transition-all"
              />
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
              {sendToSlack
                ? "Will deliver summary to Slack"
                : "Also deliver summary to Slack"}
            </button>
          </div>
        )}

        {/* Live step timeline — every row is real backend state */}
        {phase !== "idle" && (
          <div className="space-y-1.5">
            {steps.length === 0 && (
              <div className="flex items-center gap-2 text-xs text-zinc-500 px-3 py-2">
                <Loader2 className="w-3.5 h-3.5 animate-spin text-purple-400" />
                Starting pipeline…
              </div>
            )}
            {steps.map((step, i) => (
              <StepRow key={step.key} step={step} index={i} />
            ))}
          </div>
        )}

        {/* Success result */}
        {phase === "done" && result && (
          <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            className="rounded-lg bg-emerald-500/5 border border-emerald-500/20 px-4 py-3 space-y-2"
          >
            <div className="flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
              <p className="text-sm font-semibold text-emerald-400">Research Complete</p>
              <span className="ml-auto text-xs font-mono text-zinc-500">
                {formatElapsed(progress?.duration_ms ?? elapsedMs)}
              </span>
            </div>
            <div className="flex gap-4 text-xs text-zinc-400">
              <span>
                <span className="text-emerald-400 font-semibold">
                  {result.competitors_found}
                </span>{" "}
                competitors
              </span>
              <span>
                <span className="text-brand-400 font-semibold">
                  {result.sources_analyzed}
                </span>{" "}
                sources
              </span>
              <span>
                Score{" "}
                <span className="text-purple-400 font-semibold">
                  {result.research_score}/100
                </span>
              </span>
            </div>
            <p className="text-xs text-zinc-500">Report loaded in the viewer →</p>
          </motion.div>
        )}

        {/* Error */}
        {phase === "failed" && error && (
          <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            className="rounded-lg bg-rose-500/5 border border-rose-500/20 px-4 py-3"
          >
            <p className="text-xs font-semibold text-rose-400 mb-1">Research Failed</p>
            <p className="text-xs text-zinc-500 font-mono break-words">{error}</p>
          </motion.div>
        )}
      </div>

      {/* Footer */}
      <div className="px-5 py-4 border-t border-zinc-800/60 flex items-center justify-end gap-3">
        {phase === "idle" && (
          <button
            onClick={handleGenerate}
            disabled={!startupIdea.trim()}
            className={cn(
              "flex items-center gap-2 px-5 py-2 rounded-lg text-sm font-semibold transition-all",
              startupIdea.trim()
                ? "bg-purple-600 text-white hover:bg-purple-500 shadow-[0_0_20px_rgba(168,85,247,0.3)]"
                : "bg-zinc-800 text-zinc-600 cursor-not-allowed"
            )}
          >
            <Play className="w-3.5 h-3.5" />
            Generate Research
          </button>
        )}
        {phase === "running" && (
          <div className="flex items-center gap-2 text-xs text-zinc-500">
            <Loader2 className="w-3.5 h-3.5 animate-spin text-purple-400" />
            {progress?.current_step_label ?? "Running autonomous research pipeline…"}
          </div>
        )}
        {(phase === "done" || phase === "failed") && (
          <button
            onClick={handleReset}
            className="px-5 py-2 rounded-lg bg-zinc-800 text-sm font-medium text-zinc-200 hover:bg-zinc-700 transition-colors"
          >
            New Research
          </button>
        )}
      </div>
    </motion.div>
  );
}

function StepRow({ step, index }: { step: JobStep; index: number }) {
  const Icon = STEP_ICONS[step.key] ?? FileText;
  const { status } = step;
  const isRunning = status === "running";
  const isDone = status === "done";
  const isFailed = status === "failed";
  const isSkipped = status === "skipped";
  const isPending = status === "pending";

  return (
    <motion.div
      animate={{ opacity: isPending ? 0.3 : isSkipped ? 0.55 : 1 }}
      className={cn(
        "flex items-center gap-2.5 rounded-lg px-3 py-2 border transition-all text-xs",
        isRunning && "bg-purple-500/5 border-purple-500/20",
        isDone && "bg-emerald-500/5 border-emerald-500/10",
        isFailed && "bg-rose-500/5 border-rose-500/20",
        isSkipped && "bg-zinc-800/20 border-zinc-800/50",
        isPending && "bg-zinc-800/20 border-zinc-800/40"
      )}
    >
      <div className="flex-shrink-0 w-4">
        {isRunning && <Loader2 className="w-3.5 h-3.5 text-purple-400 animate-spin" />}
        {isDone && <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />}
        {isFailed && <XCircle className="w-3.5 h-3.5 text-rose-400" />}
        {isSkipped && <MinusCircle className="w-3.5 h-3.5 text-zinc-600" />}
        {isPending && (
          <div className="w-3.5 h-3.5 rounded-full border border-zinc-700 flex items-center justify-center">
            <div className="w-1 h-1 rounded-full bg-zinc-700" />
          </div>
        )}
      </div>

      <Icon
        className={cn(
          "w-3 h-3 flex-shrink-0",
          isRunning
            ? "text-purple-400"
            : isDone
            ? "text-emerald-400/70"
            : "text-zinc-600"
        )}
      />

      <div className="flex-1 min-w-0">
        <span
          className={cn(
            "font-medium block truncate",
            isRunning ? "text-zinc-200" : isDone ? "text-zinc-400" : "text-zinc-600"
          )}
        >
          {`Step ${index + 1}: ${step.label}`}
        </span>
        {step.detail && !isPending && (
          <span className="text-[10px] text-zinc-600 block truncate">{step.detail}</span>
        )}
      </div>

      {/* Real server-measured duration — not an animation estimate */}
      {(isDone || isFailed) && step.duration_ms !== null && (
        <span className="text-[10px] text-zinc-600 font-mono tabular-nums flex-shrink-0">
          {formatElapsed(step.duration_ms)}
        </span>
      )}
      {isSkipped && (
        <span className="text-[10px] text-zinc-600 flex-shrink-0">Skipped</span>
      )}
    </motion.div>
  );
}

function formatElapsed(ms: number): string {
  const s = Math.floor(ms / 1000);
  if (s < 60) return `${s}s`;
  return `${Math.floor(s / 60)}m ${s % 60}s`;
}
