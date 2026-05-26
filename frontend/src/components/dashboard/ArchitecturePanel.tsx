"use client";

import { motion } from "framer-motion";

const layers = [
  { label: "Web Sources", sub: "Apify · Google · News APIs", color: "border-zinc-600/50 bg-zinc-800/30", dot: "bg-zinc-400" },
  { label: "n8n Orchestration", sub: "Workflow automation · Scheduling · Webhooks", color: "border-brand-500/30 bg-brand-500/5", dot: "bg-brand-400" },
  { label: "AI Processing Layer", sub: "Groq LLaMA · Competitor analysis · Research synthesis", color: "border-purple-500/30 bg-purple-500/5", dot: "bg-purple-400" },
  { label: "Memory + Vector Storage", sub: "Supabase · Historical snapshots · Semantic comparison", color: "border-emerald-500/30 bg-emerald-500/5", dot: "bg-emerald-400" },
  { label: "Executive Briefing Engine", sub: "Strategic insight generation · Priority scoring", color: "border-amber-500/30 bg-amber-500/5", dot: "bg-amber-400" },
  { label: "Slack Delivery", sub: "Formatted briefings · Channel routing · Delivery tracking", color: "border-rose-500/30 bg-rose-500/5", dot: "bg-rose-400" },
];

export function ArchitecturePanel() {
  return (
    <div className="glass rounded-xl border border-zinc-800/60 p-6">
      <div className="mb-5">
        <h3 className="text-sm font-semibold text-zinc-200">System Architecture</h3>
        <p className="text-xs text-zinc-500 mt-0.5">End-to-end intelligence infrastructure</p>
      </div>

      <div className="relative flex flex-col items-center gap-0">
        {layers.map((layer, i) => (
          <div key={layer.label} className="w-full flex flex-col items-center">
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: i * 0.08 }}
              className={`w-full rounded-lg border px-4 py-3 flex items-center gap-3 ${layer.color}`}
            >
              <motion.div
                animate={{ opacity: [0.5, 1, 0.5] }}
                transition={{ duration: 2.5, repeat: Infinity, delay: i * 0.4 }}
                className={`w-2 h-2 rounded-full flex-shrink-0 ${layer.dot}`}
              />
              <div>
                <p className="text-xs font-semibold text-zinc-200">{layer.label}</p>
                <p className="text-[10px] text-zinc-500 mt-0.5">{layer.sub}</p>
              </div>
            </motion.div>

            {/* Animated connector */}
            {i < layers.length - 1 && (
              <div className="relative w-px h-5 bg-zinc-800 overflow-hidden">
                <motion.div
                  className="absolute top-0 left-0 w-full bg-gradient-to-b from-brand-500/60 to-transparent"
                  animate={{ height: ["0%", "100%", "0%"], top: ["0%", "0%", "100%"] }}
                  transition={{ duration: 1.5, repeat: Infinity, delay: i * 0.25, ease: "linear" }}
                  style={{ height: "40%" }}
                />
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
