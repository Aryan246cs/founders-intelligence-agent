# Autonomous Founder Research & Competitive Intelligence Platform

An autonomous multi-agent platform for startup founders. Researches competitors, analyses markets, detects high-signal strategic changes, generates executive briefings, and delivers intelligence to Slack — all from a single prompt.

## Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI (Python 3.11+) |
| Frontend | Next.js 14, TypeScript, Tailwind CSS |
| Database | Supabase (PostgreSQL) |
| LLM | Groq API (llama3-70b-8192) |
| Scraping | Apify (Website Crawler + Google Search) |
| Orchestration | n8n |
| Notifications | Slack Webhooks |

---

## Features

### Startup Research (Flagship)
Enter a startup idea. The platform autonomously runs a 10-step research pipeline:

1. Parses the idea — extracts industry, keywords, ICP, business model
2. Builds India-first + global search queries
3. Searches Google via Apify for real competitors
4. Scrapes competitor homepages + pricing pages
5. Falls back to snippet analysis if scraping is blocked
6. Extracts pricing tiers, features, and positioning
7. Generates a strategic report via Groq (with retry logic)
8. Builds feature comparison matrix + pricing intelligence table
9. Saves to database + memory for future comparisons
10. Delivers a structured Slack summary (optional)

**Report sections:** Executive Summary · Competitor Landscape · Feature Comparison · Pricing Analysis · Positioning Analysis · Market Gaps · Differentiation Opportunities · SWOT · Founder Recommendations · Verified Sources

### Competitor Monitoring
Scheduled or manual workflows that scrape competitor websites, detect high-signal strategic changes (pricing, product launches, partnerships, funding), and generate executive briefings.

### Intelligence Briefings
Concise, topic-scoped briefings generated from live research findings. Deduplicated against recent briefings (>75% similarity suppressed). Delivered to Slack in executive block format.

### Memory System
Every competitor snapshot is stored and diffed against previous runs. Only meaningful strategic changes surface — generic noise is filtered by the comparison engine.

### Execution Tracking
Every workflow run — briefing generation or startup research — appears in the Executions page with a step-by-step timeline and duration.

---

## How the Briefing Pipeline Works

1. **Trigger** — user clicks "Generate Briefing", or n8n fires a scheduled workflow
2. **Plan** — PlannerAgent turns a natural-language request into an execution plan
3. **Monitor** — CompetitorMonitorAgent scrapes each competitor via Apify + Groq
4. **Compare** — MemoryAgent diffs new findings against historical snapshots
5. **Brief** — BriefingAgent generates a markdown briefing scoped to this run only
6. **Deliver** — Slack delivery sends Key Developments, Strategic Intelligence, Founder Takeaway

### Signal Quality Rules
- Generic entities ("AI", "chatbots", "safety") are never compared
- Findings shorter than 80 characters are filtered
- Filler patterns ("no significant changes", "remains committed to") are suppressed
- Briefings >75% similar to recent ones are deduplicated
- Signal gate only applies to automated runs — manual triggers always generate

---

## Project Structure

```
founders-agent/
├── backend/
│   ├── agents/
│   │   ├── base.py                     # Abstract agent — task tracking + logging
│   │   ├── orchestrator.py             # Runs sequential agent step lists
│   │   ├── planner_agent.py            # Natural language → execution plan
│   │   ├── competitor_monitor.py       # Scrapes + analyses competitor websites
│   │   ├── research_agent.py           # Google search via Apify + Groq analysis
│   │   ├── memory_agent.py             # Read/write/compare persistent memory
│   │   ├── briefing_agent.py           # Generates topic-scoped executive briefings
│   │   └── startup_research_agent.py   # Full 10-step startup research pipeline
│   ├── api/routes/
│   │   ├── agents.py                   # POST /run, GET /status, GET /{task_id}
│   │   ├── briefings.py                # POST /generate, GET /, GET /{id}
│   │   ├── workflows.py                # POST /run, GET /executions, GET /status/{id}
│   │   ├── memory.py                   # POST /set, GET /{ns}/{key}, POST /list
│   │   ├── memory_comparisons.py       # GET /comparisons, GET /stats
│   │   ├── dashboard.py                # GET /stats (KPIs + chart data)
│   │   ├── activity.py                 # GET /feed (live execution log stream)
│   │   ├── research.py                 # POST /search, POST /competitor, GET /findings
│   │   └── startup_research.py         # POST /run, GET /, GET /{id}, POST /{id}/slack
│   ├── services/
│   │   ├── comparison/
│   │   │   └── comparison_engine.py    # High-signal change detection (no LLM)
│   │   ├── memory/
│   │   │   └── retrieval.py            # Historical snapshot retrieval helpers
│   │   ├── groq_service.py             # Async Groq completions with retry
│   │   ├── apify_service.py            # Web scraping + Google search
│   │   ├── slack_service.py            # Executive-format Slack block delivery
│   │   └── n8n_service.py              # n8n webhook triggers
│   ├── db/
│   │   ├── client.py                   # Supabase client singleton
│   │   ├── queries.py                  # All DB query classes
│   │   └── migrations/                 # SQL migration files (run in order)
│   ├── models/                         # Pydantic request/response schemas
│   ├── utils/                          # Structured logging (structlog)
│   ├── config.py                       # Settings via pydantic-settings
│   ├── main.py                         # FastAPI app + CORS + rate limiting
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── page.tsx                # Dashboard (KPIs, agents, activity feed)
│   │   │   ├── briefings/              # Briefings list with search + filter
│   │   │   ├── executions/             # Workflow execution history + chart
│   │   │   ├── memory/                 # Memory comparison diffs
│   │   │   ├── startup-research/       # Startup Research page (flagship)
│   │   │   └── settings/
│   │   ├── components/
│   │   │   ├── dashboard/              # KpiCard, AgentStatusGrid, ActivityFeed,
│   │   │   │                           # GenerateBriefingModal, PipelineViz, etc.
│   │   │   ├── briefings/              # BriefingCard (expandable)
│   │   │   ├── executions/             # ExecutionCard with step timeline
│   │   │   ├── memory/                 # MemoryDiffCard (old vs new snapshot)
│   │   │   ├── startup-research/       # ResearchLauncher, ResearchReport,
│   │   │   │                           # ResearchHistory
│   │   │   └── layout/                 # Sidebar, Topbar
│   │   ├── hooks/
│   │   │   ├── usePolling.ts
│   │   │   ├── useDashboard.ts
│   │   │   ├── useBriefings.ts
│   │   │   ├── useExecutions.ts
│   │   │   ├── useAgents.ts
│   │   │   ├── useMemory.ts
│   │   │   └── useStartupResearch.ts   # Research history with polling
│   │   ├── services/
│   │   │   ├── api.ts                  # Base fetch client with retry
│   │   │   ├── briefings.ts
│   │   │   ├── executions.ts
│   │   │   ├── agents.ts
│   │   │   ├── memory.ts
│   │   │   ├── dashboard.ts
│   │   │   └── startupResearch.ts      # Research API service
│   │   └── lib/
│   │       ├── types.ts                # Shared TypeScript interfaces
│   │       ├── mock-data.ts            # Fallback data (shown when backend is down)
│   │       └── utils.ts
│   ├── .env                            # NEXT_PUBLIC_API_URL=http://localhost:8000
│   └── package.json
└── n8n/
    ├── daily_briefing_workflow.json         # Runs every 24h → POST /api/briefings/generate
    └── competitor_monitor_workflow.json     # Runs every 12h → POST /api/workflows/orchestrate
```

---

## Database Schema

Run migrations in order from `backend/db/migrations/`:

| Migration | Table | Purpose |
|---|---|---|
| `001_initial_schema.sql` | `agent_tasks` | Every agent execution — status, input, result, error |
| `001_initial_schema.sql` | `research_findings` | Scraped + analysed findings with tags and source URLs |
| `001_initial_schema.sql` | `briefings` | Generated briefings with raw markdown |
| `001_initial_schema.sql` | `memory_entries` | Key-value persistent memory (namespace + key) |
| `001_initial_schema.sql` | `execution_logs` | Structured agent logs (powers the live activity feed) |
| `002_competitor_snapshots.sql` | `competitor_snapshots` | Historical competitor snapshots for diff comparison |
| `003_workflow_executions.sql` | `workflow_executions` | End-to-end workflow run records |
| `004_startup_research.sql` | `startup_research_reports` | Full startup research reports (all 10 sections as JSONB) |

---

## Setup

### Prerequisites

- Python 3.11+
- Node.js 18+
- Supabase project (free tier works)
- Groq API key — [console.groq.com](https://console.groq.com)
- Apify API token — [apify.com](https://apify.com)
- Slack webhook URL (optional)
- n8n instance (optional, for scheduled runs)

### 1. Database

Run all four SQL files in `backend/db/migrations/` against your Supabase project via the SQL editor, in order:

```
001_initial_schema.sql
002_competitor_snapshots.sql
003_workflow_executions.sql
004_startup_research.sql
```

If you get RLS errors on insert, run this in the SQL editor:

```sql
alter table startup_research_reports disable row level security;
```

### 2. Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your keys
uvicorn main:app --reload
```

Backend runs at `http://localhost:8000`. Swagger UI at `http://localhost:8000/docs`.

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at `http://localhost:3000`.

### 4. n8n (optional)

Import the JSONs from `n8n/` into your n8n instance. Update the webhook URLs to point at your backend.

---

## Environment Variables

### Backend (`backend/.env`)

```env
APP_ENV=development
APP_SECRET_KEY=your-secret-key

SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key

GROQ_API_KEY=your-groq-api-key
GROQ_MODEL=llama3-70b-8192

APIFY_API_TOKEN=your-apify-token

SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...

N8N_WEBHOOK_BASE_URL=http://localhost:5678/webhook
RATE_LIMIT_PER_MINUTE=60
```

### Frontend (`frontend/.env`)

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## Key API Endpoints

```
# Startup Research (flagship)
POST /api/startup-research/run          Launch full autonomous research pipeline
GET  /api/startup-research/             List research history
GET  /api/startup-research/{id}         Fetch a full report
POST /api/startup-research/{id}/slack   Send a saved report to Slack

# Briefing Workflows
POST /api/workflows/run                 Trigger a full autonomous briefing workflow
GET  /api/workflows/executions          List recent workflow runs
GET  /api/workflows/status/{id}         Poll a running workflow

# Briefings
GET  /api/briefings/                    List briefings (enriched for frontend)
POST /api/briefings/generate            Queue a briefing generation

# Platform
GET  /api/agents/status                 Live agent health
GET  /api/dashboard/stats               KPI aggregates + 7-day chart data
GET  /api/activity/feed                 Live execution log stream
GET  /api/memory/comparisons            Competitor snapshot diffs
GET  /api/memory/stats                  Memory system statistics
```

---

## Running Tests

```bash
cd backend
source venv/bin/activate
python -m pytest tests/ -v
```
