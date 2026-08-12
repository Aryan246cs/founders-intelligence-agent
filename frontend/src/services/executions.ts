import { api } from "./api";
import type { WorkflowExecution } from "@/lib/types";

/**
 * Raw shape returned by the backend. The API speaks snake_case (it is also
 * consumed by n8n expressions written against those names); the UI speaks
 * camelCase. `normalizeExecution` is the single place that translation happens.
 */
export interface RawExecution {
  id: string;
  execution_id: string;
  status: WorkflowExecution["status"];
  trigger_source: string;
  request_summary: string;
  plan_summary: string;
  steps_total: number;
  steps_completed: number;
  briefing_available: boolean;
  briefing_id: string | null;
  slack_delivered: boolean;
  comparison_ran: boolean;
  has_competitor_changes: boolean;
  error: string | null;
  started_at: string;
  completed_at: string | null;
  duration_ms: number | null;
}

export interface ExecutionsResponse {
  executions: RawExecution[];
  total: number;
}

export interface RunWorkflowRequest {
  request: string;
  send_to_slack?: boolean;
  trigger_source?: string;
}

/** Returned immediately by POST /run when `background` is set. */
export interface WorkflowRunResponse {
  job_id: string;
  execution_id: string;
  status: string;
  poll_url: string;
}

export function normalizeExecution(raw: Partial<RawExecution>): WorkflowExecution {
  const id = raw.id ?? raw.execution_id ?? "";
  return {
    id,
    executionId: raw.execution_id ?? id,
    status: raw.status ?? "completed",
    triggerSource: raw.trigger_source ?? "api",
    requestSummary: raw.request_summary ?? "",
    planSummary: raw.plan_summary ?? "",
    stepsTotal: raw.steps_total ?? 0,
    stepsCompleted: raw.steps_completed ?? 0,
    briefingAvailable: raw.briefing_available ?? false,
    slackDelivered: raw.slack_delivered ?? false,
    comparisonRan: raw.comparison_ran ?? false,
    hasCompetitorChanges: raw.has_competitor_changes ?? false,
    startedAt: raw.started_at ?? "",
    completedAt: raw.completed_at ?? "",
    durationMs: raw.duration_ms ?? 0,
    error: raw.error ?? undefined,
    steps: undefined, // the list endpoint does not expand per-step detail
  };
}

export const executionsService = {
  list: (limit = 20) =>
    api.get<ExecutionsResponse>(`/api/workflows/executions?limit=${limit}`),

  getStatus: (executionId: string) =>
    api
      .get<RawExecution>(`/api/workflows/status/${executionId}`)
      .then(normalizeExecution),

  /**
   * Launches the workflow in the background and returns a poll URL. Progress is
   * then read from the job tracker, which reports the real step the pipeline is
   * inside rather than an estimate.
   */
  run: (opts: RunWorkflowRequest) =>
    api.post<WorkflowRunResponse>("/api/workflows/run", {
      request: opts.request,
      send_to_slack: opts.send_to_slack ?? false,
      trigger_source: opts.trigger_source ?? "manual",
      background: true,
    }),
};
