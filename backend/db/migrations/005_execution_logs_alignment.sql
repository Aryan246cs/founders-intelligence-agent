-- Align execution_logs with what the application actually writes.
--
-- Background: the deployed table had only (id, task_id, log, created_at) while
-- the code writes structured fields (agent_type, level, message, metadata).
-- Every insert failed with PGRST204 and was swallowed by the logger's
-- exception guard, so the live activity feed was permanently empty.
--
-- Fully additive and idempotent — safe to run on an existing database and safe
-- to re-run. No column is dropped, so any legacy `log` data is preserved.

alter table execution_logs add column if not exists agent_type text;
alter table execution_logs add column if not exists level      text default 'info';
alter table execution_logs add column if not exists message    text;
alter table execution_logs add column if not exists metadata   jsonb default '{}';
alter table execution_logs add column if not exists logged_at  timestamptz default now();

-- The feed reads newest-first and is the hottest query on this table.
create index if not exists idx_execution_logs_logged_at
    on execution_logs(logged_at desc);

create index if not exists idx_execution_logs_agent_type
    on execution_logs(agent_type);
