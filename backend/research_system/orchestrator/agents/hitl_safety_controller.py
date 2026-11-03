"""
Agent 11: Human-in-the-Loop and Safety Controller
Group 3: Automation Engine (Global Safety Gate across all 4 Groups)
Mandatory centralized safety, approval, and clarification checkpoint.
Enforces authorization gates for consequential actions, ambiguous directives,
and coordinates LangGraph interrupt checkpoints.
"""

import time
import uuid
import logging
from typing import Dict, Any
from research_system.orchestrator.state import CentralGraphState
from research_system.orchestrator.agents.base import emit_agent_started, emit_agent_completed, emit_agent_failed
from research_system.models import PendingApproval, Conversation
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

        # Case 2b: User explicitly rejected / denied approval
        if approval_status in ["REJECTED", "DENIED"]:
            emit_agent_completed(
                state, AGENT_ID, AGENT_NAME, GROUP_ID, COMPONENT_TYPE,
                "Human authorization denied. Execution halted safely.",
                output_summary="Authorization: DENIED",
                duration_s=round(time.time() - t0, 2)
            )
            return {
                "current_agent": AGENT_ID,
                "approval_required": False,
                "approval_status": "REJECTED",
                "task_status": "CANCELLED"
            }

        # Case 3: MANDATORY HITL APPROVAL GATE FOR ALL AUTOMATION ACTIONS
        steps = state.get("execution_plan", [])
        auto_mode = state.get("automation_mode", "DESKTOP")
        is_automation_task = (task_type == "AUTOMATION") or (len(steps) > 0 and any(s.get("executor") in ["desktop", "browser", "system"] for s in steps))

        if is_automation_task:
            hitl_details = SafetyPolicy.build_automation_hitl_details(query, steps, mode=auto_mode)
            approval_id = f"appr_{int(time.time())}_{uuid.uuid4().hex[:6]}"
            conv = Conversation.objects.filter(conversation_id=conv_id).first()

            appr = PendingApproval.objects.create(
                approval_id=approval_id,
                conversation=conv,
                target_conversation_id=conv_id or f"conv_{int(time.time())}",
                execution_id=task_id,
                action_type=f"AUTOMATION_{auto_mode.upper()}",
                status="PENDING",
                description=hitl_details["action_summary"],
                metadata={
                    "task_id": task_id,
                    "query": query,
                    "user_query": query,
                    "mode": auto_mode,
                    **hitl_details
                }
            )

            # Publish approval request to EventBus and Cockpit
            event_bus.publish(
                request_id=req_id,
                execution_id=task_id,
                conversation_id=conv_id,
                node_id=AGENT_ID,
                component_name=AGENT_NAME,
                component_type=COMPONENT_TYPE,
                event_type="APPROVAL_REQUIRED",
                execution_status="WAITING_FOR_APPROVAL",
                safe_task_summary=f"Human authorization required: {hitl_details['action_summary']}",
                approval_id=approval_id,
                approval_reason=hitl_details["action_summary"],
                target=hitl_details["target"],
                target_application=hitl_details["target_application"],
                target_url=hitl_details["target_url"],
                target_file_path=hitl_details["target_file_path"],
                execution_plan=hitl_details["execution_plan"],
                input_content=hitl_details["input_content"],
                expected_result=hitl_details["expected_result"],
                risk_level=hitl_details["risk_level"],
                is_destructive=hitl_details["is_destructive"],
                agent_id=AGENT_ID,
                agent_name=AGENT_NAME,
                group_id=GROUP_ID,
                status="WAITING_FOR_APPROVAL",
                timestamp=time.time()
            )

            emit_agent_completed(
                state, AGENT_ID, AGENT_NAME, GROUP_ID, COMPONENT_TYPE,
                "Execution paused at Human-in-the-Loop authorization gate.",
                output_summary=f"Approval ID: {approval_id} | Target: {hitl_details['target']}",
                duration_s=round(time.time() - t0, 2)
            )

            return {
                "current_agent": AGENT_ID,
                "approval_required": True,
                "approval_status": "PENDING",
                "approval_id": approval_id,
                "approval_reason": hitl_details["action_summary"],
                "proposed_plan": steps,
                "proposed_operations": hitl_details["execution_plan"],
                "target_application": hitl_details["target_application"],
                "target_url": hitl_details["target_url"],
                "target_file_path": hitl_details["target_file_path"],
                "requested_content": hitl_details["input_content"],
                "approved_plan_hash": hitl_details["plan_hash"],
                "task_status": "WAITING_FOR_APPROVAL"
            }

        # Case 4: Non-automation (Pure Answering Engine: LLM, Web Research)
        # Check if action is consequential or risky
        risk_level, is_risky, reason = SafetyPolicy.evaluate_step_risk(action="", params={}, query=query)
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
