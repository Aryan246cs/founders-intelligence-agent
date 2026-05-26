-- Additive migration: competitor snapshot history
-- Preserves all existing tables and data.
-- Used by the historical memory comparison system.

create table if not exists competitor_snapshots (
    id uuid primary key default gen_random_uuid(),
    competitor_name text not null,
    summary text not null,
    key_points text[] default '{}',
    tags text[] default '{}',
    captured_at timestamptz default now()
);

-- Index for fast per-competitor lookups ordered by time
create index if not exists idx_competitor_snapshots_name_time
    on competitor_snapshots(competitor_name, captured_at desc);
