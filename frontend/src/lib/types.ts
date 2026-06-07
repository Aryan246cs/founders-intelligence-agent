export type AgentStatus = "active" | "idle" | "running" | "error";
export type Priority = "critical" | "high" | "medium" | "low";
export type ExecutionStatus = "completed" | "running" | "failed";

export interface KpiMetric {
  label: string;
  value: string | number;
  delta?: string;
  deltaPositive?: boolean;
  icon: string;
  color: string;
}

export interface Agent {
  id: string;
  name: string;
  type: string;
  status: AgentStatus;
  lastExecution: string;
  uptime: string;
  executionCount: number;
  description: string;
  icon: string;
}

export interface Briefing {
  id: string;
  title: string;
  generatedAt: string;
  priority: Priority;
  sentToSlack: boolean;
  sourceCount: number;
  companiesMentioned: string[];
  keyChanges: string[];
  strategicInsight: string;
  riskLevel: Priority;
  opportunitySignals: string[];
  aiConfidence: number;
  rawMarkdown?: string;
}

export interface WorkflowExecution {
  id: string;
  executionId: string;
  status: ExecutionStatus;
  triggerSource: string;
  requestSummary: string;
  planSummary: string;
  stepsTotal: number;
  stepsCompleted: number;
  briefingAvailable: boolean;
  slackDelivered: boolean;
  comparisonRan: boolean;
  hasCompetitorChanges: boolean;
  startedAt: string;
  completedAt: string;
  durationMs: number;
  error?: string;
  steps?: ExecutionStep[];
}

export interface ExecutionStep {
  agentType: string;
  status: ExecutionStatus;
  durationMs: number;
  output?: string;
}

export interface MemorySnapshot {
  id: string;
  competitor: string;
  capturedAt: string;
  summary: string;
  keyPoints: string[];
  tags: string[];
}

export interface MemoryComparison {
  id: string;
  competitor: string;
  previousSnapshot: MemorySnapshot;
  currentSnapshot: MemorySnapshot;
  hasChanges: boolean;
  changes: MemoryChange[];
  deltaSummary: string;
  detectedSignal: string;
  comparedAt: string;
}

export interface MemoryChange {
  type: string;
  summary: string;
  isAddition: boolean;
  isRemoval: boolean;
}

export interface ActivityEvent {
  id: string;
  timestamp: string;
  message: string;
  type: "info" | "success" | "warning" | "error";
  agent?: string;
}

// ---------------------------------------------------------------------------
// Startup Research
// ---------------------------------------------------------------------------

export interface ResearchCompetitor {
  name: string;
  website: string;
  domain?: string;
  description: string;
  business_focus: string;
  target_audience: string;
  market_positioning: string;
  key_features: string[];
  pricing_model: string;
  pricing_tiers: PricingTier[];
  strengths: string[];
  source_url: string;
}

export interface PricingTier {
  tier: string;
  price: string;
  features: string[];
}

export interface FeatureComparisonRow {
  feature: string;
  your_idea: string;
  [competitor: string]: string;
}

export interface PricingTableRow {
  competitor: string;
  model: string;
  tiers: PricingTier[];
}

export interface SwotAnalysis {
  strengths: string[];
  weaknesses: string[];
  opportunities: string[];
  threats: string[];
}

export interface ResearchSource {
  name: string;
  url: string;
  type: string;
}

export interface StartupResearchReport {
  id: string;
  startup_name?: string;
  startup_idea: string;
  industry: string;
  keywords: string[];
  icp: string;
  business_model: string;
  executive_summary: string;
  competitors: ResearchCompetitor[];
  feature_comparison: FeatureComparisonRow[];
  pricing_analysis: PricingTableRow[];
  positioning_analysis: string;
  market_gaps: string[];
  differentiation: string[];
  swot: SwotAnalysis;
  founder_recommendations: string[];
  sources: ResearchSource[];
  competitors_found: number;
  sources_analyzed: number;
  research_score: number;
  sent_to_slack: boolean;
  created_at: string;
}

export interface StartupResearchListItem {
  id: string;
  startup_name?: string;
  startup_idea: string;
  industry: string;
  competitors_found: number;
  sources_analyzed: number;
  research_score: number;
  sent_to_slack: boolean;
  created_at: string;
}
