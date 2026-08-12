#!/usr/bin/env python
"""
Preflight check — run this before a demo.

    cd backend && ./venv/bin/python scripts/doctor.py

Verifies, in order of how badly it breaks the demo:
  1. .env is complete
  2. Supabase resolves, authenticates, and has all 7 tables
  3. Groq accepts the key and serves the configured model
  4. Apify accepts the token
  5. Slack webhook is configured (not called — that would post a real message)

Exits non-zero if anything the pipeline needs is broken.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Allow running as `python scripts/doctor.py` from the backend directory.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

GREEN, RED, YELLOW, DIM, RESET = (
    "\033[32m",
    "\033[31m",
    "\033[33m",
    "\033[2m",
    "\033[0m",
)

REQUIRED_TABLES = [
    "agent_tasks",
    "research_findings",
    "briefings",
    "memory_entries",
    "execution_logs",
    "competitor_snapshots",
    "workflow_executions",
    "startup_research_reports",
]

failures: list[str] = []
warnings: list[str] = []


def ok(label: str, detail: str = "") -> None:
    print(f"  {GREEN}✓{RESET} {label}" + (f" {DIM}— {detail}{RESET}" if detail else ""))


def bad(label: str, detail: str, fix: str) -> None:
    print(f"  {RED}✗{RESET} {label} {DIM}— {detail}{RESET}")
    print(f"    {YELLOW}fix:{RESET} {fix}")
    failures.append(label)


def warn(label: str, detail: str) -> None:
    print(f"  {YELLOW}!{RESET} {label} {DIM}— {detail}{RESET}")
    warnings.append(label)


def check_env() -> object:
    print(f"\n{DIM}config{RESET}")
    try:
        from config import settings
    except Exception as e:
        bad(
            "backend/.env",
            str(e)[:120],
            "copy .env.example to .env and fill in Supabase, Groq and Apify keys",
        )
        sys.exit(1)
    ok(".env loaded", f"env={settings.app_env}, model={settings.groq_model}")
    return settings


def check_supabase(settings) -> None:
    print(f"\n{DIM}supabase{RESET}")
    import socket
    from urllib.parse import urlparse

    host = urlparse(settings.supabase_url).hostname or ""
    try:
        socket.gethostbyname(host)
    except OSError:
        bad(
            "DNS",
            f"{host} does not resolve",
            "the project is paused or deleted — open supabase.com/dashboard and click Restore, "
            "then update SUPABASE_URL and the keys in backend/.env if the project changed",
        )
        return
    ok("DNS", host)

    from db.client import get_supabase

    try:
        db = get_supabase()
    except Exception as e:
        bad("client", str(e)[:120], "check SUPABASE_SERVICE_ROLE_KEY in backend/.env")
        return

    missing = []
    for table in REQUIRED_TABLES:
        try:
            res = db.table(table).select("id", count="exact").limit(1).execute()
            ok(f"table {table}", f"{res.count or 0} rows")
        except Exception as e:
            missing.append(table)
            bad(
                f"table {table}",
                str(e)[:90],
                "run backend/db/migrations/*.sql in the Supabase SQL editor, in order",
            )
    if not missing:
        ok("schema", f"all {len(REQUIRED_TABLES)} tables present")


def check_groq(settings) -> None:
    print(f"\n{DIM}groq{RESET}")
    try:
        from groq import Groq

        client = Groq(api_key=settings.groq_api_key)
        available = {m.id for m in client.models.list().data}
    except Exception as e:
        msg = str(e)
        if "invalid_api_key" in msg or "401" in msg or "Authentication" in msg:
            bad(
                "auth",
                "API key rejected",
                "create a new key at console.groq.com/keys and set GROQ_API_KEY in backend/.env",
            )
        else:
            bad("auth", msg[:120], "check network access and GROQ_API_KEY")
        return
    ok("auth", f"{len(available)} models available")

    if settings.groq_model in available:
        ok(f"model {settings.groq_model}", "ready")
    else:
        suggestions = sorted(m for m in available if "llama" in m and "70b" in m)
        bad(
            f"model {settings.groq_model}",
            "not available on this account",
            "set GROQ_MODEL in backend/.env to one of: "
            + (", ".join(suggestions[:3]) or "a model listed at console.groq.com/docs/models"),
        )


def check_apify(settings) -> None:
    print(f"\n{DIM}apify{RESET}")
    try:
        from apify_client import ApifyClient

        user = ApifyClient(settings.apify_api_token).user("me").get() or {}
        ok("auth", f"user {user.get('username', '?')}")
    except Exception as e:
        bad(
            "auth",
            str(e)[:120],
            "check APIFY_API_TOKEN in backend/.env (console.apify.com → Settings → Integrations)",
        )


def check_optional(settings) -> None:
    print(f"\n{DIM}optional{RESET}")
    url = settings.slack_webhook_url or ""
    if url and "your/webhook" not in url:
        ok("slack webhook", "configured (not called)")
    else:
        warn("slack webhook", "not configured — Slack delivery will be skipped")

    if settings.n8n_webhook_base_url:
        ok("n8n base url", settings.n8n_webhook_base_url)
    else:
        warn("n8n base url", "not set — scheduled workflows disabled")


def main() -> int:
    print("Founder Intelligence Agent — preflight check")
    settings = check_env()
    check_supabase(settings)
    check_groq(settings)
    check_apify(settings)
    check_optional(settings)

    print()
    if failures:
        print(f"{RED}{len(failures)} blocking issue(s):{RESET} {', '.join(failures)}")
        print("The demo will not work until these are fixed.")
        return 1
    if warnings:
        print(f"{GREEN}Core services healthy.{RESET} {len(warnings)} optional warning(s).")
        return 0
    print(f"{GREEN}All systems go.{RESET}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
