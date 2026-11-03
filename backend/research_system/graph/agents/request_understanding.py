import time
import logging
from typing import Dict, Any, List
from research_system.graph.state import ResearchState
from research_system.events.event_bus import event_bus
from research_system.llm.ollama_client import ollama_client, MODEL_QWEN_1_7B, MODEL_QWEN_0_6B
from research_system.graph.agents.local_reasoning import start_local_reasoning

logger = logging.getLogger(__name__)

def request_understanding_node(state: ResearchState) -> Dict[str, Any]:
    """
    Reasoning Agent 1: Request Understanding Agent
    Model: Qwen3 1.7B
    Understands user request, identifies research intent, determines complexity,
    and resolves conversational follow-up references ('it', 'that', 'continue', 'previous result').
    """
    request_id = state.get("request_id", "req_unknown")
    execution_id = state.get("execution_id", "exec_unknown")
    query = state.get("query", "")
    conversation_history = state.get("conversation_history", [])
    conversation_summary = state.get("conversation_summary", "")
    t0 = time.time()

    event_bus.publish(
        request_id=request_id,
        execution_id=execution_id,
        node_id="request_understanding",
        component_name="Request Understanding Agent",
        component_type="reasoning_agent",
        event_type="NODE_STARTED",
        execution_status="RUNNING",
        safe_task_summary=f"Analyzing intent & conversational context for: '{query[:80]}...'",
        tool_name="Qwen3 0.6B",
        timestamp=t0
    )

    # Format recent conversation context for pronoun & reference resolution
    context_str = ""
    if conversation_history:
        recent_turns = conversation_history[-6:]
        context_str = "\nRecent Conversation History:\n" + "\n".join(
            f"- {turn.get('role', 'user').upper()}: {turn.get('content', '')[:160]}"
            for turn in recent_turns
        ) + "\n"
    elif conversation_summary:
        context_str = f"\nConversation Summary: {conversation_summary[:200]}\n"

    system_prompt = (
        "You are the Request Understanding Agent in O.P.S. 2.0. "
        "Analyze the user's research request. If the user refers to previous context "
        "(e.g., 'it', 'that', 'continue', 'tell me more', 'previous result', 'do the same thing'), "
        "resolve the references using the conversation history to identify the true subject. "
        "Respond strictly in valid JSON with fields: "
        "'intent_category' (e.g. FACTUAL, COMPARISON, TECHNICAL, FOLLOW_UP, CURRENT_AFFAIRS), "
        "'core_topic' (fully resolved specific topic, replacing pronouns with actual subjects), "
        "'complexity' ('simple' or 'complex'), "
        "'key_entities' (list of strings)."
    )

    user_prompt = f"{context_str}\nCurrent User Request: {query}\n\nProvide the JSON analysis."

    fallback_topic = query[:60]
    # Simple heuristic fallback if model fails: if pronouns present and history exists, append last bot subject
    if conversation_history and any(w in query.lower().split() for w in ["it", "that", "this", "its", "continue", "same"]):
        last_turn = conversation_history[-1].get("content", "")
        fallback_topic = f"{query} (context: {last_turn[:40]})"

    fallback = {
        "intent_category": "FOLLOW_UP" if conversation_history else "FACTUAL",
        "core_topic": fallback_topic,
        "complexity": "simple" if len(query.split()) < 7 else "complex",
        "key_entities": [w for w in query.split() if len(w) > 3][:4]
    }

    intent_data = ollama_client.generate_json(
        model=MODEL_QWEN_1_7B,
        prompt=user_prompt,
        system_prompt=system_prompt,
        default_fallback=fallback
    )

    is_simple = intent_data.get("complexity", "complex").lower() == "simple"
    duration = time.time() - t0

    event_bus.publish(
        request_id=request_id,
        execution_id=execution_id,
        node_id="request_understanding",
        component_name="Request Understanding Agent",
        component_type="reasoning_agent",
        event_type="NODE_COMPLETED",
        execution_status="COMPLETED",
        safe_task_summary=f"Identified intent: {intent_data.get('intent_category')} (complexity: {intent_data.get('complexity')})",
        safe_output_summary=f"Resolved Topic: {intent_data.get('core_topic')} | Entities: {', '.join(intent_data.get('key_entities', []))}",
        tool_name="Qwen3 0.6B",
        timestamp=time.time()
    )

    response_mode = state.get("response_mode", "WEB")
    if response_mode == "HYBRID":
        # Launch concurrent background local reasoning branch immediately
        start_local_reasoning(state)

    node_history = list(state.get("node_history", []))
    node_history.append("request_understanding")

    return {
        "intent": intent_data,
        "is_simple_query": is_simple,
        "current_active_component": "request_understanding",
        "node_history": node_history
    }
