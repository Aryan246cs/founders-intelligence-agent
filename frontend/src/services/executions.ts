import { api } from "./api";
import type { WorkflowExecution } from "@/lib/types";

export interface ExecutionsResponse {
  executions: WorkflowExecution[];
  total: number;
}

export interface RunWorkflowRequest {
  request: string;
  send_to_slack?: boolean;
  trigger_source?: string;
}

export interface ExecutionStats {
  total: number;
  completed: number;
  failed: number;
  avgDurationMs: number;
}

export const executionsService = {
  list: (limit = 20) =>
    api.get<ExecutionsResponse>(`/api/workflows/executions?limit=${limit}`),

  getStatus: (executionId: string) =>
    api.get<WorkflowExecution>(`/api/workflows/status/${executionId}`),

  run: (opts: RunWorkflowRequest) =>
    api.post<WorkflowExecution>("/api/workflows/run", {
      request: opts.request,
      send_to_slack: opts.send_to_slack ?? false,
      trigger_source: opts.trigger_source ?? "manual",
    }),

  /** Poll until status is no longer 'running', with timeout */
  poll: async (
    executionId: string,
    onUpdate: (exec: WorkflowExecution) => void,
    intervalMs = 2000,
    timeoutMs = 300_000
  ): Promise<WorkflowExecution> => {
    const start = Date.now();
    return new Promise((resolve, reject) => {
      const tick = async () => {
        try {
          const exec = await executionsService.getStatus(executionId);
          onUpdate(exec);
          if (exec.status !== "running") {
            resolve(exec);
            return;
          }
          if (Date.now() - start > timeoutMs) {
            reject(new Error("Execution polling timed out"));
            return;
          }
          setTimeout(tick, intervalMs);
        } catch (err) {
          reject(err);
        }
      };
      tick();
    });
  },
};
