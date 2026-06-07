"use client";

import { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
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
} from "lucide-react";
import { cn } from "@/lib/utils";
import { startupResearchService } from "@/services/startupResearch";
import type { StartupResearchReport } from "@/lib/types";

interface Props {
  onReportReady: (report: StartupResearchReport) => void;
}

const RESEARCH_STEPS = [
  { id: "parse", label: "Understanding startup idea", icon: Lightbulb, color: "text-amber-400" },
  { id: "keywords", label: "Identifying industry & keywords", icon: Tag, color: "text-brand-400" },
  { id: "search", label: "Searching for competitors", icon: Search, color: "text-purple-400" },
  { id: "scrape", label: "Analyzing competitor websites", icon: Globe, color: "text-emerald-400" },
  { id: "pricing", label: "Gathering pricing intelligence", icon: BarChart2, color: "text-rose-400" },
  { id: "positioning", label: "Extracting positioning signals", icon: FileText, color: "text-cyan-400" },
  { id: "insights", label: "Generating strategic insights", icon: Star, color: "text-amber-400" },
  { id: "report", label: "Building founder report", icon: Brain, color: "text-purple-400" },
  { id: "memory", label: "Saving to memory", icon: Brain, color: "text-brand-400" },
  { id: "complete", label: "Report complete", icon: CheckCircle2, color: "text-emerald-400" },
];

// Realistic timing (ms) each step holds before auto-advancing
const STEP_DURATIONS = [6000, 4000, 8000, 25000, 20000, 8000, 10000, 6000, 4000, 2000];

const EXAMPLE_IDEAS = [
  "AI-powered interview preparation platform",
  "Voice AI receptionist for healthcare clinics",
  "Autonomous social media content generator",
  "AI-powered legal document assistant",
  "No-code workflow automation for SMBs",
];

type Phase = "idle" | "running" | "done" | "failed";
type StepStatus = "pending" | "running" | "done" | "failed";

interface StepState {
  id: string;
  status: StepStatus;
}

export function ResearchLauncher({ onReportReady }: Props) {
  const [phase, setPhase] = useState<Phase>("idle");
  const [startupIdea, setStartupIdea] = useState("");
  const [startupName, setStartupName] = useState("");
  const [sendToSlack, setSendToSlack] = useState(false);
  const [steps, setSteps] = useState<StepState[]>(
    RESEARCH_STEPS.map((s) => ({ id: s.id, status: "pending" }))
  );
  const [elapsedMs, setElapsedMs] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [resultMeta, setResultMeta] = useState<{
    competitorsFound: number;
    sourcesAnalyzed: number;
    researchScore: number;
  } | null>(null);

  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const animTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const startTimeRef = useRef<number>(0);
  const workflowDoneRef = useRef(false);

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

  const startStepAnimation = () => {
    let currentStep = 0;
    workflowDoneRef.current = false;
    setSteps((prev) =>
      prev.map((s, i) => ({ ...s, status: i === 0 ? "running" : "pending" }))
    );

    const advance = () => {
      if (workflowDoneRef.current) return;
      const nextStep = currentStep + 1;
      if (nextStep < RESEARCH_STEPS.length) {
        setSteps((prev) =>
          prev.map((s, i) => {
            if (i < nextStep) return { ...s, status: "done" };
            if (i === nextStep) return { ...s, status: "running" };
            return s;
          })
        );
        currentStep = nextStep;
        animTimerRef.current = setTimeout(advance, STEP_DURATIONS[nextStep] ?? 8000);
      }
    };
    animTimerRef.current = setTimeout(advance, STEP_DURATIONS[0]);
  };

  const stopStepAnimation = () => {
    workflowDoneRef.current = true;
    if (animTimerRef.current) clearTimeout(animTimerRef.current);
  };

  const handleGenerate = async () => {
    if (!startupIdea.trim()) return;
    setPhase("running");
    setError(null);
    setResultMeta(null);
    startStepAnimation();

    try {
      const result = await startupResearchService.run({
        startup_idea: startupIdea.trim(),
        startup_name: startupName.trim() || undefined,
        send_to_slack: sendToSlack,
      });

      stopStepAnimation();
      setSteps((prev) => prev.map((s) => ({ ...s, status: "done" })));
      setResultMeta({
        competitorsFound: result.competitors_found,
        sourcesAnalyzed: result.sources_analyzed,
        researchScore: result.research_score,
      });
      setPhase("done");

      // Fetch full report and surface it
      const fullReport = await startupResearchService.get(result.report_id);
      onReportReady(fullReport);
    } catch (e) {
      const msg = e instanceof Error ? e.message : "Research pipeline failed";
      stopStepAnimation();
      setError(msg);
      setPhase("failed");
      setSteps((prev) =>
        prev.map((s) => (s.status === "running" ? { ...s, status: "failed" } : s))
      );
    }
  };

  const handleReset = () => {
    setPhase("idle");
    setError(null);
    setResultMeta(null);
    setSteps(RESEARCH_STEPS.map((s) => ({ id: s.id, status: "pending" })));
    setElapsedMs(0);
    workflowDoneRef.current = false;
  };

  const formatElapsed = (ms: number) => {
    const s = Math.floor(ms / 1000);
    if (s < 60) return `${s}s`;
    return `${Math.floor(s / 60)}m ${s % 60}s`;
  };

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
              {/* Example ideas */}
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
              {sendToSlack ? "Will deliver summary to Slack" : "Also deliver summary to Slack"}
            </button>
          </div>
        )}

        {/* Step timeline — shown during/after run */}
        {(phase === "running" || phase === "done" || phase === "failed") && (
          <div className="space-y-1.5">
            {RESEARCH_STEPS.map((step, i) => {
              const stepState = steps[i];
              const Icon = step.icon;
              const isRunning = stepState.status === "running";
              const isDone = stepState.status === "done";
              const isFailed = stepState.status === "failed";
              const isPending = stepState.status === "pending";

              return (
                <motion.div
                  key={step.id}
                  animate={{ opacity: isPending ? 0.3 : 1 }}
                  className={cn(
                    "flex items-center gap-2.5 rounded-lg px-3 py-2 border transition-all text-xs",
                    isRunning && "bg-purple-500/5 border-purple-500/20",
                    isDone && "bg-emerald-500/5 border-emerald-500/10",
                    isFailed && "bg-rose-500/5 border-rose-500/20",
                    isPending && "bg-zinc-800/20 border-zinc-800/40"
                  )}
                >
                  {/* Status icon */}
                  <div className="flex-shrink-0 w-4">
                    {isRunning && <Loader2 className="w-3.5 h-3.5 text-purple-400 animate-spin" />}
                    {isDone && <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />}
                    {isFailed && <XCircle className="w-3.5 h-3.5 text-rose-400" />}
                    {isPending && (
                      <div className="w-3.5 h-3.5 rounded-full border border-zinc-700 flex items-center justify-center">
                        <div className="w-1 h-1 rounded-full bg-zinc-700" />
                      </div>
                    )}
                  </div>

                  <Icon
                    className={cn(
                      "w-3 h-3 flex-shrink-0",
                      isRunning ? step.color : isDone ? "text-emerald-400/70" : "text-zinc-600"
                    )}
                  />

                  <span
                    className={cn(
                      "font-medium flex-1",
                      isRunning ? "text-zinc-200" : isDone ? "text-zinc-400" : "text-zinc-600"
                    )}
                  >
                    {`Step ${i + 1}: ${step.label}`}
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
        )}

        {/* Success result */}
        {phase === "done" && resultMeta && (
          <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            className="rounded-lg bg-emerald-500/5 border border-emerald-500/20 px-4 py-3 space-y-2"
          >
            <div className="flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
              <p className="text-sm font-semibold text-emerald-400">Research Complete</p>
              <span className="ml-auto text-xs font-mono text-zinc-500">{formatElapsed(elapsedMs)}</span>
            </div>
            <div className="flex gap-4 text-xs text-zinc-400">
              <span>
                <span className="text-emerald-400 font-semibold">{resultMeta.competitorsFound}</span> competitors
              </span>
              <span>
                <span className="text-brand-400 font-semibold">{resultMeta.sourcesAnalyzed}</span> sources
              </span>
              <span>
                Score{" "}
                <span className="text-purple-400 font-semibold">{resultMeta.researchScore}/100</span>
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
            <p className="text-xs text-zinc-500 font-mono">{error}</p>
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
            Running autonomous research pipeline…
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
