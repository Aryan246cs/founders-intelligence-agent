"use client";

import { useState, useCallback } from "react";
import { usePolling } from "./usePolling";
import { memoryService } from "@/services/memory";
import { mockMemoryComparisons } from "@/lib/mock-data";
import type { MemoryComparison } from "@/lib/types";

export function useMemoryComparisons(pollMs = 30_000) {
  const [comparisons, setComparisons] = useState<MemoryComparison[]>(mockMemoryComparisons);
  const [stats, setStats] = useState({
    totalSnapshots: 0,
    comparisonsRun: 0,
    signalsDetected: 0,
    competitorsTracked: 0,
  });
  const [loading, setLoading] = useState(true);

  const fetch = useCallback(async () => {
    try {
      const [compData, statsData] = await Promise.all([
        memoryService.listComparisons(20, true),
        memoryService.getStats(),
      ]);
      if (compData.comparisons.length > 0) {
        setComparisons(compData.comparisons);
      }
      setStats(statsData);
    } catch {
      // Keep showing previous data
    } finally {
      setLoading(false);
    }
  }, []);

  usePolling(fetch, pollMs);

  return { comparisons, stats, loading };
}
