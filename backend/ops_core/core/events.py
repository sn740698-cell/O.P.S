"""
O.P.S. Canonical System Events
Defines structured events emitted across the entire agent runtime,
WebSockets, and Pop-up Cockpit interfaces.
"""

from enum import Enum
from typing import Dict, Any, Optional
import time


class OPSEventType(str, Enum):
    # Session lifecycle
    SESSION_CREATED = "SESSION_CREATED"
    SESSION_RESET = "SESSION_RESET"
    SESSION_PAUSED = "SESSION_PAUSED"
    SESSION_STOPPED = "SESSION_STOPPED"
    
    # Task / Mission lifecycle
    TASK_CREATED = "TASK_CREATED"
    ROUTED = "ROUTED"
    MISSION_CREATED = "MISSION_CREATED"
    PLAN_CREATED = "PLAN_CREATED"
    STEP_STARTED = "STEP_STARTED"
    STEP_COMPLETED = "STEP_COMPLETED"
    STEP_FAILED = "STEP_FAILED"
    
    # Agent lifecycle
    AGENT_STARTED = "AGENT_STARTED"
    AGENT_THOUGHT = "AGENT_THOUGHT"
    AGENT_COMPLETED = "AGENT_COMPLETED"
    
    # Capability & Tool execution
    TOOL_REQUESTED = "TOOL_REQUESTED"
    APPROVAL_REQUIRED = "APPROVAL_REQUIRED"
    APPROVAL_RESOLVED = "APPROVAL_RESOLVED"
    TOOL_STARTED = "TOOL_STARTED"
    TOOL_COMPLETED = "TOOL_COMPLETED"
    TOOL_FAILED = "TOOL_FAILED"
    
    # Verification & Recovery
    VERIFICATION_STARTED = "VERIFICATION_STARTED"
    VERIFICATION_PASSED = "VERIFICATION_PASSED"
    VERIFICATION_FAILED = "VERIFICATION_FAILED"
    RECOVERY_STARTED = "RECOVERY_STARTED"
    
    # Final states
    MISSION_COMPLETED = "MISSION_COMPLETED"
    MISSION_FAILED = "MISSION_FAILED"
    RESPONSE_READY = "RESPONSE_READY"


def create_event(
    event_type: OPSEventType,
    session_id: str,
    task_id: Optional[str] = None,
    mission_id: Optional[str] = None,
    agent: Optional[str] = None,
    payload: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    return {
        "event": event_type.value,
        "session_id": session_id,
        "task_id": task_id,
        "mission_id": mission_id,
        "agent": agent,
        "timestamp": time.time(),
        "payload": payload or {}
    }
