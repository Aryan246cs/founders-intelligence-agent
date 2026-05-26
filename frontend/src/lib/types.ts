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
