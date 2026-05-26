"use client";

import { motion } from "framer-motion";
import { TrendingUp, TrendingDown } from "lucide-react";
import { cn } from "@/lib/utils";

interface KpiCardProps {
  label: string;
  value: string | number;
  delta?: string;
  deltaPositive?: boolean;
  color: string;
  index: number;
}

const colorMap: Record<string, string> = {
  brand: "from-brand-500/20 to-brand-500/5 border-brand-500/20 text-brand-400",
  emerald: "from-emerald-500/20 to-emerald-500/5 border-emerald-500/20 text-emerald-400",
  purple: "from-purple-500/20 to-purple-500/5 border-purple-500/20 text-purple-400",
  amber: "from-amber-500/20 to-amber-500/5 border-amber-500/20 text-amber-400",
  rose: "from-rose-500/20 to-rose-500/5 border-rose-500/20 text-rose-400",
  violet: "from-violet-500/20 to-violet-500/5 border-violet-500/20 text-violet-400",
};

export function KpiCard({ label, value, delta, deltaPositive, color, index }: KpiCardProps) {
  const colors = colorMap[color] ?? colorMap.brand;

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay: index * 0.06 }}
      whileHover={{ y: -2, transition: { duration: 0.15 } }}
      className={cn(
        "relative overflow-hidden rounded-xl border bg-gradient-to-br p-5 cursor-default",
        colors
      )}
    >
      {/* Glow orb */}
      <div className="absolute -top-4 -right-4 w-16 h-16 rounded-full opacity-20 blur-xl bg-current" />

      <div className="relative">
        <p className="text-xs font-medium text-zinc-500 uppercase tracking-wider">{label}</p>
        <p className="text-3xl font-bold text-zinc-100 mt-2 tabular-nums">{value}</p>
        {delta && (
          <div className="flex items-center gap-1 mt-2">
            {deltaPositive ? (
              <TrendingUp className="w-3 h-3 text-emerald-400" />
            ) : (
              <TrendingDown className="w-3 h-3 text-rose-400" />
            )}
            <span className={cn("text-xs font-medium", deltaPositive ? "text-emerald-400" : "text-rose-400")}>
              {delta}
            </span>
          </div>
        )}
      </div>

      {/* Animated pulse bar */}
      <motion.div
        className="absolute bottom-0 left-0 h-0.5 bg-current opacity-40"
        initial={{ width: "0%" }}
        animate={{ width: "100%" }}
        transition={{ duration: 1.5, delay: index * 0.1, ease: "easeOut" }}
      />
    </motion.div>
  );
}
