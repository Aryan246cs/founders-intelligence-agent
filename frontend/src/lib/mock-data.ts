import type {
  Agent,
  Briefing,
  WorkflowExecution,
  MemoryComparison,
  ActivityEvent,
  MemorySnapshot,
} from "./types";

export const mockAgents: Agent[] = [
  {
    id: "agent-1",
    name: "Web Monitoring Agent",
    type: "research",
    status: "active",
    lastExecution: "2 min ago",
    uptime: "99.8%",
    executionCount: 1247,
    description: "Continuously monitors competitor websites and news sources via Apify",
    icon: "Globe",
  },
  {
    id: "agent-2",
    name: "Competitor Intelligence Agent",
    type: "competitor_monitor",
    status: "running",
    lastExecution: "Just now",
    uptime: "99.2%",
    executionCount: 843,
    description: "Scrapes and analyzes competitor positioning, pricing, and product updates",
    icon: "Crosshair",
  },
  {
    id: "agent-3",
    name: "Memory Comparison Agent",
    type: "memory",
    status: "active",
    lastExecution: "8 min ago",
    uptime: "100%",
    executionCount: 2104,
    description: "Compares new findings against historical snapshots to detect meaningful signals",
    icon: "Brain",
  },
  {
    id: "agent-4",
    name: "Strategic Insight Agent",
    type: "planner",
    status: "idle",
    lastExecution: "14 min ago",
    uptime: "98.7%",
    executionCount: 412,
    description: "Synthesizes intelligence into actionable founder briefings using Groq LLM",
    icon: "Lightbulb",
  },
  {
    id: "agent-5",
    name: "Slack Delivery Agent",
    type: "briefing",
    status: "active",
    lastExecution: "14 min ago",
    uptime: "99.9%",
    executionCount: 389,
    description: "Formats and delivers executive briefings to configured Slack channels",
    icon: "Send",
  },
];

export const mockBriefings: Briefing[] = [
  {
    id: "brief-1",
    title: "Enterprise AI Competition Shifts Toward Security-First Positioning",
    generatedAt: "2026-05-26T14:30:00Z",
    priority: "critical",
    sentToSlack: true,
    sourceCount: 23,
    companiesMentioned: ["OpenAI", "Anthropic", "Google DeepMind", "Mistral"],
    keyChanges: [
      "OpenAI updated GPT-5.5 API pricing — 40% reduction for enterprise tiers",
      "Anthropic expanded Claude Enterprise with SOC 2 Type II compliance",
      "Google DeepMind launched Gemini Ultra for enterprise agents",
      "Mistral released Codestral 2.0 with 256k context window",
    ],
    strategicInsight:
      "Enterprise AI competition is rapidly shifting toward security-first positioning and compliance certifications. Founders building on top of these models should prioritize SOC 2 compliance as a competitive differentiator. The pricing war signals commoditization of base models — value is moving to orchestration and vertical applications.",
    riskLevel: "high",
    opportunitySignals: [
      "Enterprise compliance tooling gap — no dominant player yet",
      "Model orchestration layer still fragmented",
      "Vertical AI agents for regulated industries underserved",
    ],
    aiConfidence: 94,
  },
  {
    id: "brief-2",
    title: "Funding Surge in Autonomous Agent Infrastructure",
    generatedAt: "2026-05-25T09:15:00Z",
    priority: "high",
    sentToSlack: true,
    sourceCount: 18,
    companiesMentioned: ["Cognition", "Devin", "Cohere", "Together AI"],
    keyChanges: [
      "Cognition raised $175M Series B at $2B valuation",
      "Together AI launched dedicated inference clusters for agent workloads",
      "Cohere released Command R+ with 128k context for enterprise RAG",
    ],
    strategicInsight:
      "Autonomous agent infrastructure is attracting significant capital. The market is bifurcating between general-purpose agents and domain-specific operators. Infrastructure plays (inference, orchestration, memory) are commanding premium valuations.",
    riskLevel: "medium",
    opportunitySignals: [
      "Domain-specific agent operators still early",
      "Memory and state management for agents unsolved",
      "Agent evaluation and monitoring tooling nascent",
    ],
    aiConfidence: 89,
  },
  {
    id: "brief-3",
    title: "OpenAI Platform Strategy Signals Developer Ecosystem Expansion",
    generatedAt: "2026-05-24T16:45:00Z",
    priority: "high",
    sentToSlack: false,
    sourceCount: 14,
    companiesMentioned: ["OpenAI", "Microsoft", "GitHub"],
    keyChanges: [
      "OpenAI launched Assistants API v3 with persistent memory",
      "Microsoft Copilot Studio integrated GPT-5 for enterprise workflows",
      "GitHub Copilot added multi-file agent editing capabilities",
    ],
    strategicInsight:
      "OpenAI is aggressively expanding its developer platform to capture the application layer. The Assistants API v3 with persistent memory directly competes with custom memory solutions. Founders building memory-augmented AI products should accelerate differentiation.",
    riskLevel: "high",
    opportunitySignals: [
      "OpenAI memory is generic — vertical-specific memory still open",
      "Enterprise customization and fine-tuning demand growing",
    ],
    aiConfidence: 91,
  },
  {
    id: "brief-4",
    title: "Anthropic Constitutional AI Gains Enterprise Traction",
    generatedAt: "2026-05-23T11:20:00Z",
    priority: "medium",
    sentToSlack: true,
    sourceCount: 11,
    companiesMentioned: ["Anthropic", "Salesforce", "Accenture"],
    keyChanges: [
      "Anthropic signed enterprise agreements with Salesforce and Accenture",
      "Claude 3.5 Sonnet benchmarks exceed GPT-4o on reasoning tasks",
      "Anthropic published Constitutional AI 2.0 research paper",
    ],
    strategicInsight:
      "Anthropic's safety-first positioning is resonating with risk-averse enterprise buyers. The Salesforce and Accenture partnerships signal mainstream enterprise adoption. Constitutional AI as a differentiator is gaining credibility.",
    riskLevel: "low",
    opportunitySignals: [
      "Safety-certified AI for regulated industries (healthcare, finance, legal)",
      "Constitutional AI fine-tuning services",
    ],
    aiConfidence: 87,
  },
];

export const mockExecutions: WorkflowExecution[] = [
  {
    id: "exec-1",
    executionId: "wf_01HXYZ123ABC",
    status: "completed",
    triggerSource: "n8n",
    requestSummary: "Monitor OpenAI, Anthropic, Google DeepMind and generate founder briefing",
    planSummary: "Research 3 competitors → Memory comparison → Strategic briefing → Slack delivery",
    stepsTotal: 5,
    stepsCompleted: 5,
    briefingAvailable: true,
    slackDelivered: true,
    comparisonRan: true,
    hasCompetitorChanges: true,
    startedAt: "2026-05-26T14:28:00Z",
    completedAt: "2026-05-26T14:30:22Z",
    durationMs: 142000,
    steps: [
      { agentType: "research", status: "completed", durationMs: 28000, output: "23 findings saved" },
      { agentType: "competitor_monitor", status: "completed", durationMs: 45000, output: "3 competitors analyzed" },
      { agentType: "memory", status: "completed", durationMs: 8000, output: "4 changes detected" },
      { agentType: "briefing", status: "completed", durationMs: 52000, output: "Briefing generated" },
      { agentType: "slack", status: "completed", durationMs: 9000, output: "Delivered to #intelligence" },
    ],
  },
  {
    id: "exec-2",
    executionId: "wf_01HXYZ456DEF",
    status: "completed",
    triggerSource: "scheduler",
    requestSummary: "Daily competitive intelligence sweep — all monitored competitors",
    planSummary: "Full competitor sweep → Memory diff → Briefing",
    stepsTotal: 4,
    stepsCompleted: 4,
    briefingAvailable: true,
    slackDelivered: true,
    comparisonRan: true,
    hasCompetitorChanges: false,
    startedAt: "2026-05-25T09:00:00Z",
    completedAt: "2026-05-25T09:02:18Z",
    durationMs: 138000,
    steps: [
      { agentType: "research", status: "completed", durationMs: 31000, output: "18 findings saved" },
      { agentType: "competitor_monitor", status: "completed", durationMs: 52000, output: "4 competitors analyzed" },
      { agentType: "memory", status: "completed", durationMs: 6000, output: "No significant changes" },
      { agentType: "briefing", status: "completed", durationMs: 49000, output: "Briefing generated" },
    ],
  },
  {
    id: "exec-3",
    executionId: "wf_01HXYZ789GHI",
    status: "failed",
    triggerSource: "api",
    requestSummary: "Monitor Mistral AI and generate pricing intelligence report",
    planSummary: "Research Mistral → Competitor analysis → Briefing",
    stepsTotal: 3,
    stepsCompleted: 1,
    briefingAvailable: false,
    slackDelivered: false,
    comparisonRan: false,
    hasCompetitorChanges: false,
    startedAt: "2026-05-24T16:40:00Z",
    completedAt: "2026-05-24T16:41:05Z",
    durationMs: 65000,
    error: "Apify scrape timeout — Mistral website returned 429 rate limit",
    steps: [
      { agentType: "research", status: "completed", durationMs: 28000, output: "6 findings saved" },
      { agentType: "competitor_monitor", status: "failed", durationMs: 37000, output: "Rate limit exceeded" },
    ],
  },
  {
    id: "exec-4",
    executionId: "wf_01HXYZ012JKL",
    status: "completed",
    triggerSource: "n8n",
    requestSummary: "Weekly strategic briefing — full market sweep",
    planSummary: "Market research → 5 competitor analyses → Memory comparison → Executive briefing",
    stepsTotal: 7,
    stepsCompleted: 7,
    briefingAvailable: true,
    slackDelivered: true,
    comparisonRan: true,
    hasCompetitorChanges: true,
    startedAt: "2026-05-23T11:15:00Z",
    completedAt: "2026-05-23T11:18:44Z",
    durationMs: 224000,
    steps: [
      { agentType: "research", status: "completed", durationMs: 35000, output: "31 findings saved" },
      { agentType: "competitor_monitor", status: "completed", durationMs: 89000, output: "5 competitors analyzed" },
      { agentType: "memory", status: "completed", durationMs: 12000, output: "7 changes detected" },
      { agentType: "briefing", status: "completed", durationMs: 61000, output: "Briefing generated" },
      { agentType: "slack", status: "completed", durationMs: 8000, output: "Delivered to #founders" },
    ],
  },
];

const makeSnapshot = (
  id: string,
  competitor: string,
  capturedAt: string,
  summary: string,
  keyPoints: string[]
): MemorySnapshot => ({ id, competitor, capturedAt, summary, keyPoints, tags: ["competitor", competitor.toLowerCase()] });

export const mockMemoryComparisons: MemoryComparison[] = [
  {
    id: "mem-1",
    competitor: "OpenAI",
    previousSnapshot: makeSnapshot(
      "snap-1a", "OpenAI", "2026-05-19T09:00:00Z",
      "OpenAI focused on GPT-4 enterprise APIs with stable pricing and developer tooling.",
      ["GPT-4 flagship model", "Stable API pricing", "Developer-focused positioning", "ChatGPT Plus at $20/mo"]
    ),
    currentSnapshot: makeSnapshot(
      "snap-1b", "OpenAI", "2026-05-26T14:30:00Z",
      "OpenAI launched GPT-5.5 with aggressive enterprise pricing changes targeting large-scale adoption and introduced Assistants API v3 with persistent memory.",
      ["GPT-5.5 launched", "40% enterprise pricing reduction", "Assistants API v3 with memory", "SOC 2 Type II certified", "Microsoft deep integration"]
    ),
    hasChanges: true,
    changes: [
      { type: "pricing", summary: "GPT-5.5 API pricing introduced — 40% reduction for enterprise tiers", isAddition: true, isRemoval: false },
      { type: "product_launch", summary: "Assistants API v3 with persistent memory launched", isAddition: true, isRemoval: false },
      { type: "enterprise", summary: "SOC 2 Type II certification achieved", isAddition: true, isRemoval: false },
    ],
    deltaSummary: "OpenAI — 3 new developments detected across pricing, product, and enterprise compliance",
    detectedSignal: "Enterprise monetization strategy accelerating — pricing pressure and compliance investment signal aggressive enterprise land-grab.",
    comparedAt: "2026-05-26T14:31:00Z",
  },
  {
    id: "mem-2",
    competitor: "Anthropic",
    previousSnapshot: makeSnapshot(
      "snap-2a", "Anthropic", "2026-05-19T09:00:00Z",
      "Anthropic focused on safety research and Claude 3 model family with limited enterprise partnerships.",
      ["Claude 3 model family", "Safety-first positioning", "Limited enterprise reach", "Research-oriented brand"]
    ),
    currentSnapshot: makeSnapshot(
      "snap-2b", "Anthropic", "2026-05-26T14:30:00Z",
      "Anthropic expanded enterprise safety tooling with SOC 2 compliance, signed Salesforce and Accenture partnerships, and published Constitutional AI 2.0.",
      ["Claude 3.5 Sonnet outperforms GPT-4o", "Salesforce partnership signed", "Accenture enterprise deal", "SOC 2 Type II", "Constitutional AI 2.0 published"]
    ),
    hasChanges: true,
    changes: [
      { type: "partnership", summary: "Salesforce and Accenture enterprise partnerships signed", isAddition: true, isRemoval: false },
      { type: "model_release", summary: "Claude 3.5 Sonnet benchmarks exceed GPT-4o on reasoning", isAddition: true, isRemoval: false },
      { type: "enterprise", summary: "SOC 2 Type II compliance achieved — safety-first enterprise positioning", isAddition: true, isRemoval: false },
    ],
    deltaSummary: "Anthropic — 3 new developments detected across partnerships, model performance, and enterprise compliance",
    detectedSignal: "Anthropic transitioning from research lab to enterprise AI vendor — safety positioning becoming commercial differentiator.",
    comparedAt: "2026-05-26T14:31:00Z",
  },
  {
    id: "mem-3",
    competitor: "Google DeepMind",
    previousSnapshot: makeSnapshot(
      "snap-3a", "Google DeepMind", "2026-05-19T09:00:00Z",
      "Google DeepMind focused on Gemini model development and research publications.",
      ["Gemini Pro available", "Research-heavy positioning", "Google Cloud integration", "Limited agent tooling"]
    ),
    currentSnapshot: makeSnapshot(
      "snap-3b", "Google DeepMind", "2026-05-26T14:30:00Z",
      "Google DeepMind launched Gemini Ultra for enterprise agents with dedicated infrastructure and announced Project Astra for real-time multimodal agents.",
      ["Gemini Ultra for enterprise agents", "Project Astra announced", "Dedicated agent infrastructure", "Real-time multimodal capabilities", "Vertex AI deep integration"]
    ),
    hasChanges: true,
    changes: [
      { type: "product_launch", summary: "Gemini Ultra for enterprise agents launched with dedicated infrastructure", isAddition: true, isRemoval: false },
      { type: "product_launch", summary: "Project Astra — real-time multimodal agent platform announced", isAddition: true, isRemoval: false },
    ],
    deltaSummary: "Google DeepMind — 2 new developments detected in enterprise agent infrastructure",
    detectedSignal: "Google entering autonomous agent market with infrastructure-level investment — signals long-term platform play.",
    comparedAt: "2026-05-26T14:31:00Z",
  },
];

export const mockActivityFeed: ActivityEvent[] = [
  { id: "act-1", timestamp: "Just now", message: "Memory comparison completed — 3 changes detected for OpenAI", type: "success", agent: "Memory Agent" },
  { id: "act-2", timestamp: "2 min ago", message: "Slack briefing delivered to #intelligence channel", type: "success", agent: "Slack Agent" },
  { id: "act-3", timestamp: "3 min ago", message: "Strategic briefing generated — 94% confidence score", type: "info", agent: "Briefing Agent" },
  { id: "act-4", timestamp: "5 min ago", message: "GPT-5.5 enterprise pricing update detected", type: "warning", agent: "Competitor Agent" },
  { id: "act-5", timestamp: "8 min ago", message: "Anthropic SOC 2 compliance signal identified", type: "info", agent: "Memory Agent" },
  { id: "act-6", timestamp: "11 min ago", message: "Web scrape completed — 23 sources processed", type: "success", agent: "Research Agent" },
  { id: "act-7", timestamp: "14 min ago", message: "n8n workflow triggered — daily intelligence sweep", type: "info", agent: "Orchestrator" },
  { id: "act-8", timestamp: "22 min ago", message: "New strategic signal: Enterprise AI compliance gap identified", type: "warning", agent: "Planner Agent" },
  { id: "act-9", timestamp: "31 min ago", message: "Memory snapshot saved for Google DeepMind", type: "info", agent: "Memory Agent" },
  { id: "act-10", timestamp: "45 min ago", message: "Workflow execution completed in 2m 22s", type: "success", agent: "Orchestrator" },
];

export const kpiData = [
  { label: "Briefings Generated", value: "47", delta: "+3 today", deltaPositive: true, color: "brand" },
  { label: "Active Agents", value: "5", delta: "All healthy", deltaPositive: true, color: "emerald" },
  { label: "Memory Comparisons", value: "2,104", delta: "+12 today", deltaPositive: true, color: "purple" },
  { label: "Slack Deliveries", value: "38", delta: "+2 today", deltaPositive: true, color: "amber" },
  { label: "Executions Today", value: "6", delta: "1 failed", deltaPositive: false, color: "rose" },
  { label: "Sources Monitored", value: "142", delta: "+8 this week", deltaPositive: true, color: "violet" },
];

export const executionChartData = [
  { day: "Mon", completed: 4, failed: 0 },
  { day: "Tue", completed: 6, failed: 1 },
  { day: "Wed", completed: 5, failed: 0 },
  { day: "Thu", completed: 8, failed: 2 },
  { day: "Fri", completed: 7, failed: 0 },
  { day: "Sat", completed: 3, failed: 0 },
  { day: "Sun", completed: 6, failed: 1 },
];
