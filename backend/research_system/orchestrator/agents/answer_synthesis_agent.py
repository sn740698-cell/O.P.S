"""
Agent 6: Answer Synthesis Agent
Group 2: Answering Engine
Model: Qwen3 1.7B (hf.co/Qwen/Qwen3-1.7B-GGUF:Q8_0)
Synthesizes verified research evidence with local reasoning into coherent, grounded
answers with verifiable inline source references.
"""

import time
import logging
from typing import Dict, Any, List
from research_system.orchestrator.state import CentralGraphState
from research_system.orchestrator.agents.base import emit_agent_started, emit_agent_completed, emit_agent_failed
from research_system.llm.ollama_client import get_ollama_client, MODEL_QWEN_1_7B

logger = logging.getLogger("OPS.Agent.AnswerSynthesis")

AGENT_ID = "answer_synthesis_agent"
AGENT_NAME = "Answer Synthesis Agent"
GROUP_ID = "answering_engine"
COMPONENT_TYPE = "reasoning_agent"


def answer_synthesis_agent_node(state: CentralGraphState) -> Dict[str, Any]:
    """
    Agent 6 node: Generates grounded final answer synthesizing external evidence
    and local reasoning into a coherent structured response.
    """
    t0 = time.time()
    query = state.get("user_query", "").strip()
    answering_mode = state.get("answering_mode", "WEB")
    local_output = state.get("local_reasoning_output", "")
    validated_evidence = state.get("validated_evidence", {})
    sources = validated_evidence.get("validated_sources", [])

    emit_agent_started(state, AGENT_ID, AGENT_NAME, GROUP_ID, COMPONENT_TYPE, f"Synthesizing {answering_mode} response...")

    try:
        ollama_client = get_ollama_client()

        # Build context prompt
        context_parts = []
        if local_output:
            context_parts.append(f"### Local Analytical Reasoning:\n{local_output}")

        if sources:
            source_lines = []
            for i, s in enumerate(sources, 1):
                source_lines.append(f"[{i}] {s.get('title')} ({s.get('url')}):\n{s.get('snippet')}")
            context_parts.append("### Verified Web Research Evidence:\n" + "\n\n".join(source_lines))

        joined_context = "\n\n".join(context_parts) if context_parts else "No external evidence retrieved."

        system_prompt = (
            "You are the Answer Synthesis Agent for O.P.S. 2.0. "
            "Synthesize a clear, authoritative, and factually grounded response for the user's query. "
            "Integrate both analytical insights and external facts seamlessly. "
            "Use inline bracketed citations [1], [2] when referencing external research facts. "
            "Maintain an articulate, confident, and professional technical tone."
        )

        user_prompt = (
            f"User Question:\n{query}\n\n"
            f"Verified Research & Analysis Context:\n{joined_context}\n\n"
            "Provide the synthesized final answer:"
        )

        synthesized_text = ollama_client.generate(
            model=MODEL_QWEN_1_7B,
            prompt=user_prompt,
            system_prompt=system_prompt,
            temperature=0.2,
            num_predict=2048
        )

        duration = round(time.time() - t0, 2)
        emit_agent_completed(
            state, AGENT_ID, AGENT_NAME, GROUP_ID, COMPONENT_TYPE,
            "Answer synthesis completed with source citations.",
            output_summary=synthesized_text[:120] + "...",
            duration_s=duration
        )

        return {
            "current_agent": AGENT_ID,
            "final_response": synthesized_text,
            "source_references": sources
        }

    except Exception as e:
        logger.error(f"Answer Synthesis Agent error: {e}")
        emit_agent_failed(state, AGENT_ID, AGENT_NAME, GROUP_ID, str(e))
        fallback = f"Synthesis error: {e}\n\n" + (local_output or "No response could be synthesized.")
        return {
            "current_agent": AGENT_ID,
            "final_response": fallback,
            "errors": [f"Synthesis failed: {e}"]
        }
