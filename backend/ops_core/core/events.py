"""
O.P.S. Canonical System Events
Defines standard structured events emitted across the entire agent runtime,
WebSockets, Pop-up Cockpit, and Agents UI.
"""

from enum import Enum
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
import time
import uuid


class OPSEventType(str, Enum):
    # Session lifecycle
    SESSION_CREATED = "SESSION_CREATED"
    SESSION_RESET = "SESSION_RESET"
    SESSION_STOPPED = "SESSION_STOPPED"
    SESSION_PAUSED = "SESSION_PAUSED"

    # User input
    USER_INPUT_RECEIVED = "USER_INPUT_RECEIVED"

    # Router
    ROUTER_STARTED = "ROUTER_STARTED"
    ROUTER_COMPLETED = "ROUTER_COMPLETED"

    # Supervisor
    SUPERVISOR_STARTED = "SUPERVISOR_STARTED"
    SUPERVISOR_COMPLETED = "SUPERVISOR_COMPLETED"

    # Mission lifecycle
    MISSION_CREATED = "MISSION_CREATED"
    MISSION_STARTED = "MISSION_STARTED"
    MISSION_COMPLETED = "MISSION_COMPLETED"
    MISSION_FAILED = "MISSION_FAILED"
    MISSION_PAUSED = "MISSION_PAUSED"
    MISSION_CANCELLED = "MISSION_CANCELLED"

    # Plan
    PLAN_CREATED = "PLAN_CREATED"
    PLAN_UPDATED = "PLAN_UPDATED"

    # Agent lifecycle
    AGENT_SELECTED = "AGENT_SELECTED"
    AGENT_STARTED = "AGENT_STARTED"
    AGENT_THINKING = "AGENT_THINKING"
    AGENT_WAITING = "AGENT_WAITING"
    AGENT_COMPLETED = "AGENT_COMPLETED"
    AGENT_FAILED = "AGENT_FAILED"
    AGENT_PAUSED = "AGENT_PAUSED"

    # Capability & Tool execution
    CAPABILITY_SELECTED = "CAPABILITY_SELECTED"
    TOOL_REQUESTED = "TOOL_REQUESTED"
    TOOL_STARTED = "TOOL_STARTED"
    TOOL_COMPLETED = "TOOL_COMPLETED"
    TOOL_FAILED = "TOOL_FAILED"

    # Safety & Approvals
    APPROVAL_REQUIRED = "APPROVAL_REQUIRED"
    APPROVAL_GRANTED = "APPROVAL_GRANTED"
    APPROVAL_DENIED = "APPROVAL_DENIED"

    # Verification & Ground Truth
    VERIFICATION_STARTED = "VERIFICATION_STARTED"
    VERIFICATION_PASSED = "VERIFICATION_PASSED"
    VERIFICATION_FAILED = "VERIFICATION_FAILED"

    # Recovery & Self-Healing
    RECOVERY_STARTED = "RECOVERY_STARTED"
    REPLAN_STARTED = "REPLAN_STARTED"
    RETRY_STARTED = "RETRY_STARTED"

    # RAG / Knowledge
    RAG_SEARCH_STARTED = "RAG_SEARCH_STARTED"
    RAG_SEARCH_COMPLETED = "RAG_SEARCH_COMPLETED"
    RAG_SEARCH_FAILED = "RAG_SEARCH_FAILED"

    # Web Research
    WEB_SEARCH_STARTED = "WEB_SEARCH_STARTED"
    WEB_SEARCH_COMPLETED = "WEB_SEARCH_COMPLETED"

    # Response Engine
    RESPONSE_STARTED = "RESPONSE_STARTED"
    RESPONSE_COMPLETED = "RESPONSE_COMPLETED"

    # Error
    ERROR_OCCURRED = "ERROR_OCCURRED"


class AgentInfo(BaseModel):
    id: str
    name: str
    type: str = "specialist"                 # "core", "supervisor", "planner", "specialist", "verifier", "response"
    model: Optional[str] = None


class StructuredOPSEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: f"evt_{uuid.uuid4().hex[:8]}")
    timestamp: float = Field(default_factory=time.time)
    session_id: str = "default"
    task_id: Optional[str] = None
    mission_id: Optional[str] = None
    event_type: OPSEventType
    agent: Optional[AgentInfo] = None
    parent_agent: Optional[str] = None
    status: str = "RUNNING"                  # "IDLE", "RUNNING", "COMPLETED", "FAILED", "WAITING", "PAUSED", "RECOVERING"
    message: str = ""
    capability: Optional[str] = None
    tool: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


def create_event(
    event_type: OPSEventType,
    session_id: str = "default",
    task_id: Optional[str] = None,
    mission_id: Optional[str] = None,
    agent_id: Optional[str] = None,
    agent_name: Optional[str] = None,
    parent_agent: Optional[str] = None,
    status: str = "RUNNING",
    message: str = "",
    capability: Optional[str] = None,
    tool: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    agent_info = None
    if agent_id or agent_name:
        agent_info = AgentInfo(
            id=(agent_id or agent_name or "").lower().replace(" ", "_"),
            name=agent_name or agent_id or "Agent"
        )

    evt = StructuredOPSEvent(
        session_id=session_id,
        task_id=task_id,
        mission_id=mission_id,
        event_type=event_type,
        agent=agent_info,
        parent_agent=parent_agent,
        status=status,
        message=message,
        capability=capability,
        tool=tool,
        metadata=metadata or {}
    )
    return evt.model_dump()
