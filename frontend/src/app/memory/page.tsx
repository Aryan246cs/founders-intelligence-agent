"use client";

import { useState } from "react";
import { setMemory, getMemory } from "@/lib/api";

export default function MemoryPage() {
  const [form, setForm] = useState({ key: "", value: "", namespace: "default" });
  const [lookup, setLookup] = useState({ key: "", namespace: "default" });
  const [result, setResult] = useState<any>(null);
  const [status, setStatus] = useState("");

  const handleSet = async () => {
    if (!form.key || !form.value) return;
    let parsed: unknown = form.value;
    try { parsed = JSON.parse(form.value); } catch {}
    await setMemory(form.key, parsed, form.namespace);
    setStatus(`Saved: ${form.namespace}/${form.key}`);
  };

  const handleGet = async () => {
    if (!lookup.key) return;
    const res = await getMemory(lookup.namespace, lookup.key);
    setResult(res.data);
  };

  return (
    <div className="space-y-8">
      <h1 className="text-2xl font-bold">Memory</h1>
      {status && <p className="text-sm text-brand-500">{status}</p>}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-gray-900 border border-gray-800 rounded-lg p-5 space-y-3">
          <h2 className="font-semibold">Set Memory</h2>
          <input className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-sm" placeholder="Namespace" value={form.namespace} onChange={(e) => setForm({ ...form, namespace: e.target.value })} />
          <input className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-sm" placeholder="Key" value={form.key} onChange={(e) => setForm({ ...form, key: e.target.value })} />
          <textarea className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-sm" rows={3} placeholder='Value (string or JSON)' value={form.value} onChange={(e) => setForm({ ...form, value: e.target.value })} />
          <button onClick={handleSet} className="bg-brand-500 text-white px-4 py-2 rounded text-sm">Save</button>
        </div>

        <div className="bg-gray-900 border border-gray-800 rounded-lg p-5 space-y-3">
          <h2 className="font-semibold">Get Memory</h2>
          <input className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-sm" placeholder="Namespace" value={lookup.namespace} onChange={(e) => setLookup({ ...lookup, namespace: e.target.value })} />
          <input className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-sm" placeholder="Key" value={lookup.key} onChange={(e) => setLookup({ ...lookup, key: e.target.value })} />
          <button onClick={handleGet} className="bg-brand-500 text-white px-4 py-2 rounded text-sm">Lookup</button>
          {result && (
            <pre className="bg-gray-800 rounded p-3 text-xs overflow-auto">{JSON.stringify(result, null, 2)}</pre>
          )}
        </div>
      </div>
    </div>
  );
}
