import axios from "axios";

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000",
  headers: { "Content-Type": "application/json" },
});

// Agents
export const runAgent = (agentType: string, input: Record<string, unknown>) =>
  api.post("/api/agents/run", { agent_type: agentType, input });

export const getTask = (taskId: string) =>
  api.get(`/api/agents/${taskId}`);

// Research
export const runResearch = (query: string, maxResults = 10) =>
  api.post("/api/research/search", { query, max_results: maxResults });

export const monitorCompetitor = (name: string, website: string) =>
  api.post(`/api/research/competitor?competitor_name=${encodeURIComponent(name)}&website=${encodeURIComponent(website)}`);

export const getFindings = (limit = 20) =>
  api.get(`/api/research/findings?limit=${limit}`);

// Briefings
export const generateBriefing = (timeRangeDays = 7) =>
  api.post("/api/briefings/generate", { time_range_days: timeRangeDays });

export const getBriefings = (limit = 10) =>
  api.get(`/api/briefings/?limit=${limit}`);

// Memory
export const setMemory = (key: string, value: unknown, namespace = "default") =>
  api.post("/api/memory/set", { key, value, namespace });

export const getMemory = (namespace: string, key: string) =>
  api.get(`/api/memory/${namespace}/${key}`);

export default api;
