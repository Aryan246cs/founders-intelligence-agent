import { api } from "./api";

export interface KpiMetric {
  label: string;
  value: string;
  delta: string;
  deltaPositive: boolean;
  color: string;
}

export interface ChartDataPoint {
  day: string;
  completed: number;
  failed: number;
}

export interface DashboardStats {
  kpis: KpiMetric[];
  chartData: ChartDataPoint[];
}

export interface ActivityEvent {
  id: string;
  timestamp: string;
  message: string;
  type: "info" | "success" | "warning" | "error";
  agent?: string;
  loggedAt?: string;
}

export interface ActivityFeedResponse {
  events: ActivityEvent[];
  total: number;
}

export const dashboardService = {
  getStats: () => api.get<DashboardStats>("/api/dashboard/stats"),
  getActivityFeed: (limit = 20) =>
    api.get<ActivityFeedResponse>(`/api/activity/feed?limit=${limit}`),
};
