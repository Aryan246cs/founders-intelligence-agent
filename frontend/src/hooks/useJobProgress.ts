"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "@/services/api";
import type { JobProgress } from "@/lib/types";

interface Options {
  /** Poll interval while the job is running. */
  intervalMs?: number;
  /** Give up after this long. Long crawls legitimately take minutes. */
  timeoutMs?: number;
}

/**
 * Polls a backend job until it reaches a terminal state.
 *
 * The backend owns the step list, so the UI never invents progress: every row
 * that lights up corresponds to a step the pipeline actually entered, and every
 * duration shown is measured server-side.
 */
export function useJobProgress(
  pollPath: string | null,
  { intervalMs = 1500, timeoutMs = 600_000 }: Options = {}
) {
  const [progress, setProgress] = useState<JobProgress | null>(null);
  const [error, setError] = useState<string | null>(null);
  const startedAtRef = useRef<number>(0);
  const consecutiveErrorsRef = useRef(0);

  const reset = useCallback(() => {
    setProgress(null);
    setError(null);
    consecutiveErrorsRef.current = 0;
  }, []);

  useEffect(() => {
    if (!pollPath) return;

    let cancelled = false;
    let timer: ReturnType<typeof setTimeout>;
    startedAtRef.current = Date.now();
    consecutiveErrorsRef.current = 0;

    const tick = async () => {
      if (cancelled) return;
      try {
        const next = await api.get<JobProgress>(pollPath);
        if (cancelled) return;
        consecutiveErrorsRef.current = 0;
        setProgress(next);
        if (next.status === "completed" || next.status === "failed") return;
      } catch (e) {
        // A single dropped poll is not a failed run — the pipeline is still
        // going server-side. Only give up once polling is repeatedly failing.
        consecutiveErrorsRef.current += 1;
        if (consecutiveErrorsRef.current >= 5) {
          setError(e instanceof Error ? e.message : "Lost contact with the backend");
          return;
        }
      }

      if (Date.now() - startedAtRef.current > timeoutMs) {
        setError("Timed out waiting for the pipeline to finish");
        return;
      }
      timer = setTimeout(tick, intervalMs);
    };

    tick();
    return () => {
      cancelled = true;
      clearTimeout(timer);
    };
  }, [pollPath, intervalMs, timeoutMs]);

  return { progress, error, reset };
}
