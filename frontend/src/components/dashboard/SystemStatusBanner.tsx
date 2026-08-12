"use client";

import { motion } from "framer-motion";
import { AlertTriangle, WifiOff, CheckCircle2 } from "lucide-react";
import { cn } from "@/lib/utils";
import type { SystemHealth } from "@/lib/types";

interface Props {
  health: SystemHealth | null;
  loading: boolean;
}

/**
 * Surfaces broken dependencies instead of letting the UI imply everything is
 * fine. A dashboard that renders zeros because Supabase is unreachable looks
 * identical to one that renders zeros because nothing has run yet — this is the
 * difference.
 */
export function SystemStatusBanner({ health, loading }: Props) {
  if (loading || !health || health.status === "healthy") return null;

  const broken = health.services.filter((s) => s.configured && !s.ok);
  const offline = health.status === "offline";
  const down = health.status === "down";

  const Icon = offline ? WifiOff : down ? AlertTriangle : CheckCircle2;

  return (
    <motion.div
      initial={{ opacity: 0, y: -8 }}
      animate={{ opacity: 1, y: 0 }}
      className={cn(
        "rounded-xl border px-5 py-4 flex items-start gap-3",
        offline || down
          ? "bg-rose-500/5 border-rose-500/20"
          : "bg-amber-500/5 border-amber-500/20"
      )}
    >
      <Icon
        className={cn(
          "w-4 h-4 flex-shrink-0 mt-0.5",
          offline || down ? "text-rose-400" : "text-amber-400"
        )}
      />
      <div className="min-w-0">
        <p
          className={cn(
            "text-xs font-semibold mb-1",
            offline || down ? "text-rose-400" : "text-amber-400"
          )}
        >
          {offline
            ? "Backend unreachable"
            : down
            ? "Core services unavailable — pipelines cannot run"
            : "Running degraded"}
        </p>
        {offline ? (
          <p className="text-xs text-zinc-400">
            No response from the API. Start it with{" "}
            <code className="text-zinc-300 font-mono">uvicorn main:app --reload</code> in{" "}
            <code className="text-zinc-300 font-mono">backend/</code>. Metrics below are
            empty because nothing could be read — they are not zeroes from the database.
          </p>
        ) : (
          <ul className="space-y-0.5">
            {broken.map((s) => (
              <li key={s.name} className="text-xs text-zinc-400">
                <span className="font-medium text-zinc-300">{s.name}</span> — {s.detail}
              </li>
            ))}
          </ul>
        )}
      </div>
    </motion.div>
  );
}
