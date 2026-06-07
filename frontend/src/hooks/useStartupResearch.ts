import { useState, useEffect, useCallback } from "react";
import { startupResearchService } from "@/services/startupResearch";
import type { StartupResearchListItem } from "@/lib/types";

export function useStartupResearch(pollInterval = 30_000) {
  const [reports, setReports] = useState<StartupResearchListItem[]>([]);
  const [loading, setLoading] = useState(true);

  const fetch = useCallback(async () => {
    try {
      const data = await startupResearchService.list(20);
      setReports(data.reports);
    } catch {
      // silently ignore — page still renders with empty state
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetch();
    const id = setInterval(fetch, pollInterval);
    return () => clearInterval(id);
  }, [fetch, pollInterval]);

  return { reports, loading, refetch: fetch };
}
