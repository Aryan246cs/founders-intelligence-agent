"use client";

import { useState } from "react";
import { runResearch, monitorCompetitor, getFindings } from "@/lib/api";

export default function ResearchPage() {
  const [query, setQuery] = useState("");
  const [competitor, setCompetitor] = useState({ name: "", website: "" });
  const [findings, setFindings] = useState<any[]>([]);
  const [status, setStatus] = useState("");

  const handleResearch = async () => {
    if (!query) return;
    setStatus("Queuing research...");
    await runResearch(query);
    setStatus("Research queued. Results will appear shortly.");
  };

  const handleCompetitor = async () => {
    if (!competitor.name || !competitor.website) return;
    setStatus("Queuing competitor monitor...");
    await monitorCompetitor(competitor.name, competitor.website);
    setStatus(`Monitoring queued for ${competitor.name}`);
  };

  const loadFindings = async () => {
    const res = await getFindings(20);
    setFindings(res.data.findings ?? []);
  };

  return (
    <div className="space-y-8">
      <h1 className="text-2xl font-bold">Research</h1>

      {status && <p className="text-sm text-brand-500">{status}</p>}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-gray-900 border border-gray-800 rounded-lg p-5 space-y-3">
          <h2 className="font-semibold">Market Research</h2>
          <input
            className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-sm"
            placeholder="e.g. AI agent frameworks 2024"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
          <button onClick={handleResearch} className="bg-brand-500 text-white px-4 py-2 rounded text-sm">
            Run Research
          </button>
        </div>

        <div className="bg-gray-900 border border-gray-800 rounded-lg p-5 space-y-3">
          <h2 className="font-semibold">Competitor Monitor</h2>
          <input
            className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-sm"
            placeholder="Competitor name"
            value={competitor.name}
            onChange={(e) => setCompetitor({ ...competitor, name: e.target.value })}
          />
          <input
            className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-sm"
            placeholder="https://competitor.com"
            value={competitor.website}
            onChange={(e) => setCompetitor({ ...competitor, website: e.target.value })}
          />
          <button onClick={handleCompetitor} className="bg-brand-500 text-white px-4 py-2 rounded text-sm">
            Monitor Competitor
          </button>
        </div>
      </div>

      <div>
        <div className="flex items-center justify-between mb-3">
          <h2 className="font-semibold text-gray-300">Findings</h2>
          <button onClick={loadFindings} className="text-xs text-brand-500 hover:underline">Refresh</button>
        </div>
        <ul className="space-y-3">
          {findings.map((f) => (
            <li key={f.id} className="bg-gray-900 border border-gray-800 rounded-lg p-4">
              <p className="font-medium text-sm">{f.title}</p>
              <p className="text-gray-400 text-xs mt-1">{f.summary}</p>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
