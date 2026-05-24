# Founder Intelligence Agent

A production-style autonomous multi-agent platform for startup founders. Monitors competitors, researches AI companies, stores persistent memory, and generates strategic briefings.

## Stack

- **Backend**: FastAPI (Python)
- **Frontend**: Next.js 14 (TypeScript)
- **Database**: Supabase (PostgreSQL)
- **Workflows**: n8n
- **LLM**: Groq API
- **Scraping**: Apify
- **Notifications**: Slack Webhooks

## Project Structure

```
founder-intelligence/
├── backend/
│   ├── agents/          # Agent definitions and orchestration
│   ├── api/             # FastAPI route handlers
│   ├── services/        # External service integrations
│   ├── memory/          # Persistent memory layer
│   ├── workflows/       # n8n workflow triggers
│   ├── models/          # Pydantic schemas
│   ├── db/              # Supabase client and queries
│   ├── utils/           # Shared utilities
│   └── main.py
├── frontend/
│   ├── app/             # Next.js app router
│   ├── components/      # Reusable UI components
│   └── lib/             # API client and helpers
├── n8n/                 # Exported n8n workflow JSONs
└── docs/
```

## Setup

### Prerequisites

- Python 3.11+
- Node.js 18+
- Supabase project
- Groq API key
- Apify API token
- Slack webhook URL

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# fill in your .env values
uvicorn main:app --reload
```

### Frontend

```bash
cd frontend
npm install
cp .env.example .env.local
# fill in your .env.local values
npm run dev
```

### Database

Run the SQL migrations in `backend/db/migrations/` against your Supabase project via the Supabase SQL editor or CLI.

### n8n

Import the workflow JSONs from `n8n/` into your n8n instance. Set the webhook URLs to point at your backend.

## Environment Variables

See `backend/.env.example` and `frontend/.env.example` for all required variables.

## API Docs

Once the backend is running, visit `http://localhost:8000/docs` for the interactive Swagger UI.
