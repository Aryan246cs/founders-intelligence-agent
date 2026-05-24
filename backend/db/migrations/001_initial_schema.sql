-- Agent tasks
create table if not exists agent_tasks (
    id uuid primary key default gen_random_uuid(),
    agent_type text not null,
    input jsonb not null default '{}',
    status text not null default 'idle',
    result jsonb,
    error text,
    created_at timestamptz default now(),
    completed_at timestamptz
);

-- Competitor profiles
create table if not exists competitor_profiles (
    id uuid primary key default gen_random_uuid(),
    name text not null unique,
    website text not null,
    description text,
    funding_stage text,
    last_scraped_at timestamptz,
    raw_data jsonb,
    created_at timestamptz default now()
);

-- Research findings
create table if not exists research_findings (
    id uuid primary key default gen_random_uuid(),
    competitor_id uuid references competitor_profiles(id) on delete set null,
    source_url text not null,
    title text not null,
    summary text not null,
    sentiment text,
    tags text[] default '{}',
    found_at timestamptz default now()
);

-- Briefings
create table if not exists briefings (
    id uuid primary key default gen_random_uuid(),
    title text not null,
    sections jsonb not null default '[]',
    raw_markdown text not null,
    generated_at timestamptz default now(),
    sent_to_slack boolean default false
);

-- Persistent memory
create table if not exists memory_entries (
    id uuid primary key default gen_random_uuid(),
    key text not null,
    namespace text not null default 'default',
    value jsonb not null,
    tags text[] default '{}',
    created_at timestamptz default now(),
    updated_at timestamptz default now(),
    unique(key, namespace)
);

-- Execution logs
create table if not exists execution_logs (
    id uuid primary key default gen_random_uuid(),
    task_id uuid,
    agent_type text,
    level text not null default 'info',
    message text not null,
    metadata jsonb,
    logged_at timestamptz default now()
);

-- Indexes
create index if not exists idx_agent_tasks_status on agent_tasks(status);
create index if not exists idx_research_findings_competitor on research_findings(competitor_id);
create index if not exists idx_memory_entries_namespace on memory_entries(namespace);
create index if not exists idx_execution_logs_task on execution_logs(task_id);
