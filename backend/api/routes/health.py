"""
Health and dependency checks.

GET /health           — liveness. Is the API process up? Never touches the network.
GET /health/services  — readiness. Can we actually reach Supabase, Groq, Apify, Slack?

The split matters: a container orchestrator restarting the app because Groq is
rate-limiting would be wrong, so liveness stays local. The UI uses the readiness
probe to show which integrations are genuinely connected instead of hardcoding
five green dots.
"""

from __future__ import annotations

import asyncio
from typing import Any, Dict

from fastapi import APIRouter

from config import settings
from utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()

# Each probe is capped so one hanging dependency cannot stall the whole check.
PROBE_TIMEOUT_SECONDS = 6.0


def _result(
    name: str, ok: bool, detail: str, configured: bool = True
) -> Dict[str, Any]:
    return {
        "name": name,
        "status": "connected" if ok else ("error" if configured else "not_configured"),
        "ok": ok,
        "configured": configured,
        "detail": detail,
    }


def _check_supabase_sync() -> Dict[str, Any]:
    from db.client import get_supabase

    try:
        db = get_supabase()
        res = db.table("briefings").select("id", count="exact").limit(1).execute()
        return _result("Supabase", True, f"{res.count or 0} briefings stored")
    except Exception as e:
        msg = str(e)
        # The most common failure by far: a free-tier project paused for
        # inactivity stops resolving in DNS. Say so instead of leaking a raw
        # socket error that looks like a code bug.
        if "nodename nor servname" in msg or "Name or service not known" in msg:
            return _result(
                "Supabase",
                False,
                "Host does not resolve — the project is likely paused. Resume it in the Supabase dashboard.",
            )
        return _result("Supabase", False, msg[:180])


def _check_groq_sync() -> Dict[str, Any]:
    if not settings.groq_api_key:
        return _result("Groq", False, "GROQ_API_KEY not set", configured=False)
    try:
        from groq import Groq

        client = Groq(api_key=settings.groq_api_key)
        models = client.models.list()
        available = {m.id for m in models.data}
        if settings.groq_model not in available:
            return _result(
                "Groq",
                False,
                f"Model '{settings.groq_model}' is not available on this account",
            )
        return _result("Groq", True, f"Model {settings.groq_model} ready")
    except Exception as e:
        msg = str(e)
        if "invalid_api_key" in msg or "401" in msg or "Authentication" in msg:
            return _result(
                "Groq", False, "API key rejected — generate a new key at console.groq.com"
            )
        return _result("Groq", False, msg[:180])


def _check_apify_sync() -> Dict[str, Any]:
    if not settings.apify_api_token:
        return _result("Apify", False, "APIFY_API_TOKEN not set", configured=False)
    try:
        from apify_client import ApifyClient

        user = ApifyClient(settings.apify_api_token).user("me").get() or {}
        return _result("Apify", True, f"Authenticated as {user.get('username', 'user')}")
    except Exception as e:
        return _result("Apify", False, str(e)[:180])


def _check_slack() -> Dict[str, Any]:
    url = settings.slack_webhook_url or ""
    if not url or "your/webhook" in url:
        return _result(
            "Slack",
            False,
            "No webhook configured — deliveries are skipped",
            configured=False,
        )
    # Deliberately not posting: any request to a webhook puts a message in a
    # real channel. Configuration presence is what the UI needs to know.
    return _result("Slack", True, "Webhook configured")


def _check_n8n() -> Dict[str, Any]:
    url = settings.n8n_webhook_base_url or ""
    if not url:
        return _result("n8n", False, "No webhook base URL set", configured=False)
    return _result("n8n", True, f"Webhook base {url}")


async def _with_timeout(fn, name: str) -> Dict[str, Any]:
    """Run a blocking probe off the event loop with a hard timeout."""
    try:
        return await asyncio.wait_for(
            asyncio.to_thread(fn), timeout=PROBE_TIMEOUT_SECONDS
        )
    except asyncio.TimeoutError:
        return _result(name, False, f"Timed out after {PROBE_TIMEOUT_SECONDS:.0f}s")
    except Exception as e:
        return _result(name, False, str(e)[:180])


@router.get("")
@router.get("/")
async def health_check():
    """Liveness — process is up and serving. No external calls."""
    return {"status": "ok", "env": settings.app_env, "version": "1.1.0"}


@router.get("/services")
async def services_health():
    """Readiness — probes every external dependency in parallel."""
    supabase, groq, apify = await asyncio.gather(
        _with_timeout(_check_supabase_sync, "Supabase"),
        _with_timeout(_check_groq_sync, "Groq"),
        _with_timeout(_check_apify_sync, "Apify"),
    )
    services = [supabase, groq, apify, _check_slack(), _check_n8n()]

    # Supabase and Groq are load-bearing: without them no pipeline can complete.
    critical = [s for s in services if s["name"] in ("Supabase", "Groq")]
    degraded = [s for s in services if s["configured"] and not s["ok"]]

    if any(not s["ok"] for s in critical):
        overall = "down"
    elif degraded:
        overall = "degraded"
    else:
        overall = "healthy"

    return {
        "status": overall,
        "env": settings.app_env,
        "services": services,
        "healthy_count": sum(1 for s in services if s["ok"]),
        "total_count": len(services),
    }
