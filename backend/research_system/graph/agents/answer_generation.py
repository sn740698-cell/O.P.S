"""
O.P.S. 2.0 — Answer Generation Agent
Reasoning Agent 4: Synthesizes final evidence-grounded responses embodying
the JARVIS-inspired persona and professional Markdown formatting.
Includes continuous '📌 Discussion So Far' active conversation summary.
"""

import time
import logging
from typing import Dict, Any, List
from research_system.graph.state import ResearchState
from research_system.events.event_bus import event_bus
from research_system.llm.ollama_client import ollama_client, MODEL_QWEN_1_7B, MODEL_LLAMA_1B
from research_system.graph.agents.local_reasoning import await_local_reasoning, local_reasoning_node
from research_system.services.conversation_summary import (
    generate_updated_summary,
    attach_summary_to_response,
    extract_summary_from_text,
    SUMMARY_HEADING
)

logger = logging.getLogger(__name__)


def answer_generation_node(state: ResearchState) -> Dict[str, Any]:
    """
    Reasoning Agent 4: Answer Generation Agent
    Model: Qwen3 1.7B
    Synthesizes the final evidence-based response with JARVIS persona,
    professional Markdown (headings, tables, lists, emojis, code blocks),
    and appends the continuous '📌 Discussion So Far' conversation summary.
    """
    request_id = state.get("request_id", "req_unknown")
    execution_id = state.get("execution_id", "exec_unknown")
    conversation_id = state.get("conversation_id", None)
    query = state.get("query", "")
    conversation_history = state.get("conversation_history", [])
    conversation_summary = state.get("conversation_summary", "")
    evidence_items = state.get("retrieved_evidence", [])
    if not evidence_items:
        evidence_items = state.get("processed_chunks", [])[:8]

    contradictions = state.get("contradictions", [])
    is_sufficient = state.get("is_sufficient", True)
    response_mode = state.get("response_mode") or "WEB"

    t0 = time.time()
    current_stage = "Combining knowledge and evidence" if response_mode == "HYBRID" else "Generating answer"

    event_bus.publish(
        request_id=request_id,
        execution_id=execution_id,
        conversation_id=conversation_id,
        node_id="answer_generation",
        component_name="Answer Generation Agent",
        component_type="reasoning_agent",
        event_type="ANSWER_GENERATING",
        execution_status="RUNNING",
        safe_task_summary=f"Synthesizing [{response_mode}] response for: '{query[:80]}...'",
        response_mode=response_mode,
        current_stage=current_stage,
        tool_name="Qwen3 1.7B",
        timestamp=t0
    )

    # In Hybrid mode, retrieve the concurrent local reasoning output
    local_reasoning = ""
    if response_mode == "HYBRID":
        local_reasoning = await_local_reasoning(execution_id, timeout=20.0)
        if not local_reasoning:
            local_reasoning = state.get("local_reasoning", "")
        if not local_reasoning:
            try:
                lr_res = local_reasoning_node(state)
                local_reasoning = lr_res.get("local_reasoning", "")
            except Exception as e:
                logger.warning(f"Fallback local reasoning failed: {e}")

    # Format numbered evidence references for factual grounding
    evidence_blocks = []
    for idx, item in enumerate(evidence_items, start=1):
        domain = item.get("domain", "")
        evidence_blocks.append(
            f"[{idx}] Source: {item.get('title', 'Web Source')} ({item.get('url', 'N/A')}) [Domain: {domain}]\n"
            f"Evidence Snippet: {item.get('text', '')[:450]}"
        )
    formatted_evidence = "\n\n".join(evidence_blocks) if evidence_blocks else "No external evidence retrieved."

    # Format chronological conversation context for multi-turn dialogue
    history_str = ""
    if conversation_history:
        recent = conversation_history[-5:]
        history_str = "Prior Conversation Context:\n" + "\n".join(
            f"- {turn.get('role', 'user').upper()}: {turn.get('content', '')[:180]}"
            for turn in recent
        ) + "\n\n"

    # Format contradictions and insufficiency disclosures if detected
    contradictions_text = ""
    if contradictions:
        contradictions_text = "\nDetected Conflicting Evidence Across Sources:\n" + "\n".join(
            f"- Inconsistency in {c.get('topic', 'topic')}: Source A says '{c.get('claim_a')}', while Source B says '{c.get('claim_b')}'."
            for c in contradictions
        ) + "\nDirective: Report the disagreement objectively, contrast both perspectives, and cite respective sources.\n"

    insufficiency_note = ""
    if not is_sufficient or not evidence_items:
        insufficiency_note = (
            "\nNote on Evidence Completeness: Research evidence was partial or inconclusive. "
            "Do NOT speculate or fabricate unverified details. Disclose what could be verified and what remains unconfirmed.\n"
        )

    # JARVIS-Inspired Personality System Prompt
    system_prompt = (
        "You are O.P.S., a sophisticated personal AI assistant inspired by JARVIS from Iron Man.\n\n"
        "PERSONALITY & TONE:\n"
        "- Intelligent, articulate, courteous, calm, and composed.\n"
        "- Confident without being arrogant; helpful, proactive, and technically astute.\n"
        "- Communicates in polished, natural English with a calm assistant demeanor.\n"
        "- Concise when a brief reply is sufficient; detailed and structured when explanations are requested.\n"
        "- Avoid robotic language, repetitive throat-clearing, or excessive emojis.\n\n"
        "FACTUAL GROUNDING & ANTI-HALLUCINATION RULES:\n"
        "1. For external factual questions, release versions, dates, benchmarks, or specs, use ONLY the verified evidence.\n"
        "2. Cite external facts inline using [1], [2] matching the provided sources.\n"
        "3. Never invent release numbers, launch dates, prices, or specifications.\n"
        "4. If official evidence is missing or inconclusive, state clearly what could not be verified.\n"
        "5. If sources contradict each other, present both sides objectively.\n\n"
        "FORMATTING GUIDELINES:\n"
        "- Headings (##, ###) for structured topics\n"
        "- Bullet points (- ) and numbered lists (1., 2.)\n"
        "- Markdown tables (| Column | Details |) for comparisons\n"
        "- Fenced code blocks (```python ... ```) with language tags\n"
        "- Emojis (💡, ⚙️, 🚀, ✅, ⚠️, 🔍, 🧠, 📌) used naturally\n\n"
        "MANDATORY END SECTION:\n"
        "At the very end of your response, you MUST append a separate section titled:\n"
        "## 📌 Discussion So Far\n"
        "List 3 to 5 concise bullet points summarizing the discussion up to this point.\n"
    )

    if response_mode == "HYBRID":
        mode_instructions = (
            "RESPONSE MODE: HYBRID (Local Reasoning + Live External Evidence)\n"
            f"FOUNDATIONAL CONCEPTUAL REASONING:\n{local_reasoning}\n\n"
            "SYNTHESIS INSTRUCTIONS:\n"
            "- Seamlessly synthesize the architectural/conceptual foundations with fresh external findings into ONE unified response.\n"
            "- Ground all current specifications, release versions, and recent data in the verified evidence with [1], [2].\n"
            "- Do not repeat points twice or produce two disjointed sections.\n"
            f"{contradictions_text}"
            f"{insufficiency_note}"
        )
    else:
        mode_instructions = (
            "RESPONSE MODE: WEB (Evidence-Grounded Retrieval)\n"
            "SYNTHESIS INSTRUCTIONS:\n"
            "- Ground all factual answers strictly in the Verified Evidence below using [1], [2].\n"
            "- If the verified evidence does not contain the answer, state:\n"
            "  'I searched for current information about [topic], but could not verify [detail] from official sources.'\n"
            f"{contradictions_text}"
            f"{insufficiency_note}"
        )

    user_prompt = (
        f"{history_str}"
        f"{mode_instructions}\n"
        f"Active User Directive: {query}\n\n"
        f"Verified Evidence:\n{formatted_evidence}\n\n"
        "Provide your professional, JARVIS-styled synthesis followed by '## 📌 Discussion So Far':"
    )

    final_text = ""
    try:
        def on_token_chunk(token: str):
            event_bus.publish_text_chunk(
                request_id=request_id,
                execution_id=execution_id,
                chunk=token,
                conversation_id=conversation_id
            )

        final_text = ollama_client.generate_stream(
            model=MODEL_QWEN_1_7B,
            prompt=user_prompt,
            system_prompt=system_prompt,
            temperature=0.3,
            on_token=on_token_chunk,
            bypass_thinking=True,
            timeout=90.0
        )
    except Exception as e:
        logger.warning(f"Ollama generation encountered error ({e}), synthesizing structured JARVIS fallback.")
        # Fallback structured JARVIS synthesis
        final_text = (
            f"Certainly. Here is the synthesized briefing regarding **{query}**.\n\n"
            f"### 🔍 Key Findings & Intelligence\n\n"
        )
        if evidence_items:
            for idx, item in enumerate(evidence_items[:4], start=1):
                title = item.get("title", "Verified Source")
                snippet = item.get("text", "")[:240].strip()
                final_text += f"- **{title}** [{idx}]: {snippet}...\n"
        else:
            final_text += f"No verified documentation or external records could be found regarding '{query}'. The requested claim or feature cannot be verified from official sources.\n\n"

        final_text += "\n💡 *Additional specialized workflows can be executed upon your directive.*"

    # Ensure '## 📌 Discussion So Far' is attached
    extracted_summary = extract_summary_from_text(final_text)
    if not extracted_summary:
        # Dynamically generate summary bullets
        summary_bullets = generate_updated_summary(
            previous_summary=conversation_summary,
            conversation_turns=conversation_history,
            latest_query=query,
            latest_answer=final_text
        )
        final_text = attach_summary_to_response(final_text, summary_bullets)
    else:
        summary_bullets = extracted_summary

    duration = time.time() - t0

    event_bus.publish(
        request_id=request_id,
        execution_id=execution_id,
        conversation_id=conversation_id,
        node_id="answer_generation",
        component_name="Answer Generation Agent",
        component_type="reasoning_agent",
        event_type="NODE_COMPLETED",
        execution_status="COMPLETED",
        safe_task_summary=f"Synthesized evidence-based JARVIS response ({len(final_text)} chars) in {duration:.2f}s",
        safe_output_summary=final_text[:180] + "...",
        tool_name="Qwen3 1.7B",
        timestamp=time.time()
    )

    node_history = list(state.get("node_history", []))
    node_history.append("answer_generation")

    return {
        "final_answer": final_text,
        "conversation_summary": summary_bullets,
        "current_active_component": "answer_generation",
        "node_history": node_history
    }
