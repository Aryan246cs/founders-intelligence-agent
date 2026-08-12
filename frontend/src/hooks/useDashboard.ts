"use client";

import { useState, useCallback } from "react";
import { usePolling } from "./usePolling";
import { dashboardService } from "@/services/dashboard";
import type { DashboardStats, ActivityEvent } from "@/services/dashboard";

export function useDashboardStats(pollMs = 30_000) {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetch = useCallback(async () => {
    try {
      const data = await dashboardService.getStats();
      setStats(data);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load stats");
    } finally {
      setLoading(false);
    }
  }, []);

  usePolling(fetch, pollMs);

  // Every number rendered on the dashboard is an aggregate the backend computed
  // from the database. When the backend cannot be reached the UI shows nothing
  // rather than a plausible-looking placeholder.
  return {
    kpis: stats?.kpis ?? [],
    chartData: stats?.chartData ?? [],
    loading,
    error,
    refetch: fetch,
  };
}

export function useActivityFeed(pollMs = 10_000) {
  const [events, setEvents] = useState<ActivityEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetch = useCallback(async () => {
    try {
      const data = await dashboardService.getActivityFeed(20);
      setEvents(data.events);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load activity");
    } finally {
      setLoading(false);
    }
  }, []);

  usePolling(fetch, pollMs);

  return { events, loading, error };
}
