"use client";

import { useState, useCallback } from "react";
import { usePolling } from "./usePolling";
import { dashboardService } from "@/services/dashboard";
import type { DashboardStats, ActivityEvent } from "@/services/dashboard";
import { kpiData, mockActivityFeed } from "@/lib/mock-data";

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

  // Fall back to mock data while loading or on error
  const kpis = stats?.kpis ?? kpiData;
  const chartData = stats?.chartData ?? [];

  return { kpis, chartData, loading, error };
}

export function useActivityFeed(pollMs = 10_000) {
  const [events, setEvents] = useState<ActivityEvent[]>(mockActivityFeed);
  const [loading, setLoading] = useState(true);

  const fetch = useCallback(async () => {
    try {
      const data = await dashboardService.getActivityFeed(20);
      if (data.events.length > 0) {
        setEvents(data.events);
      }
    } catch {
      // Keep showing mock/previous data on error
    } finally {
      setLoading(false);
    }
  }, []);

  usePolling(fetch, pollMs);

  return { events, loading };
}
