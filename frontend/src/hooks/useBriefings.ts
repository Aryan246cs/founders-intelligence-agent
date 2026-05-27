"use client";

import { useState, useCallback } from "react";
import { usePolling } from "./usePolling";
import { briefingsService } from "@/services/briefings";
import { mockBriefings } from "@/lib/mock-data";
import type { Briefing } from "@/lib/types";

export function useBriefings(limit = 10, pollMs = 30_000) {
  const [briefings, setBriefings] = useState<Briefing[]>(mockBriefings);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetch = useCallback(async () => {
    try {
      const data = await briefingsService.list(limit);
      if (data.briefings.length > 0) {
        setBriefings(data.briefings);
      }
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load briefings");
    } finally {
      setLoading(false);
    }
  }, [limit]);

  usePolling(fetch, pollMs);

  return { briefings, loading, error, refetch: fetch };
}
