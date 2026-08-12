import { api } from "./api";
import type {
  StartupResearchReport,
  StartupResearchListItem,
} from "@/lib/types";

export interface StartupResearchRunRequest {
  startup_idea: string;
  startup_name?: string;
  send_to_slack?: boolean;
}

/** Returned immediately by POST /run — the pipeline continues in the background. */
export interface StartupResearchRunResponse {
  job_id: string;
  execution_id: string;
  status: string;
  steps_total: number;
  poll_url: string;
}

/** The `result` payload attached to the job once it completes. */
export interface StartupResearchResult {
  execution_id: string;
  report_id: string;
  status: string;
  startup_idea: string;
  industry: string;
  competitors_found: number;
  sources_analyzed: number;
  research_score: number;
  sent_to_slack: boolean;
}

export const startupResearchService = {
  run: (req: StartupResearchRunRequest) =>
    api.post<StartupResearchRunResponse>("/api/startup-research/run", req),

  list: (limit = 20) =>
    api.get<{ reports: StartupResearchListItem[]; total: number }>(
      `/api/startup-research/?limit=${limit}`
    ),

  get: (reportId: string) =>
    api.get<StartupResearchReport>(`/api/startup-research/${reportId}`),

  sendToSlack: (reportId: string) =>
    api.post<{ sent: boolean; report_id: string }>(
      `/api/startup-research/${reportId}/slack`,
      {}
    ),
};
