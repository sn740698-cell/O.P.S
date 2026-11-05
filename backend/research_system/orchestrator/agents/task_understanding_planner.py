"""
Agent 2: Task Understanding and Planning Agent
Group 1: Global Intelligence
Model: Qwen3 1.7B (hf.co/Qwen/Qwen3-1.7B-GGUF:Q8_0)
Understands complete objective, decomposes requests into structured subtasks,
determines required agents, resolves conversation context, and identifies task dependencies and approval gates.
"""

import time
import logging
from typing import Dict, Any, List
from research_system.orchestrator.state import CentralGraphState
from research_system.orchestrator.agents.base import emit_agent_started, emit_agent_completed, emit_agent_failed
from research_system.orchestrator.reasoning import AdvancedPromptUnderstandingAgent

logger = logging.getLogger("OPS.Agent.TaskPlanner")

AGENT_ID = "task_understanding_planner"
AGENT_NAME = "Task Understanding & Planning Agent"
GROUP_ID = "global_intelligence"
COMPONENT_TYPE = "reasoning_agent"


def task_understanding_planner_node(state: CentralGraphState) -> Dict[str, Any]:
    """
    Agent 2 node: Evaluates user goal using Qwen3 1.7B multi-stage understanding,
    resolves context and constraints, produces structured plan contract,
    and sets task dependencies and approval gates.
    """
    t0 = time.time()
    query = state.get("user_query", "").strip()
    conv_hist = state.get("conversation_history") or []
    task_id = state.get("task_id") or f"task_{int(time.time() * 1000)}"

    emit_agent_started(state, AGENT_ID, AGENT_NAME, GROUP_ID, COMPONENT_TYPE, f"Reasoning over directive: '{query[:60]}...'")

    try:
        # Invoke Qwen3 1.7B Multi-Stage Understanding & Planning Engine
        understanding_agent = AdvancedPromptUnderstandingAgent()
        contract = understanding_agent.understand_and_plan(
            query=query,
            conversation_history=conv_hist,
            task_id=task_id
        )

        task_type = contract.get("task_type", "ANSWER")
        ans_engine = contract.get("answering_engine", "NONE")
        auto_engine = contract.get("automation_engine", "NONE")
        user_obj = contract.get("user_objective") or query
        plan = contract.get("execution_plan") or []
        constraints = contract.get("constraints") or []
        clarify_req = contract.get("clarification_required", False)
        clarify_q = contract.get("clarification_question")
        approval_req = contract.get("approval_required", False)

        # Normalize answering and automation modes for state
        if task_type == "CLARIFICATION" or clarify_req:
            task_type = "CLARIFICATION"
            ans_mode = None
            auto_mode = None
            plan = [
                {"step_id": 1, "agent": "hitl_safety_controller", "action": "request_clarification", "status": "PENDING"},
                {"step_id": 2, "agent": "result_formatter_agent", "action": "format_clarification", "status": "PENDING"}
            ]
        elif task_type in ["AUTOMATION", "DEVELOPMENT"]:
            task_type = "AUTOMATION"
            ans_mode = None
            auto_mode = auto_engine if auto_engine in ["DESKTOP", "BROWSER", "HYBRID"] else "DESKTOP"
        elif task_type == "COMPOSITE":
            ans_mode = "WEB"
            auto_mode = "HYBRID"
        elif task_type == "RESEARCH":
            task_type = "ANSWER"
            ans_mode = "WEB"
            auto_mode = None
        elif task_type == "REASONING":
            task_type = "ANSWER"
            ans_mode = "HYBRID"
            auto_mode = None
        else:  # ANSWER
            task_type = "ANSWER"
            ans_mode = ans_engine if ans_engine in ["LLM", "WEB", "HYBRID", "DOCUMENT"] else "LLM"
            auto_mode = None

        # Build execution plan if model provided high-level subtasks
        if not plan:
            plan = _build_default_plan(task_type, ans_mode, auto_mode, query)

        duration = round(time.time() - t0, 2)
        emit_agent_completed(
            state, AGENT_ID, AGENT_NAME, GROUP_ID, COMPONENT_TYPE,
            f"Understood objective: {user_obj[:80]} (Type={task_type}, Ans={ans_mode}, Auto={auto_mode})",
            output_summary=f"Engine plan ready: {len(plan)} step(s) in {duration}s",
            duration_s=duration
        )

        return {
            "current_agent": AGENT_ID,
            "task_type": task_type,
            "answering_mode": ans_mode or "LLM",
            "automation_mode": auto_mode or "DESKTOP",
            "user_goal": user_obj,
            "execution_plan": plan,
            "subtasks": plan,
            "clarification_required": clarify_req,
            "clarification_prompt": clarify_q,
            "approval_required": approval_req,
            "proposed_plan": plan
        }

    except Exception as e:
        logger.error(f"Task Understanding Planner error: {e}", exc_info=True)
        emit_agent_failed(state, AGENT_ID, AGENT_NAME, GROUP_ID, str(e))
        return {
            "current_agent": AGENT_ID,
            "errors": [f"Task planning error: {e}"]
        }


def _build_default_plan(task_type: str, ans_mode: str, auto_mode: str, query: str) -> List[Dict[str, Any]]:
    """Builds standard LangGraph step sequence for task type."""
    if task_type == "CLARIFICATION":
        return [
            {"step_id": 1, "agent": "hitl_safety_controller", "action": "request_clarification", "status": "PENDING"},
            {"step_id": 2, "agent": "result_formatter_agent", "action": "format_clarification", "status": "PENDING"}
        ]
    elif task_type == "ANSWER":
        if ans_mode == "WEB":
            return [
                {"step_id": 1, "agent": "web_research_agent", "action": "retrieve_external_sources", "status": "PENDING"},
                {"step_id": 2, "agent": "evidence_validation_agent", "action": "validate_evidence_sufficiency", "status": "PENDING"},
                {"step_id": 3, "agent": "answer_synthesis_agent", "action": "synthesize_grounded_answer", "status": "PENDING"},
                {"step_id": 4, "agent": "result_formatter_agent", "action": "format_response", "status": "PENDING"}
            ]
        elif ans_mode == "HYBRID":
            return [
                {"step_id": 1, "agent": "local_reasoning_agent", "action": "generate_local_reasoning", "status": "PENDING"},
                {"step_id": 2, "agent": "web_research_agent", "action": "retrieve_external_sources", "status": "PENDING"},
                {"step_id": 3, "agent": "evidence_validation_agent", "action": "validate_evidence_sufficiency", "status": "PENDING"},
                {"step_id": 4, "agent": "answer_synthesis_agent", "action": "combine_reasoning_and_evidence", "status": "PENDING"},
                {"step_id": 5, "agent": "result_formatter_agent", "action": "format_response", "status": "PENDING"}
            ]
        else:  # LLM
            return [
                {"step_id": 1, "agent": "local_reasoning_agent", "action": "generate_local_answer", "status": "PENDING"},
                {"step_id": 2, "agent": "result_formatter_agent", "action": "format_response", "status": "PENDING"}
            ]
    elif task_type == "AUTOMATION":
        executor = "desktop_automation_executor" if auto_mode == "DESKTOP" else "browser_automation_executor"
        return [
            {"step_id": 1, "agent": "automation_planner", "action": "generate_action_steps", "status": "PENDING"},
            {"step_id": 2, "agent": "hitl_safety_controller", "action": "evaluate_safety_policy", "status": "PENDING"},
            {"step_id": 3, "agent": executor, "action": f"execute_{auto_mode.lower()}_actions", "status": "PENDING"},
            {"step_id": 4, "agent": "verification_recovery_agent", "action": f"verify_{auto_mode.lower()}_state", "status": "PENDING"},
            {"step_id": 5, "agent": "result_formatter_agent", "action": "format_response", "status": "PENDING"}
        ]
    elif task_type == "COMPOSITE":
        return [
            {"step_id": 1, "agent": "composite_task_coordinator", "action": "decompose_cross_engine_workflow", "status": "PENDING"},
            {"step_id": 2, "agent": "web_research_agent", "action": "discover_official_sources", "status": "PENDING"},
            {"step_id": 3, "agent": "automation_planner", "action": "prepare_installation_plan", "status": "PENDING"},
            {"step_id": 4, "agent": "hitl_safety_controller", "action": "gate_consequential_installation", "status": "PENDING"},
            {"step_id": 5, "agent": "desktop_automation_executor", "action": "run_installer", "status": "PENDING"},
            {"step_id": 6, "agent": "result_formatter_agent", "action": "format_response", "status": "PENDING"}
        ]
    return []
