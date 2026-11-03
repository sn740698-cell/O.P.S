"""
O.P.S. 2.0 Central LangGraph Agent Helpers
Provides structured event emission and telemetry for all 13 specialized components.
"""

import time
import logging
from typing import Dict, Any, Optional
from research_system.events.event_bus import EventBus
from research_system.orchestrator.state import CentralGraphState

logger = logging.getLogger("OPS.Orchestrator.Agents")
event_bus = EventBus()


AGENT_TO_CANONICAL_STAGE = {
    "global_intent_router": "Classifying intent",
    "task_understanding_planner": "Understanding request",
    "local_reasoning_agent": "Generating answer",
    "web_research_agent": "Searching external web",
    "evidence_validation_agent": "Validating evidence",
    "answer_synthesis_agent": "Synthesizing verified answer",
    "automation_planner": "Formulating automation plan",
    "hitl_safety_controller": "Evaluating safety policy",
    "desktop_automation_executor": "Executing desktop actions",
    "browser_automation_executor": "Interacting with web elements",
    "verification_recovery_agent": "Verifying execution outcome",
    "composite_task_coordinator": "Coordinating cross-engine plan",
    "result_formatter_agent": "Completing response"
}


def emit_agent_started(state: CentralGraphState, agent_id: str, agent_name: str, group_id: str, component_type: str, summary: str):
    """Notifies frontend that an agent has transitioned to ACTIVE."""
    now = time.time()
    req_id = state.get("request_id") or f"req_{state.get('task_id', 'task')}"
    task_id = state.get("task_id", "task")
    conv_id = state.get("conversation_id")
    active_engine = state.get("active_engine") or ("AUTOMATION" if "automation" in agent_id or group_id == "automation_engine" else "ANSWERING")
    response_mode = state.get("response_mode") or state.get("automation_mode") or state.get("answering_mode") or "LLM"
    canonical_stage = AGENT_TO_CANONICAL_STAGE.get(agent_id, summary)

    event_bus.publish(
        request_id=req_id,
        execution_id=task_id,
        conversation_id=conv_id,
        node_id=agent_id,
        component_name=agent_name,
        component_type=component_type,
        event_type="AGENT_STARTED",
        execution_status="ACTIVE",
        safe_task_summary=summary,
        agent_id=agent_id,
        agent_name=agent_name,
        group_id=group_id,
        status="ACTIVE",
        active_engine=active_engine,
        response_mode=response_mode,
        current_stage=canonical_stage,
        timestamp=now
    )


def emit_agent_progress(state: CentralGraphState, agent_id: str, agent_name: str, group_id: str, summary: str, thought: Optional[str] = None):
    """Emits incremental progress / thought updates for the active agent."""
    now = time.time()
    req_id = state.get("request_id") or f"req_{state.get('task_id', 'task')}"
    task_id = state.get("task_id", "task")
    conv_id = state.get("conversation_id")
    active_engine = state.get("active_engine") or ("AUTOMATION" if "automation" in agent_id or group_id == "automation_engine" else "ANSWERING")
    response_mode = state.get("response_mode") or state.get("automation_mode") or state.get("answering_mode") or "LLM"
    canonical_stage = AGENT_TO_CANONICAL_STAGE.get(agent_id, summary)

    event_bus.publish(
        request_id=req_id,
        execution_id=task_id,
        conversation_id=conv_id,
        node_id=agent_id,
        component_name=agent_name,
        component_type="execution_worker",
        event_type="AGENT_PROGRESS",
        execution_status="ACTIVE",
        safe_task_summary=summary,
        safe_output_summary=thought,
        agent_id=agent_id,
        agent_name=agent_name,
        group_id=group_id,
        status="ACTIVE",
        active_engine=active_engine,
        response_mode=response_mode,
        current_stage=canonical_stage,
        timestamp=now
    )


def emit_agent_completed(state: CentralGraphState, agent_id: str, agent_name: str, group_id: str, component_type: str, summary: str, output_summary: Optional[str] = None, duration_s: Optional[float] = None):
    """Notifies frontend that an agent has completed its execution successfully."""
    now = time.time()
    req_id = state.get("request_id") or f"req_{state.get('task_id', 'task')}"
    task_id = state.get("task_id", "task")
    conv_id = state.get("conversation_id")
    active_engine = state.get("active_engine") or ("AUTOMATION" if "automation" in agent_id or group_id == "automation_engine" else "ANSWERING")
    response_mode = state.get("response_mode") or state.get("automation_mode") or state.get("answering_mode") or "LLM"
    canonical_stage = AGENT_TO_CANONICAL_STAGE.get(agent_id, summary)

    event_bus.publish(
        request_id=req_id,
        execution_id=task_id,
        conversation_id=conv_id,
        node_id=agent_id,
        component_name=agent_name,
        component_type=component_type,
        event_type="AGENT_COMPLETED",
        execution_status="COMPLETED",
        safe_task_summary=summary,
        safe_output_summary=output_summary,
        agent_id=agent_id,
        agent_name=agent_name,
        group_id=group_id,
        status="COMPLETED",
        active_engine=active_engine,
        response_mode=response_mode,
        current_stage=canonical_stage,
        duration_s=duration_s,
        timestamp=now
    )


def emit_agent_skipped(state: CentralGraphState, agent_id: str, agent_name: str, group_id: str, reason: str):
    """Notifies frontend that an agent was evaluated and skipped for this workflow."""
    now = time.time()
    req_id = state.get("request_id") or f"req_{state.get('task_id', 'task')}"
    task_id = state.get("task_id", "task")
    conv_id = state.get("conversation_id")

    event_bus.publish(
        request_id=req_id,
        execution_id=task_id,
        conversation_id=conv_id,
        node_id=agent_id,
        component_name=agent_name,
        component_type="execution_worker",
        event_type="AGENT_SKIPPED",
        execution_status="SKIPPED",
        safe_task_summary=reason,
        agent_id=agent_id,
        agent_name=agent_name,
        group_id=group_id,
        status="SKIPPED",
        timestamp=now
    )


def emit_agent_failed(state: CentralGraphState, agent_id: str, agent_name: str, group_id: str, error_msg: str):
    """Notifies frontend that an agent failed with error details."""
    now = time.time()
    req_id = state.get("request_id") or f"req_{state.get('task_id', 'task')}"
    task_id = state.get("task_id", "task")
    conv_id = state.get("conversation_id")

    event_bus.publish(
        request_id=req_id,
        execution_id=task_id,
        conversation_id=conv_id,
        node_id=agent_id,
        component_name=agent_name,
        component_type="execution_worker",
        event_type="AGENT_FAILED",
        execution_status="FAILED",
        safe_task_summary=f"Failed in {agent_name}: {error_msg}",
        error_details=error_msg,
        agent_id=agent_id,
        agent_name=agent_name,
        group_id=group_id,
        status="FAILED",
        timestamp=now
    )
