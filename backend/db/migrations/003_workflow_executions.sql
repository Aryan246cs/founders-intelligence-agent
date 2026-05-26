-- Additive migration: workflow-level execution tracking
-- Provides a single record per workflow run for external orchestrators (n8n, etc.)
-- Existing tables are untouched.

create table if not exists workflow_executions (
    id uuid primary key default gen_random_uuid(),
    trigger_source text not null default 'api',   -- 'api' | 'n8n' | 'scheduler' | 'manual'
    request_summary text,                          -- human-readable description of what was requested
    status text not null default 'running',        -- 'running' | 'completed' | 'failed'
    steps_total integer not null default 0,
    steps_completed integer not null default 0,
    plan_summary text,
    briefing_id uuid references briefings(id) on delete set null,
    briefing_available boolean not null default false,
    slack_delivered boolean not null default false,
    comparison_ran boolean not null default false,
    has_competitor_changes boolean not null default false,
    error text,
    started_at timestamptz not null default now(),
    completed_at timestamptz,
    duration_ms integer                            -- wall-clock ms from started_at to completed_at
);

create index if not exists idx_workflow_executions_status
    on workflow_executions(status);

create index if not exists idx_workflow_executions_started
    on workflow_executions(started_at desc);
