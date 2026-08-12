"use client";

import { motion } from "framer-motion";
import {
  Settings,
  Slack,
  Database,
  Zap,
  Globe,
  Cpu,
  RefreshCw,
  ShieldCheck,
  CheckCircle2,
  XCircle,
  MinusCircle,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { useHealth } from "@/hooks/useHealth";
import type { ServiceHealth } from "@/lib/types";

const SERVICE_META: Record<
  string,
  { icon: React.ElementType; description: string; envVar: string }
> = {
  Supabase: {
    icon: Database,
    description: "Persistent memory, findings, briefings and execution history",
    envVar: "SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY",
  },
  Groq: {
    icon: Cpu,
    description: "LLM inference for planning, extraction and report generation",
    envVar: "GROQ_API_KEY, GROQ_MODEL",
  },
  Apify: {
    icon: Globe,
    description: "Google search and website crawling for competitor discovery",
    envVar: "APIFY_API_TOKEN",
  },
  Slack: {
    icon: Slack,
    description: "Executive briefing delivery to your team channel",
    envVar: "SLACK_WEBHOOK_URL",
  },
  n8n: {
    icon: Zap,
    description: "Scheduled workflow orchestration via webhooks",
    envVar: "N8N_WEBHOOK_BASE_URL",
  },
};

export default function SettingsPage() {
  const { health, loading, refetch } = useHealth(60_000);

  return (
    <div className="relative min-h-screen">
      <div className="fixed inset-0 grid-bg pointer-events-none opacity-40" />

      <div className="relative px-8 py-8 space-y-8 max-w-3xl">
        <motion.div
          initial={{ opacity: 0, y: -8 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex items-start justify-between"
        >
          <div>
            <div className="flex items-center gap-2 mb-1">
              <Settings className="w-5 h-5 text-zinc-400" />
              <h1 className="text-2xl font-bold text-zinc-100">Settings</h1>
            </div>
            <p className="text-zinc-500 text-sm">
              Live status of every external dependency, probed from the backend.
            </p>
          </div>
          <div className="flex items-center gap-2">
            {health && (
              <Badge
                variant={
                  health.status === "healthy"
                    ? "success"
                    : health.status === "degraded"
                    ? "warning"
                    : "error"
                }
              >
                {health.healthy_count}/{health.total_count} connected
              </Badge>
            )}
            <button
              onClick={refetch}
              className="w-8 h-8 rounded-lg bg-zinc-800/60 border border-zinc-700/40 flex items-center justify-center hover:bg-zinc-700/60 transition-colors"
              title="Re-check services"
            >
              <RefreshCw
                className={`w-3.5 h-3.5 text-zinc-400 ${loading ? "animate-spin" : ""}`}
              />
            </button>
          </div>
        </motion.div>

        {/* Credentials live server-side. Saying so is more useful than
            rendering password boxes that cannot do anything. */}
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.05 }}
          className="rounded-xl bg-brand-500/5 border border-brand-500/15 px-5 py-4 flex items-start gap-3"
        >
          <ShieldCheck className="w-4 h-4 text-brand-400 flex-shrink-0 mt-0.5" />
          <div>
            <p className="text-xs font-semibold text-brand-400 mb-1">
              Credentials are server-side only
            </p>
            <p className="text-xs text-zinc-400 leading-relaxed">
              API keys are read from{" "}
              <code className="text-zinc-300 font-mono">backend/.env</code> and never
              reach the browser — the frontend only ever learns whether a service
              answered. To change a key, edit that file and restart the backend, then
              re-check here.
            </p>
          </div>
        </motion.div>

        {/* Integrations */}
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
        >
          <h2 className="text-sm font-semibold text-zinc-400 uppercase tracking-wider mb-4">
            Integrations
          </h2>

          {!health && loading && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {Array.from({ length: 4 }).map((_, i) => (
                <div
                  key={i}
                  className="glass rounded-xl border border-zinc-800/60 p-5 h-[104px] animate-pulse"
                />
              ))}
            </div>
          )}

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {health?.services.map((service, i) => (
              <ServiceCard key={service.name} service={service} index={i} />
            ))}
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.25 }}
        >
          <h2 className="text-sm font-semibold text-zinc-400 uppercase tracking-wider mb-4">
            Environment
          </h2>
          <div className="glass rounded-xl border border-zinc-800/60 p-6 space-y-3">
            <Row label="Backend environment" value={health?.env ?? "unknown"} />
            <Row
              label="API base URL"
              value={process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"}
            />
            <Row
              label="Preflight check"
              value="cd backend && ./venv/bin/python scripts/doctor.py"
            />
          </div>
        </motion.div>
      </div>
    </div>
  );
}

function ServiceCard({ service, index }: { service: ServiceHealth; index: number }) {
  const meta = SERVICE_META[service.name];
  const Icon = meta?.icon ?? Globe;
  const StatusIcon = service.ok
    ? CheckCircle2
    : service.configured
    ? XCircle
    : MinusCircle;

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.1 + index * 0.06 }}
      className="glass rounded-xl border border-zinc-800/60 p-5 flex items-start gap-4"
    >
      <div className="w-9 h-9 rounded-lg bg-zinc-800/60 border border-zinc-700/40 flex items-center justify-center flex-shrink-0">
        <Icon className="w-4 h-4 text-zinc-400" />
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center justify-between gap-2 mb-1">
          <p className="text-sm font-semibold text-zinc-200">{service.name}</p>
          <span
            className={`inline-flex items-center gap-1 text-[10px] font-medium ${
              service.ok
                ? "text-emerald-400"
                : service.configured
                ? "text-rose-400"
                : "text-amber-400"
            }`}
          >
            <StatusIcon className="w-3 h-3" />
            {service.ok
              ? "Connected"
              : service.configured
              ? "Error"
              : "Not configured"}
          </span>
        </div>
        <p className="text-xs text-zinc-500">{meta?.description}</p>
        <p
          className={`text-xs mt-1.5 ${
            service.ok ? "text-zinc-600" : "text-zinc-400"
          }`}
        >
          {service.detail}
        </p>
        {meta?.envVar && (
          <p className="text-[10px] text-zinc-700 font-mono mt-1.5">{meta.envVar}</p>
        )}
      </div>
    </motion.div>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between gap-4">
      <span className="text-xs text-zinc-500">{label}</span>
      <code className="text-xs text-zinc-300 font-mono truncate">{value}</code>
    </div>
  );
}
