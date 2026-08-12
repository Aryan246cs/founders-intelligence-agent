"use client";

import { useState, useCallback } from "react";
import { usePolling } from "./usePolling";
import { memoryService } from "@/services/memory";
import type { MemoryComparison } from "@/lib/types";

export function useMemoryComparisons(pollMs = 30_000) {
  const [comparisons, setComparisons] = useState<MemoryComparison[]>([]);
  const [stats, setStats] = useState({
    totalSnapshots: 0,
    comparisonsRun: 0,
    signalsDetected: 0,
    competitorsTracked: 0,
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetch = useCallback(async () => {
    try {
      const [compData, statsData] = await Promise.all([
        memoryService.listComparisons(20, true),
        memoryService.getStats(),
      ]);
      setComparisons(compData.comparisons);
      setStats(statsData);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load memory history");
    } finally {
      setLoading(false);
    }
  }, []);

  usePolling(fetch, pollMs);

  return { comparisons, stats, loading, error };
}
