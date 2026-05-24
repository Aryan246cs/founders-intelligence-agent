"use client";

import { useEffect, useState } from "react";
import ReactMarkdown from "react-markdown";
import { getBriefings } from "@/lib/api";

export default function BriefingsPage() {
  const [briefings, setBriefings] = useState<any[]>([]);
  const [selected, setSelected] = useState<any | null>(null);

  useEffect(() => {
    getBriefings(10).then((r) => setBriefings(r.data.briefings ?? []));
  }, []);

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Briefings</h1>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <ul className="space-y-2 col-span-1">
          {briefings.map((b) => (
            <li
              key={b.id}
              onClick={() => setSelected(b)}
              className={`cursor-pointer bg-gray-900 border rounded-lg p-3 text-sm hover:border-brand-500 transition-colors ${selected?.id === b.id ? "border-brand-500" : "border-gray-800"}`}
            >
              <p className="font-medium">{b.title}</p>
              <p className="text-gray-500 text-xs mt-1">{new Date(b.generated_at).toLocaleDateString()}</p>
            </li>
          ))}
        </ul>

        <div className="col-span-2 bg-gray-900 border border-gray-800 rounded-lg p-6">
          {selected ? (
            <article className="prose prose-invert prose-sm max-w-none">
              <ReactMarkdown>{selected.raw_markdown}</ReactMarkdown>
            </article>
          ) : (
            <p className="text-gray-500 text-sm">Select a briefing to read it.</p>
          )}
        </div>
      </div>
    </div>
  );
}
