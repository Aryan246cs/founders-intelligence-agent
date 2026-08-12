.PHONY: help setup doctor dev backend frontend test build clean

PY  := backend/venv/bin/python
PIP := backend/venv/bin/pip

help:  ## Show available commands
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-10s\033[0m %s\n", $$1, $$2}'

setup:  ## Create the venv and install backend + frontend dependencies
	python3 -m venv backend/venv
	$(PIP) install -q -r backend/requirements.txt
	cd frontend && npm install
	@echo "Setup complete. Copy backend/.env.example to backend/.env and add your keys."

doctor:  ## Verify Supabase, Groq, Apify and Slack are reachable — run before a demo
	@cd backend && ../$(PY) scripts/doctor.py

dev:  ## Run backend and frontend together (Ctrl-C stops both)
	@echo "Backend  → http://localhost:8000/docs"
	@echo "Frontend → http://localhost:3000"
	@trap 'kill 0' INT TERM; \
		(cd backend && ../$(PY) -m uvicorn main:app --reload --port 8000) & \
		(cd frontend && npm run dev) & \
		wait

backend:  ## Run the API only
	cd backend && ../$(PY) -m uvicorn main:app --reload --port 8000

frontend:  ## Run the web app only
	cd frontend && npm run dev

test:  ## Run the backend test suite
	cd backend && ../$(PY) -m pytest tests/ -v

build:  ## Production build of the frontend (also typechecks)
	cd frontend && npm run build

clean:  ## Remove caches and build artifacts
	find . -type d -name __pycache__ -not -path "*/venv/*" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache backend/.pytest_cache frontend/.next
	@echo "Cleaned."
