# Founder Intelligence Agent

An autonomous competitive intelligence platform for startup founders. Monitors competitor websites, stores persistent memory, detects high-signal strategic changes, and generates executive-grade briefings — delivered to Slack.

## Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI (Python 3.11+) |
| Frontend | Next.js 14, TypeScript, Tailwind CSS |
| Database | Supabase (PostgreSQL) |
| LLM | Groq API (llama3-70b-8192) |
| Scraping | Apify |
| Orchestration | n8n |
| Notifications | Slack Webhooks |

## How It Works

1. **Trigger** — user clicks "Generate Briefing" in the UI, or n8n fires a scheduled workflow
2. **Plan** — PlannerAgent uses Groq to turn a natural-language request into an execution plan (e.g. monitor Zomato + Swiggy → generate briefing)
3. **Monitor** — CompetitorMonitorAgent scrapes each competitor's website via Apify and extracts structured intelligence with Groq
4. **Compare** — MemoryAgent compares new findings against historical snapshots, detecting only high-signal strategic changes (pricing, product launches, enterprise moves, partnerships, funding)
5. **Brief** — BriefingAgent generates a concise, topic-scoped briefing using only findings from the current run — no cross-contamination from previous runs
6. **Deliver** — Slack delivery sends a formatted executive summary (Key Developments, Strategic Intelligence, Founder Takeaway)

### Signal Quality Rules

The system suppresses low-value output:
- Generic entities ("AI", "chatbots", "safety", "transparency") are never compared
- Findings shorter than 80 characters are filtered out
- Filler patterns ("no significant changes", "remains committed to") are suppressed
- Briefings too similar to recent ones (>75% similarity) are deduplicated
- The signal gate only blocks **scheduled/automated** runs — manual triggers always generate

## Project Structure

```
founders-agent/
├── backend/
│   ├── agents/
│   │   ├── base.py                  # Abstract agent with task tracking + logging
│   │   ├── orchestrator.py          # Runs sequential agent step lists
│   │   ├── planner_agent.py         # Turns natural language → execution plan
│   │   ├── competitor_monitor.py    # Scrapes + analyzes competitor websites
│   │   ├── research_agent.py        # Google search via Apify + Groq analysis
│   │   ├── memory_agent.py          # Read/write/compare persistent memory
│   │   └── briefing_agent.py        # Generates topic-scoped executive briefings
│   ├── api/routes/
│   │   ├── agents.py                # POST /run, GET /status, GET /{task_id}
│   │   ├── briefings.py             # POST /generate, GET /, GET /{id}
│   │   ├── workflows.py             # POST /run, GET /executions, GET /status/{id}
│   │   ├── memory.py                # POST /set, GET /{ns}/{key}, POST /list
│   │   ├── memory_comparisons.py    # GET /comparisons, GET /stats
│   │   ├── dashboard.py             # GET /stats (KPIs + chart data)
│   │   ├── activity.py              # GET /feed (live execution log stream)
│   │   └── research.py              # POST /search, POST /competitor, GET /findings
│   ├── services/
│   │   ├── comparison/
│   │   │   └── comparison_engine.py # High-signal change detection (no LLM)
│   │   ├── memory/
│   │   │   └── retrieval.py         # Historical snapshot retrieval helpers
│   │   ├── groq_service.py          # Async Groq completions with retry
│   │   ├── apify_service.py         # Web scraping + Google search
│   │   ├── slack_service.py         # Executive-format Slack block delivery
│   │   └── n8n_service.py           # n8n webhook triggers
│   ├── db/
│   │   ├── client.py                # Supabase client singleton
│   │   ├── queries.py               # All DB query classes
│   │   └── migrations/              # SQL migration files (run in order)
│   ├── models/                      # Pydantic request/response schemas
│   ├── utils/                       # Structured logging (structlog)
│   ├── config.py                    # Settings via pydantic-settings
│   ├── main.py                      # FastAPI app + CORS + rate limiting
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── page.tsx             # Dashboard (KPIs, agents, activity feed)
│   │   │   ├── briefings/           # Briefings list with search + filter
│   │   │   ├── executions/          # Workflow execution history + chart
│   │   │   ├── memory/              # Memory comparison diffs
│   │   │   └── settings/
│   │   ├── components/
│   │   │   ├── dashboard/           # KpiCard, AgentStatusGrid, ActivityFeed,
│   │   │   │                        # GenerateBriefingModal, PipelineViz, etc.
│   │   │   ├── briefings/           # BriefingCard (expandable)
│   │   │   ├── executions/          # ExecutionCard with step timeline
│   │   │   ├── memory/              # MemoryDiffCard (old vs new snapshot)
│   │   │   └── layout/              # Sidebar, Topbar
│   │   ├── hooks/
│   │   │   ├── usePolling.ts        # Generic polling primitive
│   │   │   ├── useDashboard.ts      # KPIs + activity feed with polling
│   │   │   ├── useBriefings.ts      # Briefings list with polling
│   │   │   ├── useExecutions.ts     # Execution history with polling
│   │   │   ├── useAgents.ts         # Agent status with polling
│   │   │   └── useMemory.ts         # Memory comparisons with polling
│   │   ├── services/
│   │   │   ├── api.ts               # Base fetch client with retry
│   │   │   ├── briefings.ts
│   │   │   ├── executions.ts        # Includes poll() for live execution tracking
│   │   │   ├── agents.ts
│   │   │   ├── memory.ts
│   │   │   └── dashboard.ts
│   │   └── lib/
│   │       ├── types.ts             # Shared TypeScript interfaces
│   │       ├── mock-data.ts         # Fallback data (shown when backend is down)
│   │       └── utils.ts
│   ├── .env                         # NEXT_PUBLIC_API_URL=http://localhost:8000
│   └── package.json
└── n8n/
    ├── daily_briefing_workflow.json      # Runs every 24h → POST /api/briefings/generate
    └── competitor_monitor_workflow.json  # Runs every 12h → POST /api/workflows/orchestrate
```

## Database Schema

Run migrations in order from `backend/db/migrations/`:

| Table | Purpose |
|---|---|
| `agent_tasks` | Every agent execution — status, input, result, error |
| `research_findings` | Scraped + analyzed findings with tags and source URLs |
| `briefings` | Generated briefings with raw markdown |
| `memory_entries` | Key-value persistent memory (namespace + key) |
| `competitor_snapshots` | Historical competitor snapshots for diff comparison |
| `workflow_executions` | End-to-end workflow run records (for n8n polling) |
| `execution_logs` | Structured agent logs (powers the live activity feed) |

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

Run the three SQL files in `backend/db/migrations/` against your Supabase project via the SQL editor, in order:
1. `001_initial_schema.sql`
2. `002_competitor_snapshots.sql`
3. `003_workflow_executions.sql`

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
# .env is already created with NEXT_PUBLIC_API_URL=http://localhost:8000
npm run dev
```

Frontend runs at `http://localhost:3000`.

### 4. n8n (optional)

Import the JSONs from `n8n/` into your n8n instance. Update the webhook URLs in each workflow to point at your backend URL.

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

## Key API Endpoints

```
POST /api/workflows/run              Trigger a full autonomous workflow
GET  /api/workflows/executions       List recent workflow runs
GET  /api/workflows/status/{id}      Poll a running workflow

GET  /api/briefings/                 List briefings (enriched for frontend)
POST /api/briefings/generate         Queue a briefing generation

GET  /api/agents/status              Live agent health from agent_tasks
GET  /api/dashboard/stats            KPI aggregates + 7-day chart data
GET  /api/activity/feed              Live execution log stream

GET  /api/memory/comparisons         Competitor snapshot diffs
GET  /api/memory/stats               Memory system statistics
```

## Running Tests

```bash
cd backend
source venv/bin/activate
python -m pytest tests/ -v
```
