import { api } from "./api";
import type { MemoryComparison } from "@/lib/types";

export interface MemoryComparisonsResponse {
  comparisons: MemoryComparison[];
  total: number;
}

export interface MemoryStats {
  totalSnapshots: number;
  comparisonsRun: number;
  signalsDetected: number;
  competitorsTracked: number;
}

export const memoryService = {
  listComparisons: (limit = 20, changesOnly = true) =>
    api.get<MemoryComparisonsResponse>(
      `/api/memory/comparisons?limit=${limit}&changes_only=${changesOnly}`
    ),

  getStats: () => api.get<MemoryStats>("/api/memory/stats"),
};
