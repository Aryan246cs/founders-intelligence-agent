"use client";

import { useCallback, useState } from "react";
import { usePolling } from "./usePolling";
import { healthService, OFFLINE_HEALTH } from "@/services/health";
import type { SystemHealth } from "@/lib/types";

/**
 * Live dependency health.
 *
 * Polled slowly on purpose: each call probes Supabase, Groq and Apify over the
 * network, so a tight interval would spend real API quota to render five dots.
 */
export function useHealth(pollMs = 60_000) {
  const [health, setHealth] = useState<SystemHealth | null>(null);
  const [loading, setLoading] = useState(true);

  const fetch = useCallback(async () => {
    try {
      setHealth(await healthService.getServices());
    } catch {
      // Unreachable backend is itself a health state, not a missing value.
      setHealth(OFFLINE_HEALTH);
    } finally {
      setLoading(false);
    }
  }, []);

  usePolling(fetch, pollMs);

  return {
    health,
    loading,
    /** True only once we have proof the backend answered. */
    online: health !== null && health.status !== "offline",
    refetch: fetch,
  };
}
