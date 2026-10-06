"""
O.P.S. Base Agent Definition & Strict Contract
Enforces the Golden Rule:
1. One primary responsibility per agent.
2. Defined input.
3. Defined output.
4. Defined allowed tools.
5. Defined model assignment.
6. Defined failure behavior.
7. Defined parent/superior agent.
8. Defined downstream destination.
"""

import time
import logging
from typing import Dict, Any, List, Optional, TypedDict
from ops_core.services.event_bus import OPSEventBus
from ops_core.services.ollama_service import OPSOllamaService

logger = logging.getLogger("ops.agents.base")


class AgentTaskState(TypedDict, total=False):
    task_id: str
    session_id: str
    prompt: str
    original_prompt: str
    
    # Core interpretation
    template_data: Dict[str, Any]
    route_domain: str  # "WEB" or "AUTOMATION"
    
    # Web tree state
    web_understanding: Dict[str, Any]
    web_raw_results: List[Dict[str, Any]]
    web_retrieval_validation: Dict[str, Any]
    web_loop_count: int
    web_gap_feedback: Optional[str]
    
    # Automation tree state
    automation_understanding: Dict[str, Any]
    action_plan: List[str]
    hitl_decision: str  # "ACCEPTED", "DECLINED", "PENDING"
    hitl_reason: str
    target_automation_domain: str  # "OPEN_WEB", "INSTALLED_APPS", "OPEN_FILE", "DESKTOP_CONTROL"
    automation_execution_result: Dict[str, Any]
    
    # Execution & Result structures
    actions_completed: List[str]
    actions_failed: List[str]
    raw_facts: Dict[str, Any]
    result_type: str  # "INFORMATION_RESULT", "AUTOMATION_RESULT", "FILE_RESULT", "SYSTEM_RESULT", "RESEARCH_RESULT", "PARTIAL_RESULT", "FAILURE_RESULT"
    structured_result: str
    
    # Final Jarvis Communication
    final_jarvis_speech: str
    
    # Telemetry
    active_agent: str
    active_model: str
    status: str
    error: Optional[str]
    execution_log: List[Dict[str, Any]]


class BaseOPSAgent:
    """
    Abstract Base Class for all 14 O.P.S. Agents.
    Provides structured lifecycle, strict state contracts, logging, and real-time event streaming.
    """

    agent_id: str = "base_agent"
    agent_name: str = "Base Agent"
    level: str = "Sub-agent"  # "Core", "Superior", "Sub-agent", "Final processing", "Control"
    assigned_model: str = "Qwen3 0.6B"
    allowed_tools: List[str] = []
    parent_agent: Optional[str] = None
    downstream_destination: Optional[str] = None

    def __init__(self, ollama_service: Optional[OPSOllamaService] = None):
        self.ollama = ollama_service or OPSOllamaService()

    async def emit_thought(self, task_id: str, thought: str, step: int = 1):
        """Emits real-time cognitive reasoning over WebSockets for Cockpit & Live Topology."""
        logger.info(f"[{self.agent_name}] Thought: {thought}")
        try:
            await OPSEventBus.emit_agent_thought_async(
                thought=thought,
                agent=self.agent_name,
                step=step,
                task_id=task_id
            )
        except Exception as e:
            logger.debug(f"Failed to emit thought: {e}")

    async def emit_status(self, task_id: str, status: str, details: Optional[Dict[str, Any]] = None):
        """Emits agent lifecycle status over WebSockets."""
        logger.info(f"[{self.agent_name}] Status: {status}")
        try:
            await OPSEventBus.emit_agent_status_async(
                agent=self.agent_name,
                status=status,
                details=details or {},
                task_id=task_id
            )
        except Exception as e:
            logger.debug(f"Failed to emit status: {e}")

    def validate_input(self, state: AgentTaskState) -> bool:
        """Validates that prerequisite fields exist in state."""
        return True

    def validate_output(self, result: Dict[str, Any]) -> bool:
        """Validates that output schema conforms to requirements."""
        return True

    async def process(self, state: AgentTaskState) -> Dict[str, Any]:
        """
        Cognitive execution method. Must be overridden by subclasses.
        Returns a dictionary of state updates.
        """
        raise NotImplementedError(f"{self.__class__.__name__} must implement process()")
