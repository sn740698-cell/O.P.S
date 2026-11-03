"""
Agent 1: Global Intent Router
Group 1: Global Intelligence
Model: Qwen3 0.6B (hf.co/Qwen/Qwen3-0.6B-GGUF:Q8_0) + Deterministic Ingress Classification
Classifies request into ANSWER, AUTOMATION, COMPOSITE, or CLARIFICATION.
"""

import time
import logging
from typing import Dict, Any
from research_system.orchestrator.state import CentralGraphState
from research_system.orchestrator.agents.base import emit_agent_started, emit_agent_completed, emit_agent_failed
from research_system.router import classify_request_mode as classify_intent_fast, MODE_LLM, MODE_WEB, MODE_HYBRID, MODE_AUTOMATION
from automation_system.planner.automation_planner import AutomationPlanner, MODE_DESKTOP, MODE_BROWSER

logger = logging.getLogger("OPS.Agent.Router")

AGENT_ID = "global_intent_router"
AGENT_NAME = "Global Intent Router"
GROUP_ID = "global_intelligence"
COMPONENT_TYPE = "reasoning_agent"


def global_intent_router_node(state: CentralGraphState) -> Dict[str, Any]:
    """
    Agent 1 node: Classifies query, selects engine, decides answering/automation mode,
    and identifies if human clarification is required.
    """
    t0 = time.time()
    query = state.get("user_query", "").strip()
    emit_agent_started(state, AGENT_ID, AGENT_NAME, GROUP_ID, COMPONENT_TYPE, f"Analyzing directive: '{query[:60]}...'")

    try:
        q_lower = query.lower()
        words = q_lower.split()

        # 1. Ambiguity / Clarification Detection
        vague_directives = [
            "open it", "run it", "click it", "delete it", "download it",
            "open app", "create it", "do it", "do that", "do this",
            "do that now", "do that now please", "start it", "fix it", "make it happen"
        ]
        if q_lower in vague_directives or (len(words) <= 4 and any(v in q_lower for v in ["do that", "open it", "run it", "click it", "delete it", "download it"])):
            clarification_q = "Could you please specify which application, website, file, or target action you would like me to execute?"
            emit_agent_completed(
                state, AGENT_ID, AGENT_NAME, GROUP_ID, COMPONENT_TYPE,
                "Request is ambiguous; clarification needed.",
                output_summary=clarification_q,
                duration_s=round(time.time() - t0, 2)
            )
            return {
                "current_agent": AGENT_ID,
                "task_type": "CLARIFICATION",
                "clarification_required": True,
                "clarification_prompt": clarification_q,
                "routing_result": {
                    "task_type": "CLARIFICATION",
                    "reason": "Directive lacks specific application, file, or target entity."
                }
            }

        # 2. Composite Workflow Detection
        # Task requires research/retrieval followed by an execution action
        # e.g., "Find the latest Node.js LTS version, download it and install it"
        is_composite = False
        has_research_intent = any(w in q_lower for w in ["find", "search", "lookup", "what is", "latest", "check version", "discover"])
        has_automation_intent = any(w in q_lower for w in ["download and", "install", "open it in", "extract and", "save and open", "then launch"])

        if (has_research_intent and has_automation_intent) or ("download" in q_lower and "install" in q_lower) or ("find" in q_lower and "download" in q_lower):
            is_composite = True

        if is_composite:
            routing_res = {
                "task_type": "COMPOSITE",
                "answering_mode": "WEB",
                "automation_mode": "HYBRID",
                "user_goal": "Retrieve target information online and execute subsequent desktop/browser actions.",
                "confidence": 0.95
            }
            emit_agent_completed(
                state, AGENT_ID, AGENT_NAME, GROUP_ID, COMPONENT_TYPE,
                "Routed to Composite Task Coordinator (Research + Automation).",
                output_summary="Task Type: COMPOSITE | Answering: WEB | Automation: HYBRID",
                duration_s=round(time.time() - t0, 2)
            )
            return {
                "current_agent": AGENT_ID,
                "task_type": "COMPOSITE",
                "answering_mode": "WEB",
                "automation_mode": "HYBRID",
                "routing_result": routing_res
            }

        # 3. Dedicated Automation Engine Detection
        # Actions strictly on desktop or browser
        # e.g. "Open Notepad", "Create folder", "Navigate to github.com"
        auto_mode, auto_reason = AutomationPlanner.determine_automation_mode(query)
        is_pure_automation = False

        if any(q_lower.startswith(w) for w in ["open ", "launch ", "start ", "create folder", "delete ", "type ", "navigate to ", "click "]):
            is_pure_automation = True
        elif any(w in q_lower for w in ["in notepad", "in vs code", "on desktop", "in browser", "download file", "extract zip", "fill out form"]):
            is_pure_automation = True

        if is_pure_automation:
            routing_res = {
                "task_type": "AUTOMATION",
                "automation_mode": auto_mode,
                "reason": auto_reason,
                "confidence": 0.98
            }
            emit_agent_completed(
                state, AGENT_ID, AGENT_NAME, GROUP_ID, COMPONENT_TYPE,
                f"Routed to Automation Engine ({auto_mode} mode).",
                output_summary=f"Task Type: AUTOMATION | Mode: {auto_mode}",
                duration_s=round(time.time() - t0, 2)
            )
            return {
                "current_agent": AGENT_ID,
                "task_type": "AUTOMATION",
                "automation_mode": auto_mode,
                "routing_result": routing_res
            }

        # 4. Check for Active Temporary Document Session (RAG Mode)
        conv_id = state.get("conversation_id", "")
        from research_system.services.temporary_rag_service import get_temporary_rag_service
        rag_service = get_temporary_rag_service()
        has_active_docs = rag_service.has_active_documents(conv_id) if conv_id else False

        if has_active_docs:
            is_explicit_web = any(w in q_lower for w in ["search the web", "search online", "google it", "look up on google", "web research"])
            is_chitchat = q_lower in ["hi", "hello", "hey", "who are you", "what can you do", "good morning", "good evening"]

            if not is_explicit_web and not is_chitchat:
                active_docs = rag_service.get_active_documents(conv_id)
                doc_names = ", ".join([d.get("doc_name", "document") for d in active_docs])
                routing_res = {
                    "task_type": "ANSWER",
                    "answering_mode": "DOCUMENT",
                    "rag_retrieval_active": True,
                    "reason": f"Active document session with {len(active_docs)} document(s): {doc_names}.",
                    "confidence": 0.99
                }
                emit_agent_completed(
                    state, AGENT_ID, AGENT_NAME, GROUP_ID, COMPONENT_TYPE,
                    f"Routed to Temporary Document RAG Engine ({doc_names}).",
                    output_summary=f"Task Type: ANSWER | Mode: DOCUMENT | Docs: {doc_names}",
                    duration_s=round(time.time() - t0, 2)
                )
                return {
                    "current_agent": AGENT_ID,
                    "task_type": "ANSWER",
                    "answering_mode": "DOCUMENT",
                    "rag_retrieval_active": True,
                    "attached_documents": active_docs,
                    "routing_result": routing_res
                }

        # 5. Answering Engine Detection (LLM, WEB, HYBRID)
        fast_route = classify_intent_fast(query)
        detected_mode = fast_route.get("mode", MODE_LLM)

        if detected_mode == MODE_AUTOMATION:
            detected_mode = MODE_LLM

        routing_res = {
            "task_type": "ANSWER",
            "answering_mode": detected_mode,
            "reason": fast_route.get("reason", "Answering query classification"),
            "confidence": fast_route.get("confidence", 0.9)
        }

        emit_agent_completed(
            state, AGENT_ID, AGENT_NAME, GROUP_ID, COMPONENT_TYPE,
            f"Routed to Answering Engine ({detected_mode} mode).",
            output_summary=f"Task Type: ANSWER | Mode: {detected_mode}",
            duration_s=round(time.time() - t0, 2)
        )

        return {
            "current_agent": AGENT_ID,
            "task_type": "ANSWER",
            "answering_mode": detected_mode,
            "routing_result": routing_res
        }

    except Exception as e:
        logger.error(f"Global Intent Router error: {e}")
        emit_agent_failed(state, AGENT_ID, AGENT_NAME, GROUP_ID, str(e))
        return {
            "current_agent": AGENT_ID,
            "task_type": "ANSWER",
            "answering_mode": "LLM",
            "errors": [f"Router fallback: {e}"]
        }
