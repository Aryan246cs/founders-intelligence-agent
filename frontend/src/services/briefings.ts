import { api } from "./api";
import type { Briefing } from "@/lib/types";

export interface BriefingsResponse {
  briefings: Briefing[];
  total: number;
}

export interface GenerateBriefingRequest {
  time_range_days?: number;
  send_to_slack?: boolean;
}

export const briefingsService = {
  list: (limit = 10) =>
    api.get<BriefingsResponse>(`/api/briefings/?limit=${limit}`),

  get: (id: string) =>
    api.get<Briefing>(`/api/briefings/${id}`),

  generate: (opts: GenerateBriefingRequest = {}) =>
    api.post<{ status: string }>("/api/briefings/generate", {
      time_range_days: opts.time_range_days ?? 7,
      send_to_slack: opts.send_to_slack ?? false,
    }),
};
