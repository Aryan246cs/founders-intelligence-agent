"use client";

import { motion } from "framer-motion";
import { Settings, Slack, Database, Zap, Key, Bell, Globe } from "lucide-react";
import { Badge } from "@/components/ui/badge";

const integrations = [
  {
    name: "Slack",
    description: "Deliver executive briefings to your team channels",
    icon: Slack,
    status: "connected",
    detail: "#intelligence · #founders",
  },
  {
    name: "n8n",
    description: "Workflow automation and scheduling orchestration",
    icon: Zap,
    status: "connected",
    detail: "3 active workflows",
  },
  {
    name: "Supabase",
    description: "Persistent memory, findings, and execution storage",
    icon: Database,
    status: "connected",
    detail: "2,104 memory entries",
  },
  {
    name: "Apify",
    description: "Web scraping and Google search intelligence",
    icon: Globe,
    status: "connected",
    detail: "142 sources monitored",
  },
];

const sections = [
  {
    title: "API Keys",
    icon: Key,
    fields: [
      { label: "Groq API Key", placeholder: "gsk_••••••••••••••••", type: "password" },
      { label: "Apify API Token", placeholder: "apify_api_••••••••••••", type: "password" },
      { label: "Supabase URL", placeholder: "https://••••••.supabase.co", type: "text" },
    ],
  },
  {
    title: "Notifications",
    icon: Bell,
    fields: [
      { label: "Slack Webhook URL", placeholder: "https://hooks.slack.com/services/••••", type: "text" },
      { label: "Alert Channel", placeholder: "#intelligence", type: "text" },
    ],
  },
];

export default function SettingsPage() {
  return (
    <div className="relative min-h-screen">
      <div className="fixed inset-0 grid-bg pointer-events-none opacity-40" />

      <div className="relative px-8 py-8 space-y-8 max-w-3xl">
        <motion.div initial={{ opacity: 0, y: -8 }} animate={{ opacity: 1, y: 0 }}>
          <div className="flex items-center gap-2 mb-1">
            <Settings className="w-5 h-5 text-zinc-400" />
            <h1 className="text-2xl font-bold text-zinc-100">Settings</h1>
          </div>
          <p className="text-zinc-500 text-sm">Configure integrations, API keys, and platform preferences.</p>
        </motion.div>

        {/* Integrations */}
        <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}>
          <h2 className="text-sm font-semibold text-zinc-400 uppercase tracking-wider mb-4">Integrations</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {integrations.map((integration, i) => {
              const Icon = integration.icon;
              return (
                <motion.div
                  key={integration.name}
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.1 + i * 0.06 }}
                  className="glass rounded-xl border border-zinc-800/60 p-5 flex items-start gap-4"
                >
                  <div className="w-9 h-9 rounded-lg bg-zinc-800/60 border border-zinc-700/40 flex items-center justify-center flex-shrink-0">
                    <Icon className="w-4 h-4 text-zinc-400" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between mb-1">
                      <p className="text-sm font-semibold text-zinc-200">{integration.name}</p>
                      <Badge variant="success">Connected</Badge>
                    </div>
                    <p className="text-xs text-zinc-500">{integration.description}</p>
                    <p className="text-xs text-zinc-600 mt-1.5">{integration.detail}</p>
                  </div>
                </motion.div>
              );
            })}
          </div>
        </motion.div>

        {/* Config sections */}
        {sections.map((section, si) => {
          const Icon = section.icon;
          return (
            <motion.div
              key={section.title}
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 + si * 0.1 }}
            >
              <div className="flex items-center gap-2 mb-4">
                <Icon className="w-4 h-4 text-zinc-500" />
                <h2 className="text-sm font-semibold text-zinc-400 uppercase tracking-wider">{section.title}</h2>
              </div>
              <div className="glass rounded-xl border border-zinc-800/60 p-6 space-y-4">
                {section.fields.map((field) => (
                  <div key={field.label}>
                    <label className="block text-xs font-medium text-zinc-400 mb-1.5">{field.label}</label>
                    <input
                      type={field.type}
                      placeholder={field.placeholder}
                      className="w-full bg-zinc-900/60 border border-zinc-800 rounded-lg px-4 py-2.5 text-sm text-zinc-300 placeholder:text-zinc-700 focus:outline-none focus:border-brand-500/50 transition-all font-mono"
                    />
                  </div>
                ))}
                <div className="pt-2">
                  <button className="px-4 py-2 rounded-lg bg-brand-500/10 border border-brand-500/20 text-sm font-medium text-brand-400 hover:bg-brand-500/20 transition-all">
                    Save Changes
                  </button>
                </div>
              </div>
            </motion.div>
          );
        })}
      </div>
    </div>
  );
}
