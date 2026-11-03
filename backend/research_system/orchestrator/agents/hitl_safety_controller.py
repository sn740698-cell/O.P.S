"""
Agent 11: Human-in-the-Loop and Safety Controller
Group 3: Automation Engine (Global Safety Gate across all 4 Groups)
Mandatory centralized safety, approval, and clarification checkpoint.
Enforces authorization gates for consequential actions, ambiguous directives,
and coordinates LangGraph interrupt checkpoints.
"""

import time
import logging
from typing import Dict, Any
from research_system.orchestrator.state import CentralGraphState
from research_system.orchestrator.agents.base import emit_agent_started, emit_agent_completed, emit_agent_failed
from research_system.models import PendingApproval
from automation_system.safety.safety_policy import SafetyPolicy
from research_system.events.event_bus import EventBus

logger = logging.getLogger("OPS.Agent.HITLSafety")
event_bus = EventBus()

AGENT_ID = "hitl_safety_controller"
AGENT_NAME = "HITL & Safety Controller"
GROUP_ID = "automation_engine"
COMPONENT_TYPE = "approval_controller"


def hitl_safety_controller_node(state: CentralGraphState) -> Dict[str, Any]:
    """
    Agent 11 node: Evaluates request against safety policy.
    Pauses with approval requirement if destructive, or clarifies if ambiguous.
    """
    t0 = time.time()
    query = state.get("user_query", "").strip()
    task_type = state.get("task_type", "ANSWER")
    approval_status = state.get("approval_status", "NONE")
    req_id = state.get("request_id") or f"req_{state.get('task_id', 'task')}"
    conv_id = state.get("conversation_id")
    task_id = state.get("task_id", "task")

    emit_agent_started(state, AGENT_ID, AGENT_NAME, GROUP_ID, COMPONENT_TYPE, "Evaluating safety policy and authorization gates...")

    try:
        # Case 1: Clarification needed
        if state.get("clarification_required"):
            prompt = state.get("clarification_prompt", "Please provide additional details.")
            event_bus.publish(
                request_id=req_id,
                execution_id=task_id,
                conversation_id=conv_id,
                node_id=AGENT_ID,
                component_name=AGENT_NAME,
                component_type=COMPONENT_TYPE,
                event_type="CLARIFICATION_REQUIRED",
                execution_status="WAITING_FOR_INPUT",
                safe_task_summary="Clarification required from user before continuing.",
                clarification_prompt=prompt,
                agent_id=AGENT_ID,
                agent_name=AGENT_NAME,
                group_id=GROUP_ID,
                status="WAITING_FOR_APPROVAL",
                timestamp=time.time()
            )
            emit_agent_completed(
                state, AGENT_ID, AGENT_NAME, GROUP_ID, COMPONENT_TYPE,
                "Clarification requested from user.",
                output_summary=prompt,
                duration_s=round(time.time() - t0, 2)
            )
            return {
                "current_agent": AGENT_ID,
                "task_status": "WAITING_FOR_APPROVAL"
            }

        # Case 2: Already Approved by Human in prior turn / resume
        if approval_status == "APPROVED":
            emit_agent_completed(
                state, AGENT_ID, AGENT_NAME, GROUP_ID, COMPONENT_TYPE,
                "Human authorization confirmed. Resuming execution.",
                output_summary="Authorization: APPROVED",
                duration_s=round(time.time() - t0, 2)
            )
            return {
                "current_agent": AGENT_ID,
                "approval_required": False,
                "approval_status": "APPROVED",
                "task_status": "EXECUTING"
            }

        # Case 3: Check if action is consequential or risky
        risk_level, is_risky, reason = SafetyPolicy.evaluate_step_risk(action="", params={}, query=query)

        # In composite install tasks, installation is always consequential
        if task_type == "COMPOSITE" and "install" in query.lower():
            is_risky = True
            reason = "Directive installs software on local Windows machine."
            risk_level = "HIGH"

        if is_risky:
            appr = SafetyPolicy.create_approval_request(
                task_id=task_id,
                conversation_id=conv_id or f"conv_{int(time.time())}",
                step_id=1,
                action="CONSEQUENTIAL_OPERATION",
                reason=reason
            )

            event_bus.publish(
                request_id=req_id,
                execution_id=task_id,
                conversation_id=conv_id,
                node_id=AGENT_ID,
                component_name=AGENT_NAME,
                component_type=COMPONENT_TYPE,
                event_type="APPROVAL_REQUIRED",
                execution_status="WAITING_FOR_APPROVAL",
                safe_task_summary=f"Human authorization required: {reason}",
                approval_id=appr.approval_id,
                approval_reason=reason,
                risk_level=risk_level,
                agent_id=AGENT_ID,
                agent_name=AGENT_NAME,
                group_id=GROUP_ID,
                status="WAITING_FOR_APPROVAL",
                timestamp=time.time()
            )

            emit_agent_completed(
                state, AGENT_ID, AGENT_NAME, GROUP_ID, COMPONENT_TYPE,
                "Execution paused at Human-in-the-Loop authorization gate.",
                output_summary=f"Approval ID: {appr.approval_id} | Reason: {reason}",
                duration_s=round(time.time() - t0, 2)
            )

            return {
                "current_agent": AGENT_ID,
                "approval_required": True,
                "approval_status": "PENDING",
                "approval_id": appr.approval_id,
                "approval_reason": reason,
                "task_status": "WAITING_FOR_APPROVAL"
            }

        # Safe operation - no approval required
        emit_agent_completed(
            state, AGENT_ID, AGENT_NAME, GROUP_ID, COMPONENT_TYPE,
            "Safety check passed. No human approval required.",
            output_summary="Risk: LOW | Status: AUTHORIZED",
            duration_s=round(time.time() - t0, 2)
        )

        return {
            "current_agent": AGENT_ID,
            "approval_required": False,
            "approval_status": "NONE",
            "task_status": "EXECUTING"
        }

    except Exception as e:
        logger.error(f"HITL Safety Controller error: {e}")
        emit_agent_failed(state, AGENT_ID, AGENT_NAME, GROUP_ID, str(e))
        return {
            "current_agent": AGENT_ID,
            "errors": [f"Safety check error: {e}"]
        }
