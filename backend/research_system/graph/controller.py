import time
import logging
from typing import Literal
from research_system.graph.state import ResearchState
from research_system.events.event_bus import event_bus

logger = logging.getLogger(__name__)

def adaptive_research_controller_edge(
    state: ResearchState
) -> Literal["execute_another_search", "complete_research"]:
    """
    Adaptive Research Controller:
    A pure LangGraph conditional-routing component (NO separate LLM agent).
    Decides whether to execute another research cycle, perform deeper extraction,
    or complete research and proceed to final evidence synthesis.
    """
    request_id = state.get("request_id", "req_unknown")
    execution_id = state.get("execution_id", "exec_unknown")
    iteration = state.get("iteration_count", 0)
    max_iterations = state.get("max_iterations", 2)
    analysis = state.get("analysis", {})
    is_simple = state.get("is_simple_query", False)
    processed_chunks = state.get("processed_chunks", [])
    t0 = time.time()

    is_sufficient = analysis.get("is_sufficient", True)
    gaps = analysis.get("information_gaps", [])

    # Case 1: Simple query or sufficient evidence already verified
    if is_simple or is_sufficient or len(processed_chunks) >= 12:
        decision = "complete_research"
        reason = "Evidence verified sufficient; moving to evidence retrieval and answer generation."
    # Case 2: Max iteration limit reached
    elif iteration >= max_iterations:
        decision = "complete_research"
        reason = f"Resource limit reached (Iteration {iteration}/{max_iterations}); completing research."
    # Case 3: Gaps detected and iterations remain -> loop back for another search
    else:
        decision = "execute_another_search"
        reason = f"Information gaps detected ({len(gaps)} gaps). Initiating adaptive research loop {iteration + 1}/{max_iterations}."

    event_bus.publish(
        request_id=request_id,
        execution_id=execution_id,
        node_id="adaptive_controller",
        component_name="Adaptive Research Controller",
        component_type="adaptive_controller",
        event_type="ROUTING_DECISION",
        execution_status="COMPLETED",
        safe_task_summary=f"Adaptive Controller Decision: {decision.upper()} (Iteration {iteration})",
        safe_output_summary=reason,
        tool_name="LangGraph Conditional Routing",
        timestamp=t0
    )

    logger.info(f"Adaptive Research Controller decision: {decision} ({reason})")
    return decision


def adaptive_loop_prep_node(state: ResearchState) -> dict:
    """
    Helper node that updates state when the Adaptive Research Controller
    decides to execute another research loop.
    """
    current_iter = state.get("iteration_count", 0) + 1
    analysis = state.get("analysis", {})
    gaps = analysis.get("information_gaps", [])

    # Generate refined search queries from identified gaps
    new_queries = []
    for gap in gaps[:2]:
        if gap and len(gap.strip()) > 3:
            new_queries.append(f"{state.get('query')} {gap.strip()}")

    if not new_queries:
        new_queries = [f"{state.get('query')} deeper analysis facts"]

    node_history = list(state.get("node_history", []))
    node_history.append("adaptive_controller")

    return {
        "iteration_count": current_iter,
        "search_queries": new_queries,
        "routing_decision": "execute_another_search",
        "current_active_component": "adaptive_controller",
        "node_history": node_history
    }
