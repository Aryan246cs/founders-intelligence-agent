"use client";

import { motion } from "framer-motion";
import { Globe, Crosshair, Brain, Lightbulb, Send } from "lucide-react";
import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import type { Agent } from "@/lib/types";

const iconMap: Record<string, React.ElementType> = {
  Globe, Crosshair, Brain, Lightbulb, Send,
};

const statusConfig = {
  active: { label: "Active", badge: "success" as const, dot: "status-dot-green" },
  running: { label: "Running", badge: "info" as const, dot: "status-dot-blue" },
  idle: { label: "Idle", badge: "default" as const, dot: "status-dot-amber" },
  error: { label: "Error", badge: "error" as const, dot: "status-dot-red" },
};

interface AgentStatusGridProps {
  agents: Agent[];
}

export function AgentStatusGrid({ agents }: AgentStatusGridProps) {
  return (
    <div className="glass rounded-xl border border-zinc-800/60 overflow-hidden">
      <div className="px-6 py-4 border-b border-zinc-800/60 flex items-center justify-between">
        <div>
          <h3 className="text-sm font-semibold text-zinc-200">Autonomous Agents</h3>
          <p className="text-xs text-zinc-500 mt-0.5">Real-time agent status and execution metrics</p>
        </div>
        <Badge variant="success">5 Healthy</Badge>
      </div>

      <div className="divide-y divide-zinc-800/40">
        {agents.map((agent, i) => {
          const Icon = iconMap[agent.icon] ?? Globe;
          const status = statusConfig[agent.status];

          return (
            <motion.div
              key={agent.id}
              initial={{ opacity: 0, x: -8 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: i * 0.07 }}
              className="flex items-center gap-4 px-6 py-4 hover:bg-zinc-800/20 transition-colors group"
            >
              {/* Icon */}
              <div className="w-9 h-9 rounded-lg bg-zinc-800/60 border border-zinc-700/40 flex items-center justify-center flex-shrink-0 group-hover:border-zinc-600/60 transition-colors">
                <Icon className="w-4 h-4 text-zinc-400" />
              </div>

              {/* Info */}
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <p className="text-sm font-medium text-zinc-200 truncate">{agent.name}</p>
                  {agent.status === "running" && (
                    <motion.div
                      animate={{ opacity: [0.4, 1, 0.4] }}
                      transition={{ duration: 1, repeat: Infinity }}
                      className="w-1.5 h-1.5 rounded-full bg-brand-400"
                    />
                  )}
                </div>
                <p className="text-xs text-zinc-500 truncate mt-0.5">{agent.description}</p>
              </div>

              {/* Stats */}
              <div className="hidden md:flex items-center gap-6 text-right flex-shrink-0">
                <div>
                  <p className="text-xs text-zinc-600">Last run</p>
                  <p className="text-xs font-medium text-zinc-300">{agent.lastExecution}</p>
                </div>
                <div>
                  <p className="text-xs text-zinc-600">Uptime</p>
                  <p className="text-xs font-medium text-emerald-400">{agent.uptime}</p>
                </div>
                <div>
                  <p className="text-xs text-zinc-600">Executions</p>
                  <p className="text-xs font-medium text-zinc-300 tabular-nums">{agent.executionCount.toLocaleString()}</p>
                </div>
                <Badge variant={status.badge}>{status.label}</Badge>
              </div>
            </motion.div>
          );
        })}
      </div>
    </div>
  );
}
