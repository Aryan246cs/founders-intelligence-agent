from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Any, Dict, Optional
from enum import Enum
from datetime import datetime


class AgentType(str, Enum):
    COMPETITOR_MONITOR = "competitor_monitor"
    RESEARCH = "research"
    BRIEFING = "briefing"
    MEMORY = "memory"
    PLANNER = "planner"
    ORCHESTRATOR = "orchestrator"


class AgentStatus(str, Enum):
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class AgentTask(BaseModel):
    id: Optional[str] = None
    agent_type: AgentType
    input: Dict[str, Any]
    status: AgentStatus = AgentStatus.IDLE
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class AgentTaskCreate(BaseModel):
    agent_type: AgentType
    input: Dict[str, Any] = Field(default_factory=dict)
