"use client";

import { useEffect, useState } from "react";
import { getFindings, getBriefings, generateBriefing } from "@/lib/api";

export default function Dashboard() {
  const [findings, setFindings] = useState<any[]>([]);
  const [briefings, setBriefings] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    getFindings(5).then((r) => setFindings(r.data.findings ?? []));
    getBriefings(3).then((r) => setBriefings(r.data.briefings ?? []));
  }, []);

  const handleGenerateBriefing = async () => {
    setLoading(true);
    await generateBriefing(7);
    setLoading(false);
    alert("Briefing queued — check Slack and the Briefings page.");
  };

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Dashboard</h1>
        <button
          onClick={handleGenerateBriefing}
          disabled={loading}
          className="bg-brand-500 hover:bg-sky-400 disabled:opacity-50 text-white px-4 py-2 rounded-lg text-sm font-medium"
        >
          {loading ? "Generating..." : "Generate Briefing"}
        </button>
      </div>

      <section>
        <h2 className="text-lg font-semibold mb-3 text-gray-300">Recent Findings</h2>
        {findings.length === 0 ? (
          <p className="text-gray-500 text-sm">No findings yet. Run a research task to get started.</p>
        ) : (
          <ul className="space-y-3">
            {findings.map((f) => (
              <li key={f.id} className="bg-gray-900 border border-gray-800 rounded-lg p-4">
                <p className="font-medium text-sm">{f.title}</p>
                <p className="text-gray-400 text-xs mt-1">{f.summary}</p>
                <div className="flex gap-2 mt-2">
                  {f.tags?.map((t: string) => (
                    <span key={t} className="text-xs bg-gray-800 text-gray-300 px-2 py-0.5 rounded">{t}</span>
                  ))}
                </div>
              </li>
            ))}
          </ul>
        )}
      </section>

      <section>
        <h2 className="text-lg font-semibold mb-3 text-gray-300">Recent Briefings</h2>
        {briefings.length === 0 ? (
          <p className="text-gray-500 text-sm">No briefings yet.</p>
        ) : (
          <ul className="space-y-3">
            {briefings.map((b) => (
              <li key={b.id} className="bg-gray-900 border border-gray-800 rounded-lg p-4 flex items-center justify-between">
                <span className="text-sm font-medium">{b.title}</span>
                <span className={`text-xs px-2 py-0.5 rounded ${b.sent_to_slack ? "bg-green-900 text-green-300" : "bg-gray-800 text-gray-400"}`}>
                  {b.sent_to_slack ? "Sent to Slack" : "Not sent"}
                </span>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}
