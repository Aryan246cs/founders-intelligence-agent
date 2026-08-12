# Founder Intelligence Agent — Architecture & Interview Guide

Everything you need to explain this project confidently: what it does, how it is built,
why each decision was made, what to demo, and what to say when they push back.

**Numbers you can quote:** ~7,100 lines of Python across 8 agents and 10 route modules,
~5,200 lines of TypeScript across 8 pages, 30 HTTP endpoints, 8 Postgres tables,
67 backend tests. Two autonomous pipelines, five external services.

---

## 1. The 30-second pitch

> "It's an autonomous research platform for startup founders. You type a startup idea in
> plain English — nothing else. The system decides what to search for, finds real
> competitors on the live web, crawls their sites and pricing pages, extracts structured
> intelligence with an LLM, and produces a strategic report: competitor landscape, feature
> matrix, pricing table, market gaps, SWOT, and concrete recommendations. It also runs
> scheduled competitor monitoring that only alerts you when something strategically
> meaningful actually changed."

**The two-minute version** adds the engineering:

> "It's a multi-agent backend in FastAPI. Each agent is a class with one `execute` method
> and a shared base that handles task records, structured logging and progress reporting.
> A planner agent turns a natural-language request into a JSON execution plan, and an
> orchestrator runs those steps. Long pipelines run as background jobs, and the UI polls
> real step state — so the progress you see is measured server-side, not animated.
> There's a memory layer that diffs each competitor against previous snapshots so briefings
> only surface genuine change, not noise."

---

## 2. System architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│  Next.js 14 (App Router, TypeScript, Tailwind)                      │
│  Dashboard · Startup Research · Briefings · Executions · Memory     │
│  hooks/ → services/ → fetch  ·  polling pauses on hidden tabs        │
└───────────────────────────────┬─────────────────────────────────────┘
                                │  REST + JSON, polled
┌───────────────────────────────▼─────────────────────────────────────┐
│  FastAPI  (backend/main.py)                                          │
│  CORS · slowapi rate limiting · structlog · 30 endpoints             │
├──────────────────────────────────────────────────────────────────────┤
│  API layer      api/routes/*.py      thin — validate, dispatch, shape │
│  Agent layer    agents/*.py          all pipeline logic               │
│  Service layer  services/*.py        one module per external system   │
│  Data layer     db/queries.py        every SQL call in one file       │
└───┬──────────────┬───────────────┬──────────────┬───────────────────┘
    │              │               │              │
┌───▼────┐  ┌──────▼─────┐  ┌──────▼─────┐  ┌────▼──────┐  ┌──────────┐
│Supabase│  │   Groq     │  │   Apify    │  │   Slack   │  │   n8n    │
│Postgres│  │ llama-3.3  │  │ search +   │  │  webhook  │  │ schedule │
│8 tables│  │  70b       │  │ crawler    │  │           │  │          │
└────────┘  └────────────┘  └────────────┘  └───────────┘  └──────────┘
```

**Why layered this way:** every route stays thin enough to read in one screen, every agent
is unit-testable without HTTP, and swapping a provider (Groq → any LLM, Apify → any
scraper) touches exactly one file in `services/`.

---

## 3. The agent model

### 3.1 The base class — `backend/agents/base.py`

Every agent inherits from `BaseAgent` and implements one method. The base handles the
three cross-cutting concerns so no agent repeats them:

```python
class BaseAgent(ABC):
    agent_type: str = "base"

    def __init__(self, progress: Optional[ProgressReporter] = None) -> None:
        self.task_id: Optional[str] = None
        self.progress = progress or NULL_REPORTER

    async def run(self, input_data):
        task = AgentTaskQueries.create(self.agent_type, input_data)   # 1. task record
        self.task_id = task["id"]
        AgentTaskQueries.update_status(self.task_id, "running")
        try:
            result = await self.execute(input_data)                    # 2. domain logic
            AgentTaskQueries.update_status(self.task_id, "completed", result=result)
            return result
        except Exception as e:
            AgentTaskQueries.update_status(self.task_id, "failed", error=str(e))
            raise

    @abstractmethod
    async def execute(self, input_data): ...

    def _step(self, key, message, metadata=None):
        self.progress.start(key, message)   # 3. live progress + durable log,
        self._log("info", message, metadata) #    written from one statement
```

**Talking point:** every agent run leaves a row in `agent_tasks` and a trail in
`execution_logs`. That is what powers the live activity feed, the agent-health panel and
the uptime percentages — none of those are decorative, they are queries over real rows.

### 3.2 The eight agents

| Agent | Job |
|---|---|
| `PlannerAgent` | Natural language → JSON execution plan (which agents, what inputs) |
| `OrchestratorAgent` | Runs a plan's steps in order, propagates the progress reporter |
| `StartupResearchAgent` | The flagship 10-step research pipeline |
| `CompetitorMonitorAgent` | Crawls one competitor, extracts structured intel, saves a finding |
| `ResearchAgent` | Google search via Apify + LLM analysis |
| `MemoryAgent` | get/set/list + `compare` and `snapshot` against history |
| `BriefingAgent` | Turns this run's findings into a founder briefing |
| `BaseAgent` | The abstract contract above |

### 3.3 Registry + factory — `backend/agents/orchestrator.py`

```python
AGENT_REGISTRY: Dict[str, Type[BaseAgent]] = {
    "competitor_monitor": CompetitorMonitorAgent,
    "research": ResearchAgent,
    "briefing": BriefingAgent,
    "memory": MemoryAgent,
    "planner": PlannerAgent,
    "startup_research": StartupResearchAgent,
}
```

The planner emits `agent_type` strings; the orchestrator looks them up here. Adding a new
agent is one class plus one registry line — the planner prompt and the API need no changes
beyond describing it.

---

## 4. Pipeline 1 — Startup Research (the flagship)

`backend/agents/startup_research_agent.py` · triggered from the Startup Research page.

```
 1  parse     LLM extracts industry, keywords, ICP, business model from the raw idea
 2  strategy  builds India-first + global Google queries from that metadata
 3  search    Apify Google Search, India queries first (they get more URL budget)
 4  scrape    Apify crawler on up to 8 candidate domains, blocklist filters noise
 5  pricing   for each competitor, tries /pricing, /plans, /price to extract real tiers
 6  recover   FALLBACK: if <2 competitors scraped, mine the search snippets instead
 7  matrix    builds the feature comparison grid + pricing intelligence table
 8  insights  LLM writes the strategic report — validated, retried up to 3×
 9  persist   saves the report to Postgres and a summary into the memory namespace
10  deliver   optional Slack summary
```

**Three details worth volunteering in the interview:**

1. **A domain blocklist, not a prompt instruction.** `_SKIP_DOMAINS` holds ~70 domains —
   Google, LinkedIn, Crunchbase, TechCrunch, G2, job boards. Search results are full of
   listicles and directories; asking the LLM nicely to ignore them is unreliable and costs
   tokens. Filtering in Python before scraping is deterministic and free.

2. **The fallback ladder.** Real sites block crawlers. If fewer than two competitors are
   scraped, the pipeline analyses the search-result snippets instead of failing. That is
   the difference between a demo that works on stage and one that shows an error.

3. **Validated retries, not blind ones.** The report call checks that all six required
   sections came back non-empty and retries up to three times if not, because LLMs
   intermittently return partial JSON:

   ```python
   missing = [f for f in required if not parsed_report.get(f)]
   if missing:
       self._log("warning", f"Attempt {attempt+1}: missing fields {missing} — retrying")
       continue
   ```

   If all three attempts fail, `_build_fallback_strategic()` produces a report from what
   was *actually observed* — competitor names, positioning, who publishes pricing — and
   states plainly that AI analysis was unavailable. **It never invents market claims.**
   There is a regression test asserting no domain-specific language leaks in.

---

## 5. Pipeline 2 — Briefing workflow

`POST /api/workflows/run` · triggered from the dashboard's Generate Briefing button.

```
request: "Monitor Zomato and Swiggy and generate a founder briefing"
   │
   ▼
PlannerAgent ──► {"steps": [
                    {"agent_type": "competitor_monitor", "input": {...Zomato}},
                    {"agent_type": "competitor_monitor", "input": {...Swiggy}},
                    {"agent_type": "briefing",           "input": {...}}]}
   │
   ▼
OrchestratorAgent runs each step in order
   │
   ├─ CompetitorMonitorAgent → Apify crawl → LLM extract → research_findings row
   ├─ CompetitorMonitorAgent → …
   └─ BriefingAgent
         ├─ fetch findings from THIS run only (30-minute window + competitor filter)
         ├─ diff each competitor against history  (comparison engine)
         ├─ signal gate: automated runs abort if nothing high-signal changed
         ├─ LLM writes the briefing
         ├─ dedup: >75% similar to a recent briefing ⇒ suppressed
         └─ save + optional Slack delivery
```

### The comparison engine — `services/comparison/comparison_engine.py`

This is the part that makes the product useful rather than noisy, and **it contains no LLM
calls at all** — it is deterministic and unit-tested (that is a deliberate choice worth
stating: you cannot write reliable tests against a model's mood).

Four filters, in order:

1. **Suppressed entities** — a "competitor" named `AI`, `chatbots`, `platform` or
   `analytics` is dropped outright. Comparing generic nouns produces generic output.
2. **Length floor** — findings under 80 characters carry no intelligence.
3. **Near-duplicate rejection** — `SequenceMatcher` ratio ≥ 0.72 against previous findings
   means it is not new.
4. **High-signal categories** — what survives must match one of ten categories:
   `pricing_change`, `enterprise_expansion`, `product_launch`, `model_release`,
   `infrastructure_move`, `partnership_deal`, `funding_event`, `developer_ecosystem`,
   `competitive_positioning`, `go_to_market`. Anything else is noise.

```python
if not changes:
    logger.info("All changes were low-signal — suppressing", competitor=competitor)
    return {"competitor": competitor, "has_changes": False, "changes": [], ...}
```

**The line that lands:** *"A competitive intelligence tool that fires every day is a tool
you mute in week two. The engine is designed to stay silent — the signal gate only applies
to automated runs, so a founder who clicks the button always gets an answer, but the
scheduled job only interrupts them when something real happened."*

---

## 6. The upgrade worth leading with: real progress, not animated progress

**The problem.** These pipelines take 1–5 minutes: several Apify crawls plus ~10 LLM calls.
Originally `/run` executed the whole pipeline inside the HTTP request. Two consequences:
the browser held a connection open for minutes (and any proxy in between could time it
out), and since the client learned nothing until the very end, the UI *estimated* progress
with `setTimeout` timers:

```typescript
// the old approach — a guess, dressed up as telemetry
const STEP_DURATIONS = [6000, 4000, 8000, 25000, 20000, 8000, 10000, 6000, 4000, 2000];
```

**The fix.** A job tracker (`services/job_tracker.py`) plus background execution:

```
POST /api/startup-research/run
   ├─ create workflow_executions row  (durable record, status='running')
   ├─ create Job from the agent's declared step list
   ├─ asyncio.create_task(pipeline)   ← returns control immediately
   └─ 202 { job_id, execution_id, poll_url, steps_total }

GET /api/startup-research/jobs/{job_id}   ← polled every 1.5s by the UI
   └─ { status, steps: [{key, label, status, detail, duration_ms}],
        current_step, progress_pct, result, error }
```

The agent marks steps as it reaches them; the UI renders exactly that. Every duration on
screen is measured server-side. Steps that legitimately did not apply — Slack when you
didn't ask for it, the snippet-recovery fallback when scraping worked — show as *skipped*
rather than silently completing.

**Three design points to raise before they ask:**

- **Why in-memory and not Redis/Celery?** The registry is a bounded dict in the API
  process. It is correct for single-process deployment, and terminal outcomes are always
  mirrored to the `workflow_executions` table, which is the durable record — a lost job
  only loses live *progress*, never results. Scaling to multiple workers means replacing
  one module; the agent-facing API (`reporter.start/done/fail`) would not change. *Naming
  the limit before they find it is the whole point.*
- **Backwards compatibility.** n8n and cron were written against the blocking behaviour, so
  `?wait=true` (research) and `background: false` (workflows, the default) preserve it
  exactly. The web UI opts in to background mode. No existing caller broke.
- **`NULL_REPORTER`.** Agents run untracked in tests, from n8n and from scripts. Rather
  than `if self.progress:` at 30 call sites, an object whose methods do nothing is
  injected. Null-object pattern — the call sites stay clean.

---

## 7. Data model

| Table | Purpose |
|---|---|
| `agent_tasks` | One row per agent run — type, input, status, result, error, timings |
| `research_findings` | Extracted competitor intelligence with tags + source URL |
| `briefings` | Generated briefings, raw markdown, Slack delivery flag |
| `memory_entries` | Namespaced key/value memory, `unique(key, namespace)` |
| `execution_logs` | Structured agent logs — powers the live activity feed |
| `competitor_snapshots` | Point-in-time competitor state for historical diffing |
| `workflow_executions` | One row per end-to-end run — the durable execution record |
| `startup_research_reports` | Full reports; each section a JSONB column |

**Why JSONB for report sections:** the report shape evolved through the build (SWOT and the
pricing table were added late). Rigid columns would have meant a migration per section
while the format was still moving; JSONB let the schema stay still. The cost is no
constraints inside those blobs — an acceptable trade for a document that is always read
whole, and one worth naming as a trade rather than a free win.

**Migrations are additive.** `002`, `003`, `004` only add tables — no existing table is
ever altered, so re-running them on a live database is safe.

---

## 8. Frontend architecture

```
src/
├── app/           8 routes (App Router, all client components)
├── components/    grouped by feature, not by type
├── hooks/         one hook per data domain — polling + state
│   ├── usePolling.ts      shared timer, pauses on hidden tabs
│   ├── useJobProgress.ts  polls a job until terminal, tolerates dropped polls
│   ├── useHealth.ts       live dependency status
│   └── useDashboard/Agents/Briefings/Executions/Memory
├── services/      one module per API domain; the only place fetch is called
└── lib/           types + utils
```

**The rule:** components never call `fetch`. `hooks/ → services/ → api.ts`. One place
handles base URL, retries, and turning a FastAPI `detail` into a readable message.

**Two decisions to raise:**

- **Polling, not WebSockets.** Everything here is a periodic read of state that changes on
  the order of seconds; polling has no connection lifecycle, no reconnect logic, and works
  through any proxy. WebSockets would be the right call for genuinely push-shaped data —
  this isn't that. Polling pauses on hidden tabs so a backgrounded dashboard isn't burning
  requests all day.
- **No fabricated fallback data.** An earlier version shipped a `mock-data.ts` that the
  dashboard silently fell back to when the API was down — so a broken backend rendered
  "1,247 executions, 99.8% uptime". That was deleted. Now the UI shows real empty states
  plus a banner naming exactly which dependency is broken. *"A dashboard that renders
  zeros because Supabase is unreachable looks identical to one that renders zeros because
  nothing has run yet — unless you say which."*

---

## 9. Engineering decisions — the "why" answers

| Decision | Reasoning |
|---|---|
| **Groq over OpenAI** | Inference speed. The research pipeline makes ~10 sequential LLM calls; at OpenAI latency this is a 4–5 minute wait, on Groq it is well under two. For a pipeline that must feel interactive, tokens/second mattered more than peak model quality. |
| **Comparison engine has no LLM** | Deterministic and testable. "Did this change matter?" must give the same answer twice, and I need it under unit test — you cannot write a stable test against a model's mood. |
| **Blocking SDKs via `asyncio.to_thread`** | The Groq and Apify clients are synchronous. Calling them directly in an async handler blocks the event loop and stalls every other request. `to_thread` moves them to the thread pool. |
| **Service-role key server-side only** | The key bypasses row-level security. It never leaves the backend; the browser only ever learns whether a service answered. |
| **Retry only transient failures** | Original code retried everything 3× — including a rejected API key, turning a clear error into a slow opaque one. Now only rate limits, connection errors and timeouts retry; auth failures and decommissioned models fail immediately with an actionable message. |
| **Findings scoped to a 30-minute window** | Without it, a briefing about food delivery would pull in yesterday's AI-model findings and write a report about companies the user never asked about. The briefing agent filters to this run's competitors and time window. |
| **Additive migrations only** | Safe to re-run against a live database; no destructive ALTERs. |

---

## 10. Demo script (rehearse this exact path)

**Before you leave the house:**

```bash
make doctor          # verifies Supabase, Groq, Apify, Slack — fix anything red
make dev             # backend :8000 + frontend :3000
```

Then run one full research **before** the interview so history has real content.

**The 6-minute walkthrough:**

1. **Dashboard (30s).** "Every number here is a live aggregate — briefings generated, agent
   uptime, executions today. Bottom right is the activity feed: every agent step writes a
   row as it runs." Point at the sidebar: *"those integration dots are real probes, not
   decoration."*

2. **Startup Research — the flagship (3 min).** Type a real idea. Click Generate.
   → *"Watch the steps. This is not an animation — the backend returns a job id, each step
   lights up when the agent actually enters it, and those durations on the right are
   measured server-side. Step 6 will show as skipped because scraping succeeded, so the
   snippet-recovery fallback wasn't needed."*
   Then walk the report: competitor cards → feature matrix → pricing table → market gaps →
   SWOT → sources. **Click a source URL.** *"Every claim traces back to a page we actually
   crawled."*

3. **Executions (1 min).** "Every run is recorded with duration and step count, whether
   triggered here, by n8n on a schedule, or by an API call."

4. **Memory (1 min).** "Each competitor is snapshotted and diffed. This page only shows
   runs where something high-signal changed — everything else is suppressed by design."

5. **Swagger at `/docs` (30s).** "30 endpoints, all typed with Pydantic. This is what n8n
   calls on a schedule."

**If the live pipeline fails on stage:** don't panic and don't hide it — open the failed
report, show the error surfaced in the UI, and say: *"That's the degraded path doing its
job. Apify is blocked by that site — the fallback report contains only verified crawl data
and says explicitly that AI analysis was unavailable, because a plausible-looking invented
gap is worse than a short honest report."* Then open a report from history. **A handled
failure explained well is a stronger signal than a happy path.**

---

## 11. Questions they will ask

**"How do you stop the LLM from hallucinating competitors?"**
Three layers. The model never chooses companies — it only analyses pages we fetched.
Domains are filtered by blocklist before scraping. The extraction prompt says explicitly
*"NEVER invent features, prices, or names not present in the content"* and returns
`{"skip": true}` for non-companies. Every competitor card carries the source URL that
produced it, so any claim is checkable in one click.

**"What happens when a competitor's site blocks your crawler?"**
That is the common case, not the edge case. The pipeline falls back to analysing search
snippets, which are enough to identify the company and its positioning even when the page
body is unreachable. If even that fails, the report says so rather than filling the gap.

**"Why not LangChain / CrewAI / AutoGen?"**
The orchestration here is a sequential list of steps with typed inputs — roughly 60 lines.
A framework would have added a dependency, an abstraction layer and a debugging surface to
replace code I can read end to end. I would reach for one when I need agents that loop,
negotiate or call each other dynamically. *(This answer works because you can then explain
every line of the orchestrator — never claim you'd never use a framework.)*

**"How would you scale this?"**
Three bottlenecks, in the order they'd bite:
1. *In-memory job registry* → Redis or Celery/RQ, so multiple workers share job state.
2. *Sequential competitor scraping* → `asyncio.gather` with a semaphore; the crawls are
   independent and this is the single biggest latency win available.
3. *Apify cost and rate limits* → cache crawls per domain with a TTL; competitor sites do
   not change hourly.
Then: per-user auth and row-level security (today the service-role key means one shared
workspace).

**"What is the weakest part?"**
Pick one and answer honestly — that answer is what they're testing:
*"Extraction quality depends on page structure. A React site that renders pricing client-side
gives the cheerio crawler nothing, and we fall back to `Not publicly disclosed` — which is
honest but less useful. The fix is a rendering crawler for known-hard domains, at higher
cost per crawl. I chose speed and cost by default and left the accuracy escape hatch."*

**"How do you test something that depends on an LLM?"**
Split the deterministic parts out and test those properly — the comparison engine, the job
tracker, the response envelopes, the fallback report builder. For the pipeline itself, the
external services are replaced with fakes and the assertion is on *behaviour*: which steps
ran, which were skipped, which step is blamed on failure. 67 tests, no network calls, sub-second.

**"Why India-first search?"**
Product decision. Generic queries return US SaaS incumbents that an Indian founder cannot
usefully benchmark against. The parser generates explicit India-biased queries, those run
first, and they get 8 of the 12 URL slots — with global results kept for context.

---

## 12. Known limitations (say these before they find them)

- **Single-tenant.** No auth; the service-role key means one shared workspace.
- **In-process job registry.** Live progress is lost on restart; results are not.
- **Sequential scraping.** Correct but slow — parallelising is the obvious next win.
- **No caching.** Every run re-crawls, even for a domain seen ten minutes ago.
- **Cheerio crawler.** No JavaScript rendering, so client-rendered pricing pages are missed.
- **Briefing dedup is lexical.** `SequenceMatcher`, not embeddings — cheap and predictable,
  but it will miss two briefings that say the same thing in different words.

---

## 13. File map — what to have open

| If they ask about… | Open |
|---|---|
| The agent abstraction | `backend/agents/base.py` (52 lines — read it aloud) |
| The flagship pipeline | `backend/agents/startup_research_agent.py` |
| Signal filtering | `backend/services/comparison/comparison_engine.py` |
| Real progress tracking | `backend/services/job_tracker.py` |
| Planning / orchestration | `backend/agents/planner_agent.py`, `orchestrator.py` |
| API design | `backend/api/routes/workflows.py` |
| Failure handling | `backend/services/groq_service.py`, `db/client.py` |
| Testing approach | `backend/tests/test_comparison_engine.py`, `test_job_endpoints.py` |
| Frontend data flow | `frontend/src/hooks/useJobProgress.ts` |

---

## 14. Commands

```bash
make setup     # venv + npm install (first time only)
make doctor    # preflight: are Supabase, Groq, Apify, Slack reachable?
make dev       # run backend :8000 and frontend :3000 together
make test      # 67 backend tests
make build     # production frontend build (also typechecks)
```

Backend docs: `http://localhost:8000/docs` · Health: `http://localhost:8000/health/services`
