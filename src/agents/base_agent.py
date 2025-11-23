"""Base agent class that all agents inherit from."""

import time
from abc import ABC, abstractmethod
from typing import Any, Optional

from loguru import logger

from src.database.connection import get_db
from src.database.models import AgentLog


class BaseAgent(ABC):
    """
    Base class for all AI agents in the system.

    All agents should inherit from this class and implement the execute() method.
    """

    def __init__(self, name: str):
        """
        Initialize the agent.

        Args:
            name: The name of the agent (e.g., "MarketScannerAgent")
        """
        self.name = name
        logger.info(f"{self.name} initialized")

    @abstractmethod
    async def execute(self, *args, **kwargs) -> Any:
        """
        Main execution method for the agent.

        This method should be implemented by all subclasses.
        """

    async def run(self, *args, **kwargs) -> Any:
        """
        Wrapper method that handles logging and error handling.

        This method should be called instead of execute() directly.
        """
        start_time = time.time()
        action = kwargs.get("action", "execute")

        logger.info(f"{self.name} starting: {action}")

        try:
            result = await self.execute(*args, **kwargs)
            execution_time = time.time() - start_time

            # Log successful execution
            self._log_activity(
                action=action,
                status="success",
                details={"result_summary": str(result)[:500]},
                execution_time=execution_time
            )

            logger.info(
                f"{self.name} completed: {action} "
                f"(took {execution_time:.2f}s)"
            )

            return result

        except Exception as e:
            execution_time = time.time() - start_time
            error_message = str(e)

            # Log failed execution
            self._log_activity(
                action=action,
                status="error",
                error_message=error_message,
                execution_time=execution_time
            )

            logger.error(
                f"{self.name} failed: {action} - {error_message} "
                f"(took {execution_time:.2f}s)"
            )

            raise

    def _log_activity(
        self,
        action: str,
        status: str,
        details: Optional[dict] = None,
        error_message: Optional[str] = None,
        execution_time: Optional[float] = None
    ):
        """
        Log agent activity to the database.

        Args:
            action: The action being performed
            status: success, error, or warning
            details: Additional details about the action
            error_message: Error message if status is error
            execution_time: Time taken to execute in seconds
        """
        try:
            with get_db() as db:
                log_entry = AgentLog(
                    agent_name=self.name,
                    action=action,
                    status=status,
                    details=details or {},
                    error_message=error_message,
                    execution_time=execution_time
                )
                db.add(log_entry)
                db.commit()
        except Exception as e:
            # Don't let logging errors break the agent
            logger.warning(f"Failed to log activity: {e}")

    def log_info(self, message: str):
        """Log an info message."""
        logger.info(f"[{self.name}] {message}")

    def log_warning(self, message: str):
        """Log a warning message."""
        logger.warning(f"[{self.name}] {message}")

    def log_error(self, message: str):
        """Log an error message."""
        logger.error(f"[{self.name}] {message}")
