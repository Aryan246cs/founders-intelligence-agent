from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from db.queries import AgentTaskQueries, ExecutionLogQueries
from services.job_tracker import NULL_REPORTER, ProgressReporter
from utils.logger import get_logger

logger = get_logger(__name__)


class BaseAgent(ABC):
    """Abstract base class for all agents.

    Handles the three cross-cutting concerns every agent needs so subclasses
    only contain domain logic:
      1. task lifecycle — a row in `agent_tasks` per run, status transitions
      2. logging — structured logs plus a durable row in `execution_logs`
      3. progress — optional step reporting into the in-process job tracker
    """

    agent_type: str = "base"

    def __init__(self, progress: Optional[ProgressReporter] = None) -> None:
        self.task_id: Optional[str] = None
        self.progress: ProgressReporter = progress or NULL_REPORTER

    async def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a task record, execute, and persist the result."""
        task = AgentTaskQueries.create(self.agent_type, input_data)
        self.task_id = task["id"]

        self._log("info", f"Agent {self.agent_type} started")
        AgentTaskQueries.update_status(self.task_id, "running")

        try:
            result = await self.execute(input_data)
            AgentTaskQueries.update_status(self.task_id, "completed", result=result)
            self._log("info", f"Agent {self.agent_type} completed")
            return result
        except Exception as e:
            error_msg = str(e)
            AgentTaskQueries.update_status(self.task_id, "failed", error=error_msg)
            self._log("error", f"Agent {self.agent_type} failed: {error_msg}")
            raise

    @abstractmethod
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Implement agent-specific logic here."""
        ...

    def _log(self, level: str, message: str, metadata: Optional[dict] = None) -> None:
        ExecutionLogQueries.log(
            task_id=self.task_id,
            agent_type=self.agent_type,
            level=level,
            message=message,
            metadata=metadata,
        )
        getattr(logger, level)(message, task_id=self.task_id, agent=self.agent_type)

    def _step(self, key: str, message: str, metadata: Optional[dict] = None) -> None:
        """Mark a tracked step as running and log the same message.

        One call keeps the activity feed and the live progress UI in sync — they
        can never drift apart because they are fed from the same statement.
        """
        self.progress.start(key, message)
        self._log("info", message, metadata)
