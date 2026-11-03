"""
O.P.S. 2.0 Central LangGraph Orchestrator
Sections 2, 6: Central 13-Component Multi-Agent Workflow
Coordinates:
- Group 1: Global Intelligence (Agents 1, 2)
- Group 2: Answering Engine (Agents 3, 4, 5, 6)
- Group 3: Automation Engine (Agents 7, 8, 9, 10, 11)
- Group 4: Composite Coordination and Delivery (Agents 12, 13)
"""

import logging
from typing import Dict, Any, List, Optional
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from research_system.orchestrator.state import CentralGraphState

# Group 1: Global Intelligence
from research_system.orchestrator.agents.global_intent_router import global_intent_router_node
from research_system.orchestrator.agents.task_understanding_planner import task_understanding_planner_node

# Group 2: Answering Engine
from research_system.orchestrator.agents.local_reasoning_agent import local_reasoning_agent_node
from research_system.orchestrator.agents.web_research_agent import web_research_agent_node
from research_system.orchestrator.agents.evidence_validation_agent import evidence_validation_agent_node
from research_system.orchestrator.agents.answer_synthesis_agent import answer_synthesis_agent_node

# Group 3: Automation Engine
from research_system.orchestrator.agents.automation_planner_agent import automation_planner_agent_node
from research_system.orchestrator.agents.desktop_automation_executor import desktop_automation_executor_node
from research_system.orchestrator.agents.browser_automation_executor import browser_automation_executor_node
from research_system.orchestrator.agents.verification_recovery_agent import verification_recovery_agent_node
from research_system.orchestrator.agents.hitl_safety_controller import hitl_safety_controller_node

# Group 4: Composite Coordination & Delivery
from research_system.orchestrator.agents.composite_task_coordinator import composite_task_coordinator_node
from research_system.orchestrator.agents.result_formatter_agent import result_formatter_agent_node

logger = logging.getLogger("OPS.Orchestrator.Builder")

# Central Checkpointer for thread and HITL resume management
central_checkpointer = MemorySaver()


def route_after_task_planning(state: CentralGraphState) -> str:
    """
    Decides the next node or engine branch based on task_type and answering_mode.
    """
    task_type = state.get("task_type", "ANSWER")
    answering_mode = state.get("answering_mode", "LLM")

    if task_type == "CLARIFICATION":
        return "hitl_safety_controller"
    elif task_type == "AUTOMATION":
        return "automation_planner"
    elif task_type == "COMPOSITE":
        return "composite_task_coordinator"
    else:  # ANSWER
        if answering_mode in ["LLM", "DOCUMENT"]:
            return "local_reasoning_agent"
        elif answering_mode == "WEB":
            return "web_research_agent"
        else:  # HYBRID
            return "hybrid_fanout"


def route_after_safety_controller(state: CentralGraphState) -> str:
    """
    Evaluates whether the automation task requires pausing for approval
    or can immediately proceed to execution.
    """
    approval_required = state.get("approval_required", False)
    approval_status = state.get("approval_status", "NONE")
    auto_mode = state.get("automation_mode", "DESKTOP")

    # If approval is needed and not yet confirmed, pause directly to formatter
    if approval_required and approval_status != "APPROVED":
        return "result_formatter_agent"

    # Execution route based on automation mode
    if auto_mode == "DESKTOP":
        return "desktop_automation_executor"
    elif auto_mode == "BROWSER":
        return "browser_automation_executor"
    else:  # HYBRID automation
        return "browser_automation_executor"


def hybrid_fanout_node(state: CentralGraphState) -> Dict[str, Any]:
    """
    Fan-out intermediary node for Hybrid answering mode,
    triggering both local reasoning and web research.
    """
    # In synchronous execution, local reasoning can run followed by research
    # and both outputs populate the shared state before evidence validation.
    state_update = {}
    r_up = local_reasoning_agent_node(state)
    state_update.update(r_up)

    w_up = web_research_agent_node(state)
    state_update.update(w_up)

    return state_update


def route_after_answer_synthesis(state: CentralGraphState) -> str:
    """
    Routes composite workflows to automation planning after research validation,
    or directly to result formatter for pure answering workflows.
    """
    if state.get("task_type") == "COMPOSITE":
        return "automation_planner"
    return "result_formatter_agent"


def route_after_browser_executor(state: CentralGraphState) -> str:
    """
    In hybrid automation workflows, after browser actions complete,
    proceeds to desktop automation executor if desktop steps exist.
    Otherwise routes directly to verification recovery.
    """
    steps = state.get("execution_plan", [])
    has_desktop_steps = any(s.get("executor") == "desktop" for s in steps)
    auto_res = state.get("automation_results", {})
    desktop_done = len(auto_res.get("desktop_results", [])) > 0
    if has_desktop_steps and not desktop_done:
        return "desktop_automation_executor"
    return "verification_recovery_agent"


def build_central_ops_graph():
    """
    Constructs and compiles the canonical 13-component LangGraph orchestrator.
    """
    workflow = StateGraph(CentralGraphState)

    # 1. Register all 13 component nodes
    workflow.add_node("global_intent_router", global_intent_router_node)
    workflow.add_node("task_understanding_planner", task_understanding_planner_node)
    workflow.add_node("local_reasoning_agent", local_reasoning_agent_node)
    workflow.add_node("web_research_agent", web_research_agent_node)
    workflow.add_node("evidence_validation_agent", evidence_validation_agent_node)
    workflow.add_node("answer_synthesis_agent", answer_synthesis_agent_node)
    workflow.add_node("automation_planner", automation_planner_agent_node)
    workflow.add_node("desktop_automation_executor", desktop_automation_executor_node)
    workflow.add_node("browser_automation_executor", browser_automation_executor_node)
    workflow.add_node("verification_recovery_agent", verification_recovery_agent_node)
    workflow.add_node("hitl_safety_controller", hitl_safety_controller_node)
    workflow.add_node("composite_task_coordinator", composite_task_coordinator_node)
    workflow.add_node("result_formatter_agent", result_formatter_agent_node)

    # Intermediary Fan-out node for Parallel Hybrid Answering
    workflow.add_node("hybrid_fanout", hybrid_fanout_node)

    # 2. Main Entry Path
    workflow.add_edge(START, "global_intent_router")
    workflow.add_edge("global_intent_router", "task_understanding_planner")

    # 3. Conditional Routing after Task Understanding
    workflow.add_conditional_edges(
        "task_understanding_planner",
        route_after_task_planning,
        {
            "local_reasoning_agent": "local_reasoning_agent",
            "web_research_agent": "web_research_agent",
            "hybrid_fanout": "hybrid_fanout",
            "automation_planner": "automation_planner",
            "composite_task_coordinator": "composite_task_coordinator",
            "hitl_safety_controller": "hitl_safety_controller"
        }
    )

    # 4. Answering Engine Paths
    # LLM Path
    workflow.add_edge("local_reasoning_agent", "result_formatter_agent")

    # Web Research Path
    workflow.add_edge("web_research_agent", "evidence_validation_agent")
    workflow.add_edge("evidence_validation_agent", "answer_synthesis_agent")
    workflow.add_conditional_edges(
        "answer_synthesis_agent",
        route_after_answer_synthesis,
        {
            "automation_planner": "automation_planner",
            "result_formatter_agent": "result_formatter_agent"
        }
    )

    # Hybrid Path: converges at evidence_validation_agent
    workflow.add_edge("hybrid_fanout", "evidence_validation_agent")

    # 5. Automation Engine Path
    workflow.add_edge("automation_planner", "hitl_safety_controller")
    workflow.add_conditional_edges(
        "hitl_safety_controller",
        route_after_safety_controller,
        {
            "result_formatter_agent": "result_formatter_agent",
            "desktop_automation_executor": "desktop_automation_executor",
            "browser_automation_executor": "browser_automation_executor"
        }
    )

    # Post-Execution -> Verification (supports chained Hybrid Automation)
    workflow.add_edge("desktop_automation_executor", "verification_recovery_agent")
    workflow.add_conditional_edges(
        "browser_automation_executor",
        route_after_browser_executor,
        {
            "desktop_automation_executor": "desktop_automation_executor",
            "verification_recovery_agent": "verification_recovery_agent"
        }
    )
    workflow.add_edge("verification_recovery_agent", "result_formatter_agent")

    # 6. Composite Coordination Path
    workflow.add_edge("composite_task_coordinator", "web_research_agent")

    # 7. Final Delivery Path
    workflow.add_edge("result_formatter_agent", END)

    # Compile with central checkpointer
    app = workflow.compile(checkpointer=central_checkpointer)
    logger.info("Compiled O.P.S. 2.0 Central LangGraph Orchestrator (13 components).")
    return app


# Singleton instance of compiled central graph
central_orchestrator = build_central_ops_graph()
