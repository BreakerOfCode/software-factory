"""
Base abstract class for LLM Engine adapters.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field


class EngineExecutionResult(BaseModel):
    """Execution telemetry returned by an engine cycle."""
    success: bool
    exit_code: int
    stdout: str
    stderr: str
    duration_seconds: float
    cost_usd: float = 0.0
    engine_name: str
    model_used: str
    error_message: Optional[str] = None


class BaseEngineAdapter(ABC):
    """Abstract interface for LLM CLI engines (Claude, Codex, etc.)."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config

    @abstractmethod
    def execute_cycle(
        self,
        prompt: str,
        project_dir: str,
        model: Optional[str] = None,
        timeout_seconds: int = 1800
    ) -> EngineExecutionResult:
        """Executes a single software factory development cycle."""
        pass
