import time
import logging
from typing import Dict, Any, List
from research_system.graph.state import ResearchState
from research_system.events.event_bus import event_bus
from research_system.llm.ollama_client import ollama_client, MODEL_QWEN_1_7B

logger = logging.getLogger(__name__)

def research_planner_node(state: ResearchState) -> Dict[str, Any]:
    """
    Reasoning Agent 2: Research Planner Agent
    Model: Qwen3 1.7B
    Generates research plans, focused subquestions, and search queries.
    """
    request_id = state.get("request_id", "req_unknown")
    execution_id = state.get("execution_id", "exec_unknown")
    query = state.get("query", "")
    intent = state.get("intent", {})
    is_simple = state.get("is_simple_query", False)
    t0 = time.time()

    event_bus.publish(
        request_id=request_id,
        execution_id=execution_id,
        node_id="research_planner",
        component_name="Research Planner Agent",
        component_type="reasoning_agent",
        event_type="NODE_STARTED",
        execution_status="RUNNING",
        safe_task_summary="Formulating research plan and targeted search queries",
        tool_name="Qwen3 1.7B",
        timestamp=t0
    )

    system_prompt = (
        "You are the Research Planner Agent in O.P.S. 2.0. "
        "Formulate a research plan for the query. Respond strictly in valid JSON with fields: "
        "'plan_steps' (list of 2-4 concise strings), "
        "'subquestions' (list of 2-3 specific questions needed to answer the user), "
        "'search_queries' (list of 2-3 precise search query strings)."
    )

    user_prompt = (
        f"User Query: {query}\n"
        f"Intent Analysis: {intent}\n"
        f"Mode: {'Simple direct lookup' if is_simple else 'Comprehensive multi-source research'}\n\n"
        "Generate the research plan in JSON."
    )

    fallback = {
        "plan_steps": ["Execute primary search", "Extract content", "Synthesize findings"],
        "subquestions": [f"What are the core facts regarding {query}?"],
        "search_queries": [query, f"{query} overview latest"]
    }

    plan_data = ollama_client.generate_json(
        model=MODEL_QWEN_1_7B,
        prompt=user_prompt,
        system_prompt=system_prompt,
        default_fallback=fallback
    )

    subquestions = plan_data.get("subquestions", fallback["subquestions"])
    search_queries = plan_data.get("search_queries", fallback["search_queries"])

    event_bus.publish(
        request_id=request_id,
        execution_id=execution_id,
        node_id="research_planner",
        component_name="Research Planner Agent",
        component_type="reasoning_agent",
        event_type="NODE_COMPLETED",
        execution_status="COMPLETED",
        safe_task_summary=f"Generated {len(plan_data.get('plan_steps', []))} plan steps and {len(search_queries)} search queries",
        safe_output_summary=f"Queries: {', '.join(search_queries[:2])}",
        tool_name="Qwen3 1.7B",
        timestamp=time.time()
    )

    node_history = list(state.get("node_history", []))
    node_history.append("research_planner")

    return {
        "research_plan": plan_data,
        "subquestions": subquestions,
        "search_queries": search_queries,
        "current_active_component": "research_planner",
        "node_history": node_history
    }
