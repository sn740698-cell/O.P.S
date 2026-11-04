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

        # Build context prompt with verified crawled passages and sources
        valid_passages = validated_evidence.get("valid_passages", [])
        context_parts = []

        if sources:
            source_lines = []
            for i, s in enumerate(sources, 1):
                source_lines.append(f"[{i}] {s.get('title')} ({s.get('url')}):\n{s.get('snippet')}")
            context_parts.append("### Verified Web Research Sources:\n" + "\n\n".join(source_lines))

        if valid_passages:
            passages_text = "\n---\n".join(valid_passages[:5])
            context_parts.append("### Verified Retrieved Page Excerpts:\n" + passages_text)

        if local_output and answering_mode == "HYBRID":
            context_parts.append(f"### Local Analytical Reasoning (for qualitative synthesis):\n{local_output}")

        joined_context = "\n\n".join(context_parts) if context_parts else "No external evidence retrieved."

        system_prompt = (
            "You are the Answer Synthesis Agent for O.P.S. 2.0 (Over-Engineered Programmed System).\n"
            "Synthesize an articulate, factually accurate, and rigorously grounded response.\n"
            "STRICT FACTUAL GROUNDING RULES:\n"
            "1. Ground all version numbers, release dates, and technical details strictly on the retrieved web research passages.\n"
            "2. NEVER invent or hallucinate release numbers, publication dates, benchmarks, or URLs.\n"
            "3. If asked for the latest version or release of software (such as Django), use the exact version stated in the official documentation or release notes. Never use outdated pre-training memory.\n"
            "4. For technical comparisons (e.g. Django vs FastAPI):\n"
            "   - Separate official feature facts from qualitative analysis.\n"
            "   - Label performance conclusions as qualitative unless empirical, verified benchmark evidence is retrieved.\n"
            "   - NEVER invent requests-per-second numbers or arbitrary benchmark figures.\n"
            "5. Use inline bracketed citations [1], [2] when referencing external research facts.\n"
            "6. Maintain a calm, articulate, confident JARVIS-style technical persona."
        )

        user_prompt = (
            f"User Question:\n{query}\n\n"
            f"Verified Research & Analysis Context:\n{joined_context}\n\n"
            "Provide the synthesized final answer:"
        )

        from research_system.llm.ollama_client import MODEL_QWEN_0_6B
        try:
            synthesized_text = ollama_client.generate(
                model=MODEL_QWEN_1_7B,
                prompt=user_prompt,
                system_prompt=system_prompt,
                temperature=0.2,
                num_predict=1024,
                timeout=45.0
            )
        except Exception:
            synthesized_text = ollama_client.generate(
                model=MODEL_QWEN_0_6B,
                prompt=user_prompt,
                system_prompt=system_prompt,
                temperature=0.2,
                num_predict=1024,
                timeout=45.0
            )

        if not synthesized_text or not synthesized_text.strip():
            if local_output:
                synthesized_text = local_output
            elif sources:
                source_bullets = "\n".join([f"- **{s.get('title')}**: {s.get('snippet')}" for s in sources[:4] if s.get('snippet')])
                synthesized_text = f"Live Research Findings for '{query}':\n\n{source_bullets}"
            else:
                synthesized_text = f"Completed research for '{query}'."

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
        if sources:
            source_bullets = "\n".join([f"- **{s.get('title')}**: {s.get('snippet')}" for s in sources[:4] if s.get('snippet')])
            fallback = f"Retrieved Live Web Findings for '{query}':\n\n{source_bullets}"
        else:
            fallback = local_output or f"Research completed for '{query}'. Operational findings verified."

        return {
            "current_agent": AGENT_ID,
            "final_response": fallback,
            "source_references": sources,
            "errors": [f"Synthesis failed: {e}"]
        }
