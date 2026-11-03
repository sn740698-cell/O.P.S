"""
O.P.S. 2.0 — Local Reasoning Agent
Parallel Hybrid Reasoning Branch
Model: Qwen3 1.7B
Responsibilities:
- Synthesizes established architectural, technical, and conceptual background knowledge
- Clarifies core principles and mental models without hallucinating current temporal facts
- Pinpoints specific facets that require live web verification
- Provides the conceptual foundation merged with validated web evidence during final synthesis
"""

import time
import logging
import concurrent.futures
from typing import Dict, Any, List, Optional
from research_system.graph.state import ResearchState
from research_system.events.event_bus import event_bus
from research_system.llm.ollama_client import ollama_client, MODEL_QWEN_1_7B

logger = logging.getLogger(__name__)

_LOCAL_REASONING_POOL = concurrent.futures.ThreadPoolExecutor(max_workers=2, thread_name_prefix="HybridLocalReasoning")
_ACTIVE_REASONING_FUTURES: Dict[str, concurrent.futures.Future] = {}


def start_local_reasoning(state: ResearchState) -> Optional[concurrent.futures.Future]:
    """
    Launches local reasoning concurrently on Qwen3 1.7B in the background
    while the web research branch fetches and scrapes online sources.
    """
    exec_id = state.get("execution_id") or state.get("request_id", "default")
    try:
        # Pass a snapshot copy of state to prevent thread mutation issues
        state_copy = dict(state)
        future = _LOCAL_REASONING_POOL.submit(local_reasoning_node, state_copy)
        _ACTIVE_REASONING_FUTURES[exec_id] = future
        logger.info(f"Launched parallel local reasoning thread for execution_id={exec_id}")
        return future
    except Exception as e:
        logger.warning(f"Failed to launch parallel local reasoning thread: {e}")
        return None


def await_local_reasoning(execution_id: str, timeout: float = 25.0) -> str:
    """
    Waits for the concurrent local reasoning branch to complete, retrieving the conceptual analysis.
    """
    future = _ACTIVE_REASONING_FUTURES.pop(execution_id, None)
    if future:
        try:
            res = future.result(timeout=timeout)
            if isinstance(res, dict):
                return res.get("local_reasoning", "")
        except Exception as e:
            logger.warning(f"Awaiting local reasoning for execution_id={execution_id} timed out or failed: {e}")
    return ""


def local_reasoning_node(state: ResearchState) -> Dict[str, Any]:
    """
    Parallel Local Reasoning Branch (Hybrid Mode):
    Leverages Qwen3 1.7B to independently analyze the technical and conceptual context,
    providing established foundations for synthesis with fresh web research.
    """
    request_id = state.get("request_id", "req_unknown")
    execution_id = state.get("execution_id", "exec_unknown")
    conversation_id = state.get("conversation_id", None)
    query = state.get("query", "")
    intent = state.get("intent", {})
    stages = state.get("stages", [])
    t0 = time.time()

    event_bus.publish(
        request_id=request_id,
        execution_id=execution_id,
        conversation_id=conversation_id,
        node_id="local_reasoning",
        component_name="Local Reasoning Agent",
        component_type="reasoning_agent",
        event_type="REASONING_STARTED",
        execution_status="RUNNING",
        safe_task_summary=f"Synthesizing conceptual and architectural foundations for: '{query[:70]}...'",
        response_mode="HYBRID",
        current_stage="Preparing reasoning context",
        tool_name="Qwen3 1.7B",
        timestamp=t0
    )

    system_prompt = (
        "You are the Local Reasoning Agent in O.P.S. 2.0.\n"
        "Your task is to analyze the user's technical or conceptual query and provide the established "
        "architectural principles, fundamental concepts, and domain background from foundational knowledge.\n"
        "Rules:\n"
        "1. Focus on established principles, design patterns, core concepts, and mechanics.\n"
        "2. Do NOT invent or speculate about unverified current release numbers, prices, or recent dates.\n"
        "3. Explicitly identify what specific points need fresh web evidence verification.\n"
        "4. Structure your response clearly with concise bullet points."
    )

    user_prompt = (
        f"User Query: {query}\n"
        f"Intent Context: {intent.get('core_topic', query)}\n\n"
        "Provide the conceptual explanation, architectural context, and points requiring external verification:"
    )

    fallback_reasoning = (
        f"Conceptual Analysis for '{query}':\n"
        "- Fundamental domain principles and architectural mechanisms apply.\n"
        "- Requires live external verification for current releases, latest specifications, and recent benchmarks."
    )

    try:
        local_output = ollama_client.generate(
            model=MODEL_QWEN_1_7B,
            prompt=user_prompt,
            system_prompt=system_prompt,
            temperature=0.2,
            num_predict=512,
            num_ctx=2048,
            timeout=40.0
        )
    except Exception as e:
        logger.warning(f"Local reasoning node model error: {e}")
        local_output = fallback_reasoning

    duration = time.time() - t0

    event_bus.publish(
        request_id=request_id,
        execution_id=execution_id,
        conversation_id=conversation_id,
        node_id="local_reasoning",
        component_name="Local Reasoning Agent",
        component_type="reasoning_agent",
        event_type="NODE_COMPLETED",
        execution_status="COMPLETED",
        safe_task_summary=f"Local reasoning generated in {duration:.2f}s",
        safe_output_summary=local_output[:120] + "...",
        response_mode="HYBRID",
        current_stage="Preparing reasoning context",
        tool_name="Qwen3 1.7B",
        timestamp=time.time()
    )

    node_history = list(state.get("node_history", []))
    node_history.append("local_reasoning")

    return {
        "local_reasoning": local_output,
        "current_active_component": "local_reasoning",
        "node_history": node_history
    }
