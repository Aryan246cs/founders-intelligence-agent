"use client";

import { motion } from "framer-motion";
import { ArrowRight } from "lucide-react";

const nodes = [
  {
    label: "Sources",
    tech: "Apify",
    color: "from-zinc-700 to-zinc-800",
    border: "border-zinc-600/40",
    dot: "bg-zinc-400",
    desc: "Web scraping",
  },
  {
    label: "AI Agents",
    tech: "Groq + LLaMA",
    color: "from-brand-500/20 to-brand-600/10",
    border: "border-brand-500/30",
    dot: "bg-brand-400",
    desc: "Intelligence extraction",
  },
  {
    label: "Memory Engine",
    tech: "Supabase",
    color: "from-emerald-500/20 to-emerald-600/10",
    border: "border-emerald-500/30",
    dot: "bg-emerald-400",
    desc: "Historical comparison",
  },
  {
    label: "Insight Layer",
    tech: "n8n + Groq",
    color: "from-purple-500/20 to-purple-600/10",
    border: "border-purple-500/30",
    dot: "bg-purple-400",
    desc: "Signal detection",
  },
  {
    label: "Slack Delivery",
    tech: "Slack API",
    color: "from-amber-500/20 to-amber-600/10",
    border: "border-amber-500/30",
    dot: "bg-amber-400",
    desc: "Executive briefing",
  },
];

export function PipelineViz() {
  return (
    <div className="glass rounded-xl p-6 border border-zinc-800/60">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-sm font-semibold text-zinc-200">Intelligence Pipeline</h3>
          <p className="text-xs text-zinc-500 mt-0.5">End-to-end autonomous execution flow</p>
        </div>
        <div className="flex items-center gap-1.5">
          <motion.div
            animate={{ scale: [1, 1.4, 1] }}
            transition={{ duration: 1.5, repeat: Infinity }}
            className="w-1.5 h-1.5 rounded-full bg-emerald-400"
            style={{ boxShadow: "0 0 6px rgba(52,211,153,0.8)" }}
          />
          <span className="text-xs text-emerald-400 font-medium">Live</span>
        </div>
      </div>

      <div className="flex items-center gap-2 overflow-x-auto pb-2">
        {nodes.map((node, i) => (
          <div key={node.label} className="flex items-center gap-2 flex-shrink-0">
            <motion.div
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: i * 0.1, duration: 0.3 }}
              whileHover={{ scale: 1.03, transition: { duration: 0.15 } }}
              className={`relative rounded-xl border bg-gradient-to-br ${node.color} ${node.border} p-4 w-36 cursor-default`}
            >
              {/* Animated dot */}
              <motion.div
                animate={{ opacity: [0.5, 1, 0.5] }}
                transition={{ duration: 2, repeat: Infinity, delay: i * 0.3 }}
                className={`w-2 h-2 rounded-full ${node.dot} mb-3`}
                style={{ boxShadow: `0 0 8px currentColor` }}
              />
              <p className="text-xs font-semibold text-zinc-200">{node.label}</p>
              <p className="text-[10px] text-zinc-500 mt-0.5">{node.tech}</p>
              <p className="text-[10px] text-zinc-600 mt-1">{node.desc}</p>

              {/* Flow particle */}
              {i < nodes.length - 1 && (
                <motion.div
                  className="absolute -right-3 top-1/2 -translate-y-1/2 w-1.5 h-1.5 rounded-full bg-brand-400/60"
                  animate={{ x: [0, 8, 0], opacity: [0, 1, 0] }}
                  transition={{ duration: 1.5, repeat: Infinity, delay: i * 0.3 }}
                />
              )}
            </motion.div>

            {i < nodes.length - 1 && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: i * 0.1 + 0.2 }}
              >
                <ArrowRight className="w-4 h-4 text-zinc-700 flex-shrink-0" />
              </motion.div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
