import { api } from "./api";
import type { SystemHealth } from "@/lib/types";

/** Shown when the backend itself is unreachable — the UI must not claim health. */
export const OFFLINE_HEALTH: SystemHealth = {
  status: "offline",
  env: "unknown",
  services: [
    { name: "Supabase", status: "error", ok: false, configured: true, detail: "Backend unreachable" },
    { name: "Groq", status: "error", ok: false, configured: true, detail: "Backend unreachable" },
    { name: "Apify", status: "error", ok: false, configured: true, detail: "Backend unreachable" },
    { name: "Slack", status: "error", ok: false, configured: true, detail: "Backend unreachable" },
    { name: "n8n", status: "error", ok: false, configured: true, detail: "Backend unreachable" },
  ],
  healthy_count: 0,
  total_count: 5,
};

export const healthService = {
  /** Readiness — probes Supabase, Groq, Apify and reports per-service state. */
  getServices: () => api.get<SystemHealth>("/health/services"),
};
