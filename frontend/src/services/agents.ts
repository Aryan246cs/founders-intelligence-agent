import { api } from "./api";
import type { Agent } from "@/lib/types";

export interface AgentsStatusResponse {
  agents: Agent[];
}

export const agentsService = {
  getStatus: () => api.get<AgentsStatusResponse>("/api/agents/status"),
};
