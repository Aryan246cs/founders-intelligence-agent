-- Startup Research Reports
-- Stores the full autonomous research output for a startup idea

create table if not exists startup_research_reports (
    id uuid primary key default gen_random_uuid(),
    startup_name text,
    startup_idea text not null,
    industry text,
    keywords text[] default '{}',
    icp text,
    business_model text,

    -- Report sections stored as JSONB
    executive_summary text,
    competitors jsonb default '[]',       -- array of competitor objects
    feature_comparison jsonb default '[]', -- feature matrix rows
    pricing_analysis jsonb default '[]',   -- competitor pricing tiers
    positioning_analysis text,
    market_gaps jsonb default '[]',        -- array of gap strings
    differentiation jsonb default '[]',    -- array of opportunity strings
    swot jsonb default '{}',              -- {strengths, weaknesses, opportunities, threats}
    founder_recommendations jsonb default '[]',
    sources jsonb default '[]',           -- [{name, url, type}]

    -- Meta
    competitors_found integer default 0,
    sources_analyzed integer default 0,
    research_score integer default 0,     -- 0-100
    execution_id uuid,                    -- link to workflow_executions if applicable
    sent_to_slack boolean default false,
    created_at timestamptz default now()
);

create index if not exists idx_startup_research_created on startup_research_reports(created_at desc);
create index if not exists idx_startup_research_idea on startup_research_reports using gin(to_tsvector('english', startup_idea));
