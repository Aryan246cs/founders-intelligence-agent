from abc import ABC, abstractmethod
from typing import Any
from datetime import datetime, timezone

from db.queries import AgentTaskQueries, ExecutionLogQueries
from utils.logger import get_logger

logger = get_logger(__name__)


class BaseAgent(ABC):
    """Abstract base class for all agents."""

    agent_type: str = "base"

    def __init__(self):
        self.task_id: str | None = None

    async def run(self, input_data: dict) -> dict:
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
    async def execute(self, input_data: dict) -> dict:
        """Implement agent-specific logic here."""
        ...

    def _log(self, level: str, message: str, metadata: dict = None):
        ExecutionLogQueries.log(
            task_id=self.task_id,
            agent_type=self.agent_type,
            level=level,
            message=message,
            metadata=metadata,
        )
        getattr(logger, level)(message, task_id=self.task_id, agent=self.agent_type)
