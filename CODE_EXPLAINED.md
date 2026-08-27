# Code Explained — Interview Prep Sheet

Plain-English guide to this codebase: what it does, how it's arranged, and a line-by-line walkthrough of the two files you're most likely to be grilled on.

---

## 1. What the product does (30-second answer)

> "It's a competitive-intelligence tool for startup founders. You type your startup idea, and a chain of AI agents searches Google, scrapes competitor websites, pulls their pricing, and writes you a strategy report — competitors, feature matrix, market gaps, SWOT, recommendations. It also runs a second flow that monitors named competitors and sends a daily briefing to Slack."

**Stack:** Next.js 14 (frontend) → FastAPI (backend) → Supabase/Postgres (database).
**External brains:** Groq (LLM), Apify (Google search + web scraping), Slack (delivery), n8n (scheduling).

---

## 2. Top-level folders

| Folder | What lives there |
|---|---|
| `backend/` | The FastAPI Python API — all the agents, AI logic, and database code |
| `frontend/` | The Next.js dashboard the user actually clicks on |
| `n8n/` | Two JSON files you import into n8n so it calls our API on a schedule |
| `README.md`, `ARCHITECTURE.md`, `Makefile` | Docs and `make dev` / `make test` shortcuts |

---

## 3. Backend map (`backend/`)

Data flows **downward**. Each layer only talks to the layer below it.

```
HTTP request
   ↓
api/routes/     ← the URLs (thin — no business logic)
   ↓
agents/         ← the brains (each agent does one job)
   ↓
services/       ← the outside world (Groq, Apify, Slack, n8n) + job tracking
   ↓
db/             ← Supabase reads and writes
```

| File / folder | What's inside |
|---|---|
| `main.py` | App entry. Creates the FastAPI app, adds CORS + rate limiting, plugs in all 10 routers. ~66 lines. |
| `config.py` | Reads `.env` into a typed `Settings` object. Supabase/Groq/Apify keys are **required** (app won't boot without them); Slack/n8n are optional (app just skips them). |
| `agents/base.py` | `BaseAgent` — the parent class every agent inherits. |
| `agents/orchestrator.py` | Runs a list of agent steps one after another. Holds the `AGENT_REGISTRY` dict. |
| `agents/planner_agent.py` | Turns a sentence ("Monitor Zomato and Swiggy") into a JSON step list, using the LLM. |
| `agents/startup_research_agent.py` | **The big one (1031 lines).** The 10-step startup research pipeline. |
| `agents/competitor_monitor.py` | Scrapes one competitor site, LLM-summarises it, saves a "finding". |
| `agents/research_agent.py` | Google-searches a query, LLM-summarises the results, saves findings. |
| `agents/briefing_agent.py` | Takes recent findings → writes a markdown briefing → saves it → optionally Slacks it. |
| `agents/memory_agent.py` | Reads/writes memory; also runs `compare` to diff a competitor against its own history. |
| `services/groq_service.py` | LLM wrapper. Retries, and converts messy LLM text into JSON. |
| `services/apify_service.py` | Google search + website scraping wrapper. |
| `services/slack_service.py` | Turns markdown into Slack "blocks" and posts to the webhook. |
| `services/n8n_service.py` | Fires an n8n webhook. |
| `services/job_tracker.py` | **Second big one.** Live progress tracking for long-running runs. |
| `services/comparison/comparison_engine.py` | Decides if a competitor change is *actually important* (483 lines of filtering). |
| `services/memory/retrieval.py` | Fetches a competitor's past findings/snapshots for comparison. |
| `db/client.py` | Creates the Supabase client once (singleton) + human-readable DB error messages. |
| `db/queries.py` | All SQL-ish code in one place — one class per table (`BriefingQueries`, `MemoryQueries`, …). |
| `db/migrations/*.sql` | 5 SQL files that create the tables. Run them in Supabase's SQL editor. |
| `models/` | Pydantic shapes (`AgentTask`, `Briefing`, `MemoryEntry`) used for request validation. |
| `api/routes/` | 10 route files, one per feature area (see table below). |
| `utils/logger.py` | Structured JSON logging via `structlog`. |
| `scripts/doctor.py` | `make doctor` — checks all 4 external services are reachable before a demo. |
| `tests/` | 7 pytest files, ~1300 lines. Mostly the comparison engine, job tracker, and pipeline. |

### The API routes

| Route file | URL prefix | Main endpoints |
|---|---|---|
| `startup_research.py` | `/api/startup-research` | `POST /run` (returns a `job_id`), `GET /jobs/{id}`, `GET /`, `GET /{id}`, `POST /{id}/slack` |
| `workflows.py` | `/api/workflows` | `POST /run` (plan→execute), `POST /manual-trigger`, `GET /status/{id}`, `GET /jobs/{id}`, `GET /executions` |
| `health.py` | `/health` | `GET /` (is the app alive?), `GET /services` (can we reach Supabase/Groq/Apify/Slack?) |
| `dashboard.py` | `/api/dashboard` | `GET /stats` — the 6 KPI tiles + 7-day chart |
| `agents.py` | `/api/agents` | `GET /status` (per-agent uptime), `POST /run`, `GET /{task_id}` |
| `briefings.py` | `/api/briefings` | `GET /` — reads briefings and regex-parses the markdown into UI fields |
| `activity.py` | `/api/activity` | `GET /feed` — the live event log on the dashboard |
| `memory.py`, `memory_comparisons.py` | `/api/memory` | memory get/set + snapshot diffs for the Memory page |
| `research.py` | `/api/research` | fire a research or competitor-monitor agent |

### The database tables (5 migrations)

| Table | Holds |
|---|---|
| `agent_tasks` | One row per agent run — type, input, status, result, error |
| `research_findings` | One row per thing discovered, with `tags[]` used for competitor filtering |
| `briefings` | Generated markdown briefings |
| `memory_entries` | Key/value/namespace store (unique on `key + namespace`) |
| `execution_logs` | Every log line an agent emits → powers the activity feed |
| `competitor_snapshots` | Point-in-time competitor state, for diffing later |
| `workflow_executions` | One row per end-to-end run — the **durable** record |
| `startup_research_reports` | The full research report (most columns are JSONB) |

---

## 4. Frontend map (`frontend/src/`)

Same idea, also layered:

```
app/ (pages)  →  hooks/ (state + polling)  →  services/ (fetch calls)  →  backend
       ↘ components/ (dumb UI)
```

| Folder | What's inside |
|---|---|
| `app/` | Next.js App Router pages: `/` dashboard, `/briefings`, `/executions`, `/memory`, `/startup-research`, `/settings`. `layout.tsx` wraps everything in Sidebar + Topbar and forces dark mode. |
| `hooks/` | One hook per data type: `useDashboard`, `useAgents`, `useBriefings`, `useExecutions`, `useMemory`, `useHealth`, `useStartupResearch`. All built on `usePolling`. Plus `useJobProgress` for live pipeline steps. |
| `services/` | `api.ts` is the shared fetch client (retries + error message extraction). The rest are thin typed wrappers per feature. |
| `lib/types.ts` | All TypeScript interfaces — mirrors the backend JSON shapes. |
| `lib/utils.ts` | `cn()` class merger + `formatDuration`. |
| `components/dashboard/` | KPI cards, pipeline diagram, agent grid, activity feed, the Generate-Briefing modal. |
| `components/startup-research/` | `ResearchLauncher` (form + live step timeline), `ResearchReport` (740-line tabbed report viewer), `ResearchHistory`. |
| `components/layout/`, `brand/`, `ui/` | Sidebar, Topbar, logo, avatar, badge. |

**Two useful details to know:**
- `usePolling` **pauses when the browser tab is hidden** and refreshes instantly on return — so a backgrounded dashboard doesn't hammer Supabase all day.
- `lib/api.ts` (an axios client) is **dead code** — nothing imports it. Everything uses `services/api.ts` (plain `fetch`). Say so if asked; don't pretend it's live.

---

## 5. Architecture patterns — the names to say out loud

| Pattern | Where it is | One-line explanation |
|---|---|---|
| **Layered (N-tier) architecture** | whole backend | routes → agents → services → db. Nothing skips a layer upward. |
| **Multi-agent / Plan-and-Execute** | `planner_agent` + `orchestrator` | One agent writes the plan, another runs it. |
| **Template Method** | `BaseAgent.run()` | The parent fixes the *steps* (create task → run → save result); children only fill in `execute()`. |
| **Registry + Factory** | `AGENT_REGISTRY`, `get_agent()` | Look an agent up by a string name instead of hard-coding `if/else`. |
| **Repository** | `db/queries.py` | Every table has a class; no raw Supabase calls scattered around. |
| **Adapter / Gateway** | `services/*_service.py` | Each external API is wrapped once, so swapping Groq for OpenAI is a one-file change. |
| **Asynchronous Request-Reply** | `POST /run` → `job_id` → `GET /jobs/{id}` | Long jobs return instantly; the client polls. |
| **Null Object** | `NULL_REPORTER` | Agents can always call `self.progress.start(...)` — outside a job it just does nothing. No `if progress:` checks anywhere. |
| **Retry with exponential backoff** | `tenacity` in Groq/Apify services | Retry the flaky stuff, fail fast on the permanent stuff. |
| **Graceful degradation** | `_build_fallback_strategic`, `_check_slack` | If the LLM dies, still return the *real scraped data*. Never invent. |
| **Singleton** | `get_supabase()`, `get_groq_client()` | One client, created lazily, reused. |

---

# 6. DEEP DIVE #1 — `backend/agents/startup_research_agent.py`

**Why this file matters:** it's the flagship feature, the longest file (1031 lines), and it touches every layer. Expect most questions here.

### 6.1 The shape of the file

Five parts, in order:

1. **`RESEARCH_STEPS`** — the list of 10 step names
2. **Prompts** — 4 big text blocks telling the LLM exactly what JSON to return
3. **`_SKIP_DOMAINS`** — a blocklist of ~70 sites that are never competitors
4. **Helper functions** — query building, URL extraction, validation, fallback report
5. **`StartupResearchAgent.execute()`** — the actual 10-step pipeline
6. **`_send_research_to_slack()`** — formats the report as Slack blocks

### 6.2 `RESEARCH_STEPS` — the contract with the UI

```python
RESEARCH_STEPS = [("parse", "Understanding startup idea"), ("strategy", ...), ...]
```

**In plain words:** a list of 10 `(key, label)` pairs.

**Why it exists:** the API creates the job from this list *before the agent starts*. So the moment you click Generate, the UI already draws all 10 rows greyed out, then lights them up as the agent reaches each one. The frontend never guesses progress — the labels come from here.

> **Interview line:** "The step list is defined once on the backend and exported to the UI. The frontend only maps keys to icons. That way the progress bar can never lie about what's running."

### 6.3 The four prompts

Every prompt says **"Respond ONLY with valid JSON"** and shows the exact shape.

| Prompt | Job |
|---|---|
| `PARSE_IDEA_PROMPT` | Idea sentence → industry, keywords, ICP, business model, **plus 3 India search queries and 2 global ones**. |
| `ANALYZE_COMPETITOR_PROMPT` | Scraped page text → structured competitor object. Has an escape hatch: if the page is a blog/news/directory, reply `{"skip": true}`. |
| `ANALYZE_SNIPPET_PROMPT` | Google snippets → a list of competitors. This is the **Plan B** when scraping fails. |
| `GENERATE_REPORT_PROMPT` | All competitor data → executive summary, positioning, gaps, differentiation, SWOT, recommendations. |

**The anti-fluff rule** is baked into the report prompt — it explicitly bans phrases like *"monitor your competitors"* and *"leverage AI"*, and demands every point cite a named company from the data.

> **Interview line:** "I ask for JSON, not prose, so the output is parseable. And I set `temperature=0.1` for extraction steps because I want the same input to give the same output — creativity is a bug when you're extracting facts."

### 6.4 `_SKIP_DOMAINS`

A `set` of ~70 domains: Google, LinkedIn, Reddit, TechCrunch, YourStory, G2, Crunchbase, Naukri, Amazon, Flipkart…

**Why:** a Google search for "quick commerce startups India" returns mostly *articles about* startups, not the startups. Without this, the pipeline would scrape TechCrunch and report TechCrunch as a competitor. It's a `set` (not a list) so lookups are O(1).

### 6.5 The helper functions

**`_build_search_queries(idea, parsed)`** → `(india_queries, global_queries)`
Takes the LLM's queries and **guarantees a floor**: if the LLM returned fewer than 3 India queries, it builds extras from keywords / industry / the raw idea. Caps at 4 India + 2 global.
*Why:* the LLM sometimes returns 1 query. The pipeline must not go thin because of that.

**`_extract_urls(results, max_urls)`**
Digs into Apify's `organicResults`, pulls the URL/title/description, computes the domain, **skips blocklisted and already-seen domains**, stops at the cap. Has a fallback for older Apify actor versions that return a flat `url` field.
*Key point:* dedup is **by domain**, not by URL — so `example.com/pricing` and `example.com/about` count as one company.

**`_extract_snippets(results)`**
Same walk, but keeps the text snippets instead of URLs. Feeds Plan B.

**`_page_text(pages)`** — joins the first 3 scraped pages, 2500 chars each, so we never blow the LLM's token budget.

**`_is_valid_competitor(c)`** — rejects `{"skip": true}`, empty entries, and names that look like URLs.

**`_build_fallback_strategic(...)`** — the honesty net. If **all three** LLM report attempts fail, this builds a report **purely from what was actually observed**: how many competitors had no public pricing, whether they all share one positioning, how many were found. It explicitly says *"Strategic analysis could not be generated in this run."*

> **Interview line — this is your best answer to "tell me about a design decision":**
> "A fabricated market gap that reads well is worse than an honest short report, because a founder might actually act on it. So the fallback only states things the crawl literally saw, and tells the user the AI step failed."

### 6.6 `execute()` — the 10 steps, walked through

**Input:** `{startup_idea, startup_name, send_to_slack}`. Raises immediately if `startup_idea` is empty.

**Step 1 — Parse (`parse`)**
One Groq call with `PARSE_IDEA_PROMPT`. Out: industry, keywords, ICP, business model, and the search queries.

**Step 2 — Strategy (`strategy`)**
No API call. Just `_build_search_queries()` topping up the query list.

**Step 3 — Search (`search`)**
Runs India queries first (10 results each), then global (8 each). **Every search is individually wrapped in try/except** — one failed query logs a warning and the pipeline keeps going.
Then: `_extract_urls(india, max=8)` + `_extract_urls(global, max=4)`, merged with India first and deduped by domain.
*Why India-first:* the target user is an Indian founder. Global results are context, not the answer. Since the scrape budget is spent top-down, putting India first means India gets scraped first.

**Steps 4–5 — Scrape + Pricing (`scrape`, `pricing`)**
Loops over the first 8 candidate URLs:
1. Scrape up to 2 pages via Apify
2. Skip if under 200 characters (a dead or JS-only page)
3. Send the text to Groq with `ANALYZE_COMPETITOR_PROMPT`
4. Skip if `_is_valid_competitor()` says no
5. **Pricing hunt:** if the competitor has no pricing tiers, try `/pricing`, then `/plans`, then `/price`. First one that returns >150 chars gets analysed and breaks the loop.
6. Record the source, append the competitor
7. **Stop at 6 competitors**

The whole body is in a try/except — one bad site can't kill the run.

**Step 6 — Recover (`recover`) — the Plan B**
`if len(competitors) < 2:` — scraping failed (bot walls, Cloudflare, JS-only sites). Fall back to reading the Google **snippets** with `ANALYZE_SNIPPET_PROMPT`. India snippets first, up to 25 of them, one LLM call. Dedupes against names already found.
If scraping worked, the step is marked **skipped**, not failed — the UI shows a grey dash.

> **Interview line:** "Scraping real websites fails constantly. Rather than return an empty report, I degrade to a lower-fidelity source that I already paid for. The user sees fewer details but still gets named competitors."

**Step 7 — Matrix (`matrix`)**
Pure Python, no LLM. Collects every competitor's features into a `set` (lowercased, deduped), takes the top 10, and builds one row per feature with a `✓` / `—` per competitor. Matching is fuzzy-ish: `feat in cf or cf in feat` (substring both ways). Also builds the flat pricing table.

**Step 8 — Insights (`insights`)**
Packs up to 8 competitors into JSON, sends it with `GENERATE_REPORT_PROMPT`, and **retries up to 3 times** — but not on errors alone. After each attempt it checks all 6 required fields are non-empty, and retries if any are missing. If all 3 attempts fail → `_build_fallback_strategic()`.

> **Interview line:** "This is validation-driven retry, not just error retry. A 200 OK with an empty `market_gaps` array is still a failure from the user's point of view, so I treat it as one."

**Step 9 — Persist (`persist`)**
Computes a 0–100 `research_score`:

```
competitors × 10  +  sources × 4  +  15 (has gaps)  +  10 (has recommendations)
+ 10 (has summary)  +  5 (any public pricing)  +  6 (has SWOT strengths),  capped at 100
```

It's a **data-completeness score, not a quality score** — say that plainly if asked.

Then saves the report. A DB failure here **raises** (the report is the product — no point continuing). Then it mirrors a small summary into `memory_entries`; a failure there is logged as a warning and swallowed, because it's a nice-to-have.

> **Interview line:** "I deliberately made saving the report fatal and saving to memory non-fatal. Fail loudly on the thing the user asked for, quietly on the extras."

**Step 10 — Deliver (`deliver`)**
If `send_to_slack`, builds Slack blocks and posts. Three outcomes, three different UI states: `done` (sent), `skip` (no webhook configured / not requested), `fail_step` (Slack rejected it). Slack failure never fails the run.

**Returns** a small summary dict (`report_id`, counts, score) — not the whole report. The frontend fetches the full report separately by id.

### 6.7 Known rough edges (be honest if asked)

- **`_is_valid_competitor` can crash** on a competitor with an empty `name` but a non-empty `description`: `"".split()[-1]` raises `IndexError`. In the scrape loop it's caught by the surrounding try/except; in the snippet-recovery loop it isn't, so it would fail the run. One-line fix: guard `name.split()` before indexing.
- **Sequential, not parallel.** Sites are scraped one at a time, which is why a run takes 1–5 minutes. `asyncio.gather` with a semaphore would cut that a lot; the trade-off was simpler rate-limit behaviour with Apify and Groq.
- **Feature matching is substring-based**, so "AI chat" and "chat support" can wrongly match. Embeddings would be the real fix.

---

# 7. DEEP DIVE #2 — `backend/services/job_tracker.py`

**Why this file matters:** it's the piece that shows system design thinking, and its own docstring already admits its limits — interviewers love that.

### 7.1 The problem it solves

The research pipeline takes 1–5 minutes. If you run it inside the HTTP request:
- the browser holds a connection open for minutes,
- gateways/proxies time out,
- the user sees **nothing** until the very end.

The old fix was a fake progress bar driven by a timer. That lies.

**The fix here:** the API creates a **Job** (an ordered list of steps), launches the real work as a background `asyncio` task, and returns a `job_id` immediately. The agent marks steps done as it *actually* reaches them. The UI polls `GET /jobs/{id}` every 1.5s and renders real state with real, server-measured durations.

### 7.2 The four pieces

**1. `JobStep`** (a dataclass)
`key`, `label`, `status` (`pending`/`running`/`done`/`failed`/`skipped`), `detail`, `started_at`, `completed_at`.
`duration_ms` is a **computed property** — if the step is still running it measures against *now*, so a running step's timer ticks up without anyone writing to it.

**2. `Job`**
Holds `id` (uuid), `kind`, `summary`, the step list, `status`, timestamps, `error`, `result`, and `execution_id` (the link to the durable DB row).
`to_dict()` is the API response: it counts completed steps, finds the currently running one, and computes `progress_pct` — all derived, nothing stored twice.

**3. `JobRegistry`**
A dict of jobs guarded by a `threading.Lock`. Capped at **200 jobs**; `_evict_locked()` drops the oldest when you go over.
*Why a cap:* it's an in-memory dict on a long-running server. Without eviction it's a slow memory leak. No background cleaner thread needed — eviction happens on insert.

**4. `ProgressReporter`** — the handle agents actually hold

| Method | Meaning |
|---|---|
| `begin()` / `finish(result)` / `fail(error)` | job-level lifecycle |
| `start(key, detail)` | mark a step running |
| `done` / `skip` / `fail_step` | terminal states for one step |
| `detail(key, text)` | update the subtitle without changing status |
| `extend(steps)` | **append steps discovered at runtime** |

### 7.3 The three clever bits (these are the answers to "what's non-obvious here?")

**a) `start()` closes stale earlier steps.**
It walks the list up to the current step and force-completes anything still `running`. Without this, an optional step that was quietly skipped would spin forever in the UI.

**b) `finish()` turns leftover `pending` steps into `skipped`.**
So a completed job never renders half-lit. Skipped ≠ failed — it means "correctly not needed", and the UI greys it out.

**c) `extend()` exists because the plan isn't known up front.**
For the briefing workflow, only `plan` is known at launch. Once the `PlannerAgent` returns, `describe_steps()` converts the plan into `(key, label)` pairs and `extend()` appends them. Keys are **positional** (`step_0`, `step_1`) because the same agent can legitimately appear multiple times in one plan — one `competitor_monitor` per competitor.

### 7.4 The Null Object trick

```python
NULL_REPORTER = ProgressReporter(None)
```

Every method starts with `if not self.job: return`. So an agent can be called from a test, from n8n, or from a script with no job attached, and `self.progress.start(...)` is simply a no-op.

> **Interview line:** "That's the Null Object pattern. It means there isn't a single `if self.progress:` check anywhere in the agent code — the progress calls read as normal statements."

### 7.5 The limitation (say this before they ask)

Straight from the module docstring:

> **"This registry lives in the API process memory, so it is correct for a single-process deployment and loses in-flight jobs on restart."**

Two mitigations:
1. Terminal outcomes are **always mirrored into the `workflow_executions` table** — that's the durable record. The job is just the live view.
2. `GET /jobs/{id}` returns a 404 whose message literally says *"Jobs are held in memory and are lost on restart."*

**The scaling answer:** *"Moving to multiple workers means swapping this one module for Redis or a real queue — Celery or RQ. The agent-facing API — `reporter.start` / `done` / `fail` — wouldn't change at all, because agents only depend on the `ProgressReporter` interface, not on the storage."*

---

## 8. The supporting cast (60 seconds each)

### `agents/base.py` — 70 lines, but every agent inherits it

`BaseAgent.run()` does three things every agent needs, so no agent has to:
1. **Task lifecycle** — insert a row in `agent_tasks`, flip it to `running`, then `completed` or `failed` with the result/error
2. **Logging** — `_log()` writes both a structured console log *and* a durable `execution_logs` row (which is what the dashboard's activity feed reads)
3. **Progress** — `_step()` marks the step running **and** logs the same message in one call, so the activity feed and the progress bar physically cannot drift apart

Subclasses only implement `execute()`. That's the **Template Method** pattern.

### `agents/orchestrator.py`

`AGENT_REGISTRY` maps `"briefing"` → `BriefingAgent`. `execute()` loops the steps, looks up the class, and — importantly — **passes its own reporter into every child**, so a child's sub-steps land on the same timeline. Unknown agent type → `ValueError`.

### `services/groq_service.py`

- Groq's SDK is synchronous, so it's wrapped in `asyncio.to_thread` to avoid blocking the event loop.
- **Retries only transient errors** (rate limit, connection, timeout). A bad API key or a decommissioned model fails identically every time — retrying just turns a clear error into a slow, opaque one.
- Converts errors into *actionable* messages: expired key → "generate a new one at console.groq.com/keys"; 404 on the model → "update GROQ_MODEL in backend/.env".
- `parse_json_response()` handles the reality that LLMs wrap JSON in ```` ``` ```` fences or add chatter: strip fences → `json.loads` → if that fails, grab everything between the first `{` and last `}` → if *that* fails, return `{"raw": ...}` instead of raising.

### `services/comparison/comparison_engine.py`

The "is this actually news?" filter, for the competitor-monitoring flow. A change survives only if it passes **all** of:
1. The competitor isn't a generic term (`SUPPRESSED_ENTITIES`: "ai", "cloud", "innovation"…)
2. The text is ≥ 80 characters and isn't filler ("continues to focus on", "remains committed to")
3. It's < 0.72 similar to anything seen before (`difflib.SequenceMatcher`)
4. It matches one of **10 high-signal categories** — pricing change, funding, product launch, model release, enterprise expansion, partnership, etc.

If nothing survives, it returns `has_changes: False` and an **empty string** — deliberately, so the briefing contains no "no significant changes" noise.

### `db/queries.py`

One static-method class per table. Two details worth knowing:
- `StartupResearchQueries.save()` runs a `json.dumps`/`loads` round-trip on JSONB fields, because Supabase's Python client needs plain dicts and lists.
- `ExecutionLogQueries.log()` **swallows its own exceptions** — a logging failure must never crash an agent. Migration `005` exists because that guard once hid a schema mismatch that silently emptied the activity feed for weeks. Good story if they ask about a bug you fixed.

### Frontend: `useJobProgress` + `ResearchLauncher`

- `useJobProgress(pollPath)` polls every 1.5s, stops on `completed`/`failed`, times out at 10 minutes, and **tolerates 4 consecutive failed polls** before giving up — one dropped request isn't a dead pipeline.
- `ResearchLauncher` maps step **keys** to icons and renders the backend's **labels** verbatim. `deliveredRef` guards against double-fetching the report when React re-renders on the same completed state.

---

## 9. Likely questions → short answers

**"Why polling instead of WebSockets?"**
Polling is stateless, survives reconnects for free, works through any proxy, and 1.5s is plenty for a 3-minute job. WebSockets would add connection management for no user-visible gain.

**"Where does the real state live?"**
Postgres, via Supabase. The job registry is a live *view*; `workflow_executions` and `agent_tasks` are the durable record.

**"What happens when the LLM returns garbage?"**
Three layers: `parse_json_response` salvages malformed JSON → the report step retries 3× with field-level validation → `_build_fallback_strategic` reports only observed facts and says the AI step failed.

**"How would you scale this?"**
Swap `job_tracker` for Redis/Celery; parallelise the scrape loop with `asyncio.gather` + a semaphore; cache Apify results by domain (they're the slow, paid part); add a per-user auth layer, which doesn't exist today.

**"What's the weakest part?"**
In-memory jobs (single-process only), sequential scraping, and substring-based feature matching. All three are known and documented in the code, not accidents.

**"What are you proudest of?"**
The honesty of the failure paths. The system would rather say "the analysis step failed, here's what I actually saw" than generate a confident-sounding market gap that a founder might act on.
