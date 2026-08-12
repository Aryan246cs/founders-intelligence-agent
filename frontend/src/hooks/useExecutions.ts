"use client";

import { useState, useCallback } from "react";
import { usePolling } from "./usePolling";
import { executionsService, normalizeExecution } from "@/services/executions";
import type { WorkflowExecution } from "@/lib/types";

export function useExecutions(limit = 20, pollMs = 15_000) {
  const [executions, setExecutions] = useState<WorkflowExecution[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetch = useCallback(async () => {
    try {
      const data = await executionsService.list(limit);
      setExecutions(data.executions.map(normalizeExecution));
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load executions");
    } finally {
      setLoading(false);
    }
  }, [limit]);

  usePolling(fetch, pollMs);

  return { executions, loading, error, refetch: fetch };
}
