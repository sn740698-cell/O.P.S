"""
Agent 1: Global Intent Router
Group 1: Global Intelligence
Model: Qwen3 0.6B + Semantic Intent & Syntactic Routing Engine
Classifies request into ANSWER, AUTOMATION, COMPOSITE, or CLARIFICATION.
Selects the operational Engine (ANSWERING, AUTOMATION, COMPOSITE, CLARIFICATION)
and operational Mode (LLM, WEB, HYBRID, DOCUMENT, DESKTOP, BROWSER, HYBRID).
"""

import time
import logging
from typing import Dict, Any
from research_system.orchestrator.state import CentralGraphState
from research_system.orchestrator.agents.base import emit_agent_started, emit_agent_completed, emit_agent_failed
from research_system.router import (
    classify_request_mode,
    TASK_ANSWER,
    TASK_AUTOMATION,
    TASK_COMPOSITE,
    TASK_CLARIFICATION,
    ENGINE_ANSWERING,
    ENGINE_AUTOMATION,
    ENGINE_COMPOSITE,
    ENGINE_CLARIFICATION,
    MODE_LLM,
    MODE_WEB,
    MODE_HYBRID,
    MODE_DOCUMENT,
    MODE_CLARIFICATION,
    MODE_DESKTOP_AUTO,
    MODE_BROWSER_AUTO,
    MODE_HYBRID_AUTO,
    STAGES_MAP
)
from research_system.events.event_bus import EventBus

logger = logging.getLogger("OPS.Agent.Router")
event_bus = EventBus()

AGENT_ID = "global_intent_router"
AGENT_NAME = "Global Intent Router"
GROUP_ID = "global_intelligence"
COMPONENT_TYPE = "reasoning_agent"


def global_intent_router_node(state: CentralGraphState) -> Dict[str, Any]:
    """
    Agent 1 node: Classifies query, selects engine, decides answering/automation mode,
    and identifies if human clarification is required. Emits real-time ENGINE_SELECTED
    and MODE_SELECTED events to Pop-up Cockpit and browser UI.
    """
    t0 = time.time()
    query = state.get("user_query", "").strip()
    req_id = state.get("request_id") or f"req_{state.get('task_id', 'task')}"
    task_id = state.get("task_id", "task")
    conv_id = state.get("conversation_id")

    emit_agent_started(state, AGENT_ID, AGENT_NAME, GROUP_ID, COMPONENT_TYPE, f"Analyzing directive intent: '{query[:60]}...'")

    try:
        q_lower = query.lower()

        # 1. Check for Active Temporary Document Session (RAG Mode)
        # Follow Section 11 Rules 13 & 14:
        # - Asking general knowledge with doc attached -> LLM
        # - Asking current info with doc attached -> WEB / HYBRID
        # - Asking about document -> DOCUMENT / RAG
        has_active_docs = False
        active_docs = []
        if conv_id:
            try:
                from research_system.services.temporary_rag_service import get_temporary_rag_service
                rag_service = get_temporary_rag_service()
                if rag_service.has_active_documents(conv_id):
                    has_active_docs = True
                    active_docs = rag_service.get_active_documents(conv_id)
            except Exception as e_rag:
                logger.warning(f"RAG document check notice: {e_rag}")

        is_explicit_doc_query = False
        if has_active_docs:
            doc_triggers = [
                "resume", "document", "uploaded", "ncc", "pdf", "word", "docx",
                "this document", "my document", "in the file", "from the file",
                "read my", "summarize my", "achievements", "according to the doc"
            ]
            if any(dt in q_lower for dt in doc_triggers):
                is_explicit_doc_query = True

        if has_active_docs and is_explicit_doc_query:
            doc_names = ", ".join([d.get("doc_name", "document") for d in active_docs])
            reason = f"Directive targets active temporary document session ({doc_names})."
            stages = STAGES_MAP.get(MODE_DOCUMENT, [])
            routing_res = {
                "response_mode": MODE_DOCUMENT,
                "mode": MODE_DOCUMENT,
                "task_type": TASK_ANSWER,
                "active_engine": ENGINE_ANSWERING,
                "user_intent": "TEMPORARY_DOCUMENT_INTELLIGENCE",
                "user_goal": f"Retrieve and reason over active document: {query}",
                "answering_engine_required": True,
                "automation_engine_required": False,
                "selected_answering_mode": MODE_DOCUMENT,
                "selected_automation_mode": None,
                "required_agents": ["global_intent_router", "task_understanding_planner", "local_reasoning_agent", "result_formatter_agent"],
                "required_tools": ["PineconeVectorStore", "DocumentRetriever"],
                "execution_plan": [],
                "approval_required": False,
                "clarification_required": False,
                "confidence": 0.99,
                "routing_reason": reason,
                "reason": reason,
                "search_query": query,
                "stages": stages,
                "latency_ms": round((time.time() - t0) * 1000, 2)
            }

            # Emit real-time telemetry events
            _emit_routing_events(req_id, task_id, conv_id, ENGINE_ANSWERING, MODE_DOCUMENT, TASK_ANSWER, reason, stages, t0)

            emit_agent_completed(
                state, AGENT_ID, AGENT_NAME, GROUP_ID, COMPONENT_TYPE,
                f"Routed to Temporary Document RAG Engine ({doc_names}).",
                output_summary=f"Engine: ANSWERING | Mode: DOCUMENT | Docs: {doc_names}",
                duration_s=round(time.time() - t0, 2)
            )

            return {
                "current_agent": AGENT_ID,
                "task_type": TASK_ANSWER,
                "active_engine": ENGINE_ANSWERING,
                "answering_mode": MODE_DOCUMENT,
                "response_mode": MODE_DOCUMENT,
                "user_goal": routing_res["user_goal"],
                "rag_retrieval_active": True,
                "attached_documents": active_docs,
                "routing_result": routing_res
            }

        # 2. Comprehensive Semantic & Syntactic Intent Classification
        fast_route = classify_request_mode(query, allow_model_call=True)

        task_type = fast_route.get("task_type", TASK_ANSWER)
        active_engine = fast_route.get("active_engine", ENGINE_ANSWERING)
        resp_mode = fast_route.get("response_mode") or fast_route.get("mode") or MODE_LLM
        reason = fast_route.get("routing_reason") or fast_route.get("reason") or "Classified directive intent."
        stages = fast_route.get("stages") or STAGES_MAP.get(resp_mode, STAGES_LLM)
        user_goal = fast_route.get("user_goal") or f"Execute: {query}"
        approval_req = fast_route.get("approval_required", False)
        approval_reason = fast_route.get("approval_reason", "")
        clarify_req = fast_route.get("clarification_required", False)
        clarify_prompt = fast_route.get("clarification_prompt")

        # Map answering and automation modes
        if task_type == TASK_AUTOMATION:
            answering_mode = None
            automation_mode = resp_mode  # 'DESKTOP' | 'BROWSER' | 'HYBRID'
        elif task_type == TASK_COMPOSITE:
            answering_mode = MODE_WEB
            automation_mode = MODE_HYBRID_AUTO
        elif task_type == TASK_CLARIFICATION:
            answering_mode = None
            automation_mode = None
        else:  # ANSWER
            answering_mode = resp_mode
            automation_mode = None

        # 3. Emit real-time routing events for cockpit & browser streaming
        _emit_routing_events(req_id, task_id, conv_id, active_engine, resp_mode, task_type, reason, stages, t0)

        duration = round(time.time() - t0, 2)
        emit_agent_completed(
            state, AGENT_ID, AGENT_NAME, GROUP_ID, COMPONENT_TYPE,
            f"Resolved Engine: {active_engine} | Mode: {resp_mode} ({reason}).",
            output_summary=f"Engine: {active_engine} | Mode: {resp_mode} | Task: {task_type}",
            duration_s=duration
        )

        return {
            "current_agent": AGENT_ID,
            "task_type": task_type,
            "active_engine": active_engine,
            "answering_mode": answering_mode or "LLM",
            "automation_mode": automation_mode or "DESKTOP",
            "response_mode": resp_mode,
            "user_goal": user_goal,
            "approval_required": approval_req,
            "approval_reason": approval_reason,
            "clarification_required": clarify_req,
            "clarification_prompt": clarify_prompt,
            "routing_result": fast_route
        }

    except Exception as e:
        logger.error(f"Global Intent Router error: {e}", exc_info=True)
        emit_agent_failed(state, AGENT_ID, AGENT_NAME, GROUP_ID, str(e))
        return {
            "current_agent": AGENT_ID,
            "task_type": TASK_ANSWER,
            "active_engine": ENGINE_ANSWERING,
            "answering_mode": "LLM",
            "response_mode": "LLM",
            "errors": [f"Router fallback: {e}"]
        }


def _emit_routing_events(
    req_id: str,
    task_id: str,
    conv_id: str,
    engine: str,
    mode: str,
    task_type: str,
    reason: str,
    stages: list,
    t0: float
):
    """Publishes ENGINE_SELECTED and MODE_SELECTED events to active listeners."""
    now = time.time()
    event_bus.publish(
        request_id=req_id,
        execution_id=task_id,
        conversation_id=conv_id,
        node_id=AGENT_ID,
        component_name=AGENT_NAME,
        component_type=COMPONENT_TYPE,
        event_type="ENGINE_SELECTED",
        execution_status="RUNNING",
        active_engine=engine,
        task_type=task_type,
        response_mode=mode,
        mode=mode,
        mode_reason=reason,
        stages=stages,
        current_stage=stages[0] if stages else "Planning directive",
        safe_task_summary=f"Active Engine: {engine} ({mode} Mode)",
        timestamp=now
    )

    event_bus.publish(
        request_id=req_id,
        execution_id=task_id,
        conversation_id=conv_id,
        node_id=AGENT_ID,
        component_name=AGENT_NAME,
        component_type=COMPONENT_TYPE,
        event_type="MODE_SELECTED",
        execution_status="RUNNING",
        active_engine=engine,
        task_type=task_type,
        response_mode=mode,
        new_mode=mode,
        mode=mode,
        mode_reason=reason,
        reason=reason,
        stages=stages,
        current_stage=stages[0] if stages else "Planning directive",
        safe_task_summary=reason,
        timestamp=now
    )
