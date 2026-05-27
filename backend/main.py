from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from api.routes import agents, research, briefings, memory, workflows
from api.routes import activity, dashboard, memory_comparisons
from utils.logger import get_logger, configure_logging
from config import settings

configure_logging()
logger = get_logger(__name__)

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[f"{settings.rate_limit_per_minute}/minute"],
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Founder Intelligence Agent starting", env=settings.app_env)
    yield
    logger.info("Founder Intelligence Agent shutting down")


app = FastAPI(
    title="Founder Intelligence Agent",
    description="Autonomous multi-agent platform for startup founders",
    version="1.0.0",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(agents.router, prefix="/api/agents", tags=["agents"])
app.include_router(research.router, prefix="/api/research", tags=["research"])
app.include_router(briefings.router, prefix="/api/briefings", tags=["briefings"])
app.include_router(memory.router, prefix="/api/memory", tags=["memory"])
app.include_router(workflows.router, prefix="/api/workflows", tags=["workflows"])
app.include_router(activity.router, prefix="/api/activity", tags=["activity"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["dashboard"])
app.include_router(memory_comparisons.router, prefix="/api/memory", tags=["memory"])


@app.get("/health", tags=["health"])
async def health_check():
    return {"status": "ok", "env": settings.app_env, "version": "1.0.0"}
