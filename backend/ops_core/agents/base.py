"""
O.P.S. Canonical Base Agent Contract
Every specialized agent implements this interface.
Agents only execute through registered capabilities.
"""

import abc
import logging
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from ops_core.capabilities.schemas import ToolCallResult
from ops_core.tools.executor import ToolExecutor
from ops_core.services.ollama_service import OPSOllamaService

logger = logging.getLogger("ops.agents.base")


class AgentResult(BaseModel):
    status: str = "SUCCESS"                  # "SUCCESS", "PARTIAL", "FAILED", "DECLINED"
    agent_name: str
    summary: str
    evidence: Dict[str, Any] = Field(default_factory=dict)
    artifacts: List[Dict[str, Any]] = Field(default_factory=list)
    error: Optional[str] = None


class BaseAgent(abc.ABC):
    name: str = "BaseAgent"
    description: str = ""
    assigned_model: str = "Qwen3 1.7B"
    allowed_capabilities: List[str] = []

    def __init__(self, ollama_service: Optional[OPSOllamaService] = None, executor: Optional[ToolExecutor] = None):
        self.ollama = ollama_service or OPSOllamaService()
        self.executor = executor or ToolExecutor()

    @abc.abstractmethod
    async def process(self, directive: str, context: Optional[Dict[str, Any]] = None) -> AgentResult:
        """Processes the directive using only allowed capabilities."""
        pass
