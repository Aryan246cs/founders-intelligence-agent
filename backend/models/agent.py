from pydantic import BaseModel, Field
from typing import Optional, Any
from enum import Enum
from datetime import datetime


class AgentType(str, Enum):
    COMPETITOR_MONITOR = "competitor_monitor"
    RESEARCH = "research"
    BRIEFING = "briefing"
    MEMORY = "memory"
    ORCHESTRATOR = "orchestrator"


class AgentStatus(str, Enum):
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class AgentTask(BaseModel):
    id: Optional[str] = None
    agent_type: AgentType
    input: dict[str, Any]
    status: AgentStatus = AgentStatus.IDLE
    result: Optional[dict[str, Any]] = None
    error: Optional[str] = None
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class AgentTaskCreate(BaseModel):
    agent_type: AgentType
    input: dict[str, Any] = Field(default_factory=dict)


class AgentTaskResponse(AgentTask):
    pass
