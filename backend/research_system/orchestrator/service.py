"""
O.P.S. 2.0 Central LangGraph Orchestrator Service
Coordinates execution of the 13-component multi-agent graph with
Django persistence, real-time SSE streaming, and thread checkpointing.
"""

import time
import uuid
import logging
from typing import Dict, Any, Optional
from django.utils import timezone
from research_system.orchestrator.state import CentralGraphState
from research_system.orchestrator.builder import central_orchestrator, central_checkpointer
from research_system.models import Conversation, ChatMessage, PendingApproval
from research_system.events.event_bus import EventBus

logger = logging.getLogger("OPS.Orchestrator.Service")
event_bus = EventBus()


class CentralOrchestratorService:
    """
    Primary interface for invoking the 13-component Central LangGraph.
    Manages execution threads, human-in-the-loop checkpoints, and conversation memory.
    """

    @classmethod
    def execute_directive(
        cls,
        query: str,
        conversation_id: str,
        request_id: Optional[str] = None,
        task_id: Optional[str] = None,
        approval_id: Optional[str] = None,
        approval_decision: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Executes a user directive through the central multi-agent LangGraph.
        Supports new directives as well as resuming from saved HITL checkpoints.
        """
        t0 = time.time()
        conv, _ = Conversation.objects.get_or_create(
            conversation_id=conversation_id,
            defaults={"title": query[:40] or "New Session", "status": "ACTIVE"}
        )

        tid = task_id or f"task_ops_{int(t0)}_{uuid.uuid4().hex[:6]}"
        req_id = request_id or f"req_{tid}"

        # Check if resuming after HITL approval
        is_approval_resume = bool(approval_id and approval_decision)
        is_approved = approval_decision in ["approve", "accept", "yes", "true"] if is_approval_resume else False

        initial_state: CentralGraphState = {
            "task_id": tid,
            "conversation_id": conversation_id,
            "request_id": req_id,
            "user_query": query,
            "task_type": "ANSWER",
            "answering_mode": "LLM",
            "automation_mode": "DESKTOP",
            "user_goal": query,
            "routing_result": {},
            "execution_plan": [],
            "current_agent": "global_intent_router",
            "active_agents": [],
            "completed_agents": [],
            "pending_agents": [],
            "agent_status": {},
            "task_dependencies": {},
            "local_reasoning_output": "",
            "research_results": {},
            "validated_evidence": {},
            "automation_results": {},
            "verification_results": {},
            "approval_required": False,
            "approval_status": "APPROVED" if (is_approval_resume and is_approved) else ("REJECTED" if (is_approval_resume and not is_approved) else "NONE"),
            "approval_id": approval_id,
            "approval_reason": "",
            "clarification_required": False,
            "clarification_prompt": None,
            "clarification_response": None,
            "retry_count": 0,
            "errors": [],
            "final_response": "",
            "source_references": [],
            "task_status": "RECEIVED",
            "timestamps": {"started_at": t0}
        }

        # If user rejected the approval, handle safe cancellation immediately
        if is_approval_resume and not is_approved:
            appr = PendingApproval.objects.filter(approval_id=approval_id).first()
            if appr:
                appr.status = "REJECTED"
                appr.resolved_at = timezone.now()
                appr.save()

            cancel_msg = (
                f"## 🛑 OPERATION CANCELLED BY USER\n\n"
                f"**Directive**: `{query}`\n\n"
                f"The pending operation (Approval ID: `{approval_id}`) was explicitly rejected. "
                f"No system modifications or external actions were executed.\n\n"
                f"## 📌 Discussion So Far\n\n"
                f"- Operation cancelled by human administrator: '{query}'\n"
                f"- Status: `CANCELLED`\n"
                f"- Task Identifier: `{tid}`"
            )
            event_bus.publish(
                request_id=req_id,
                execution_id=tid,
                conversation_id=conversation_id,
                node_id="hitl_safety_controller",
                component_name="HITL & Safety Controller",
                component_type="approval_controller",
                event_type="APPROVAL_REJECTED",
                execution_status="CANCELLED",
                safe_task_summary="Operation rejected by user.",
                final_answer=cancel_msg,
                content=cancel_msg,
                timestamp=time.time()
            )
            return {
                "success": True,
                "status": "CANCELLED",
                "task_id": tid,
                "conversation_id": conversation_id,
                "final_answer": cancel_msg,
                "content": cancel_msg,
                "response": cancel_msg
            }

        # Compile thread configuration for LangGraph checkpointing
        config = {"configurable": {"thread_id": conversation_id}}

        # Publish initial task events
        event_bus.publish(
            request_id=req_id,
            execution_id=tid,
            conversation_id=conversation_id,
            node_id="system",
            component_name="O.P.S. Core",
            component_type="orchestrator",
            event_type="REQUEST_STARTED",
            execution_status="ACTIVE",
            safe_task_summary=f"Directive initiated: '{query[:60]}'",
            directive=query,
            timestamp=t0
        )
        event_bus.publish(
            request_id=req_id,
            execution_id=tid,
            conversation_id=conversation_id,
            node_id="global_intent_router",
            component_name="Global Intent Router",
            component_type="reasoning_agent",
            event_type="TASK_RECEIVED",
            execution_status="ACTIVE",
            safe_task_summary=f"Received directive: '{query[:60]}'",
            timestamp=t0
        )

        try:
            # Invoke Central 13-Component Graph
            final_state = central_orchestrator.invoke(initial_state, config=config)

            final_answer = final_state.get("final_response", "")
            task_type = final_state.get("task_type", "ANSWER")
            answering_mode = final_state.get("answering_mode", "LLM")
            auto_mode = final_state.get("automation_mode", "DESKTOP")
            appr_id = final_state.get("approval_id")
            appr_req = final_state.get("approval_required", False)
            clarify_req = final_state.get("clarification_required", False)

            # Determine response mode label for frontend
            if task_type == "AUTOMATION":
                resp_mode = auto_mode
            elif task_type == "COMPOSITE":
                resp_mode = "COMPOSITE"
            elif task_type == "CLARIFICATION":
                resp_mode = "CLARIFICATION"
            else:
                resp_mode = answering_mode

            active_engine = final_state.get("active_engine")
            if not active_engine:
                if task_type == "AUTOMATION":
                    active_engine = "AUTOMATION"
                elif task_type == "COMPOSITE":
                    active_engine = "COMPOSITE"
                elif task_type == "CLARIFICATION":
                    active_engine = "GLOBAL"
                else:
                    active_engine = "ANSWERING"

            # Determine chat message status
            msg_status = "completed"
            if clarify_req:
                msg_status = "needs_clarification"
            elif appr_req and final_state.get("approval_status") == "PENDING":
                msg_status = "pending_approval"

            # Create Assistant Chat Message in database
            assistant_msg = ChatMessage.objects.create(
                conversation=conv,
                message_id=f"msg_{int(time.time())}_{uuid.uuid4().hex[:6]}",
                role="assistant",
                content=final_answer,
                input_type="text",
                status=msg_status,
                metadata={
                    "task_id": tid,
                    "task_type": task_type,
                    "mode": resp_mode,
                    "response_mode": resp_mode,
                    "active_engine": active_engine,
                    "approval_id": appr_id,
                    "clarification_prompt": final_state.get("clarification_prompt"),
                    "plan": final_state.get("execution_plan", [])
                }
            )

            # Update conversation summary
            conv.refresh_from_db()
            conv.status = "ACTIVE"
            conv.save()

            duration = round(time.time() - t0, 2)
            logger.info(f"Central LangGraph completed task {tid} in {duration}s (engine: {active_engine}, mode: {resp_mode}).")

            return {
                "success": True,
                "task_id": tid,
                "conversation_id": conversation_id,
                "request_id": req_id,
                "task_type": task_type,
                "active_engine": active_engine,
                "mode": resp_mode,
                "response_mode": resp_mode,
                "content": final_answer,
                "response": final_answer,
                "final_answer": final_answer,
                "approval_id": appr_id,
                "approval_required": appr_req,
                "clarification_required": clarify_req,
                "clarification_prompt": final_state.get("clarification_prompt"),
                "duration_s": duration,
                "plan": final_state.get("execution_plan", [])
            }

        except Exception as e:
            logger.error(f"Central LangGraph execution error: {e}", exc_info=True)
            err_msg = (
                f"## ⚠️ ORCHESTRATION PIPELINE NOTICE\n\n"
                f"An execution exception occurred during multi-agent graph traversal: `{e}`\n\n"
                f"## 📌 Discussion So Far\n\n"
                f"- Directive encountered failure: '{query}'\n"
                f"- Task Identifier: `{tid}`"
            )
            return {
                "success": False,
                "task_id": tid,
                "conversation_id": conversation_id,
                "error": str(e),
                "final_answer": err_msg,
                "content": err_msg,
                "response": err_msg
            }
