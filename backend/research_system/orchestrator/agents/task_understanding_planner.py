"""
Agent 2: Task Understanding and Planning Agent
Group 1: Global Intelligence
Model: Qwen3 1.7B (hf.co/Qwen/Qwen3-1.7B-GGUF:Q8_0)
Understands complete objective, decomposes requests into structured subtasks,
determines required agents, and identifies task dependencies and human approval gates.
"""

import time
import logging
from typing import Dict, Any, List
from research_system.orchestrator.state import CentralGraphState
from research_system.orchestrator.agents.base import emit_agent_started, emit_agent_completed, emit_agent_failed

logger = logging.getLogger("OPS.Agent.TaskPlanner")

AGENT_ID = "task_understanding_planner"
AGENT_NAME = "Task Understanding & Planning Agent"
GROUP_ID = "global_intelligence"
COMPONENT_TYPE = "reasoning_agent"


def task_understanding_planner_node(state: CentralGraphState) -> Dict[str, Any]:
    """
    Agent 2 node: Evaluates user goal and task_type, establishes execution plan,
    determines the list of required agents, and flags downstream approval needs.
    """
    t0 = time.time()
    query = state.get("user_query", "").strip()
    task_type = state.get("task_type", "ANSWER")
    answering_mode = state.get("answering_mode", "LLM")
    automation_mode = state.get("automation_mode", "DESKTOP")

    emit_agent_started(state, AGENT_ID, AGENT_NAME, GROUP_ID, COMPONENT_TYPE, f"Decomposing workflow for {task_type} task...")

    try:
        execution_plan: List[Dict[str, Any]] = []
        required_agents: List[str] = [AGENT_ID]
        user_goal = query

        if task_type == "CLARIFICATION":
            user_goal = "Request clarifying details from user."
            execution_plan = [
                {"step_id": 1, "agent": "hitl_safety_controller", "action": "request_clarification", "status": "PENDING"},
                {"step_id": 2, "agent": "result_formatter_agent", "action": "format_clarification", "status": "PENDING"}
            ]
            required_agents.extend(["hitl_safety_controller", "result_formatter_agent"])

        elif task_type == "ANSWER":
            if answering_mode == "LLM":
                user_goal = f"Explain and reason locally: {query}"
                execution_plan = [
                    {"step_id": 1, "agent": "local_reasoning_agent", "action": "generate_local_answer", "status": "PENDING"},
                    {"step_id": 2, "agent": "result_formatter_agent", "action": "format_response", "status": "PENDING"}
                ]
                required_agents.extend(["local_reasoning_agent", "result_formatter_agent"])

            elif answering_mode == "WEB":
                user_goal = f"Conduct targeted web research and synthesize evidence: {query}"
                execution_plan = [
                    {"step_id": 1, "agent": "web_research_agent", "action": "retrieve_external_sources", "status": "PENDING"},
                    {"step_id": 2, "agent": "evidence_validation_agent", "action": "validate_evidence_sufficiency", "status": "PENDING"},
                    {"step_id": 3, "agent": "answer_synthesis_agent", "action": "synthesize_grounded_answer", "status": "PENDING"},
                    {"step_id": 4, "agent": "result_formatter_agent", "action": "format_response", "status": "PENDING"}
                ]
                required_agents.extend(["web_research_agent", "evidence_validation_agent", "answer_synthesis_agent", "result_formatter_agent"])

            elif answering_mode == "HYBRID":
                user_goal = f"Synthesize local reasoning with verified live research: {query}"
                execution_plan = [
                    {"step_id": 1, "agent": "local_reasoning_agent", "action": "generate_local_reasoning", "status": "PENDING"},
                    {"step_id": 2, "agent": "web_research_agent", "action": "retrieve_external_sources", "status": "PENDING"},
                    {"step_id": 3, "agent": "evidence_validation_agent", "action": "validate_evidence_sufficiency", "status": "PENDING"},
                    {"step_id": 4, "agent": "answer_synthesis_agent", "action": "combine_reasoning_and_evidence", "status": "PENDING"},
                    {"step_id": 5, "agent": "result_formatter_agent", "action": "format_response", "status": "PENDING"}
                ]
                required_agents.extend(["local_reasoning_agent", "web_research_agent", "evidence_validation_agent", "answer_synthesis_agent", "result_formatter_agent"])

        elif task_type == "AUTOMATION":
            user_goal = f"Execute verified {automation_mode} automation directive: {query}"
            execution_plan = [
                {"step_id": 1, "agent": "automation_planner", "action": "generate_action_steps", "status": "PENDING"},
                {"step_id": 2, "agent": "hitl_safety_controller", "action": "evaluate_safety_policy", "status": "PENDING"}
            ]
            if automation_mode == "DESKTOP":
                execution_plan.extend([
                    {"step_id": 3, "agent": "desktop_automation_executor", "action": "execute_desktop_actions", "status": "PENDING"},
                    {"step_id": 4, "agent": "verification_recovery_agent", "action": "verify_desktop_state", "status": "PENDING"},
                    {"step_id": 5, "agent": "result_formatter_agent", "action": "format_response", "status": "PENDING"}
                ])
                required_agents.extend(["automation_planner", "hitl_safety_controller", "desktop_automation_executor", "verification_recovery_agent", "result_formatter_agent"])
            elif automation_mode == "BROWSER":
                execution_plan.extend([
                    {"step_id": 3, "agent": "browser_automation_executor", "action": "execute_browser_actions", "status": "PENDING"},
                    {"step_id": 4, "agent": "verification_recovery_agent", "action": "verify_browser_state", "status": "PENDING"},
                    {"step_id": 5, "agent": "result_formatter_agent", "action": "format_response", "status": "PENDING"}
                ])
                required_agents.extend(["automation_planner", "hitl_safety_controller", "browser_automation_executor", "verification_recovery_agent", "result_formatter_agent"])
            else:  # HYBRID automation
                execution_plan.extend([
                    {"step_id": 3, "agent": "browser_automation_executor", "action": "execute_browser_download", "status": "PENDING"},
                    {"step_id": 4, "agent": "verification_recovery_agent", "action": "verify_download_state", "status": "PENDING"},
                    {"step_id": 5, "agent": "desktop_automation_executor", "action": "execute_desktop_actions", "status": "PENDING"},
                    {"step_id": 6, "agent": "verification_recovery_agent", "action": "verify_desktop_state", "status": "PENDING"},
                    {"step_id": 7, "agent": "result_formatter_agent", "action": "format_response", "status": "PENDING"}
                ])
                required_agents.extend(["automation_planner", "hitl_safety_controller", "browser_automation_executor", "desktop_automation_executor", "verification_recovery_agent", "result_formatter_agent"])

        elif task_type == "COMPOSITE":
            user_goal = f"Coordinate research discovery followed by verified system automation: {query}"
            execution_plan = [
                {"step_id": 1, "agent": "composite_task_coordinator", "action": "decompose_cross_engine_workflow", "status": "PENDING"},
                {"step_id": 2, "agent": "web_research_agent", "action": "discover_official_sources", "status": "PENDING"},
                {"step_id": 3, "agent": "evidence_validation_agent", "action": "verify_version_and_download_source", "status": "PENDING"},
                {"step_id": 4, "agent": "automation_planner", "action": "prepare_installation_plan", "status": "PENDING"},
                {"step_id": 5, "agent": "hitl_safety_controller", "action": "gate_consequential_installation", "status": "PENDING"},
                {"step_id": 6, "agent": "browser_automation_executor", "action": "download_verified_package", "status": "PENDING"},
                {"step_id": 7, "agent": "desktop_automation_executor", "action": "run_installer", "status": "PENDING"},
                {"step_id": 8, "agent": "verification_recovery_agent", "action": "verify_installation_state", "status": "PENDING"},
                {"step_id": 9, "agent": "result_formatter_agent", "action": "format_response", "status": "PENDING"}
            ]
            required_agents.extend([
                "composite_task_coordinator", "web_research_agent", "evidence_validation_agent",
                "automation_planner", "hitl_safety_controller", "browser_automation_executor",
                "desktop_automation_executor", "verification_recovery_agent", "result_formatter_agent"
            ])

        duration = round(time.time() - t0, 2)
        emit_agent_completed(
            state, AGENT_ID, AGENT_NAME, GROUP_ID, COMPONENT_TYPE,
            f"Created execution plan with {len(execution_plan)} step(s).",
            output_summary=f"Required Agents: {', '.join(required_agents)}",
            duration_s=duration
        )

        return {
            "current_agent": AGENT_ID,
            "user_goal": user_goal,
            "execution_plan": execution_plan,
            "active_agents": required_agents
        }

    except Exception as e:
        logger.error(f"Task Understanding Planner error: {e}")
        emit_agent_failed(state, AGENT_ID, AGENT_NAME, GROUP_ID, str(e))
        return {
            "current_agent": AGENT_ID,
            "errors": [f"Planning error: {e}"]
        }
