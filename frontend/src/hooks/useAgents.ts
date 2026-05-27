"use client";

import { useState, useCallback } from "react";
import { usePolling } from "./usePolling";
import { agentsService } from "@/services/agents";
import { mockAgents } from "@/lib/mock-data";
import type { Agent } from "@/lib/types";

export function useAgents(pollMs = 15_000) {
  const [agents, setAgents] = useState<Agent[]>(mockAgents);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetch = useCallback(async () => {
    try {
      const data = await agentsService.getStatus();
      if (data.agents.length > 0) {
        setAgents(data.agents);
      }
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load agents");
    } finally {
      setLoading(false);
    }
  }, []);

  usePolling(fetch, pollMs);

  return { agents, loading, error };
}
