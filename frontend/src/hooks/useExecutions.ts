"use client";

import { useState, useCallback } from "react";
import { usePolling } from "./usePolling";
import { executionsService } from "@/services/executions";
import { mockExecutions } from "@/lib/mock-data";
import type { WorkflowExecution } from "@/lib/types";

export function useExecutions(limit = 20, pollMs = 15_000) {
  const [executions, setExecutions] = useState<WorkflowExecution[]>(mockExecutions);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetch = useCallback(async () => {
    try {
      const data = await executionsService.list(limit);
      if (data.executions.length > 0) {
        // Normalize backend shape to frontend shape
        const normalized = data.executions.map(normalizeExecution);
        setExecutions(normalized);
      }
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

/** Map backend execution_id field to frontend executionId */
function normalizeExecution(raw: Record<string, unknown>): WorkflowExecution {
  return {
    id: (raw.id as string) ?? "",
    executionId: (raw.execution_id as string) ?? (raw.id as string) ?? "",
    status: (raw.status as WorkflowExecution["status"]) ?? "completed",
    triggerSource: (raw.trigger_source as string) ?? "api",
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
    error: raw.error as string | undefined,
    steps: undefined, // steps not returned by list endpoint
  };
}
