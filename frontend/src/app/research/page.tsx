"use client";

import { motion } from "framer-motion";
import { Globe, ArrowRight } from "lucide-react";
import Link from "next/link";

export default function ResearchPage() {
  return (
    <div className="relative min-h-screen flex items-center justify-center">
      <div className="fixed inset-0 grid-bg pointer-events-none opacity-40" />
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        className="relative text-center space-y-4"
      >
        <div className="w-12 h-12 rounded-xl bg-brand-500/10 border border-brand-500/20 flex items-center justify-center mx-auto">
          <Globe className="w-6 h-6 text-brand-400" />
        </div>
        <h1 className="text-xl font-bold text-zinc-200">Research Console</h1>
        <p className="text-zinc-500 text-sm max-w-sm">
          Research is triggered autonomously via the workflow engine. View results in Briefings.
        </p>
        <Link
          href="/briefings"
          className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-brand-500/10 border border-brand-500/20 text-sm font-medium text-brand-400 hover:bg-brand-500/20 transition-all"
        >
          View Briefings <ArrowRight className="w-4 h-4" />
        </Link>
      </motion.div>
    </div>
  );
}
