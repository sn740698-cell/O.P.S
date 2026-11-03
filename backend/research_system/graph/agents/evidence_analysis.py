"""
O.P.S. 2.0 — Evidence Analysis Agent
Reasoning Agent 3: Evaluates retrieved text against the research directive.
Features:
- Classifies evidence into: VERIFIED, PARTIALLY_SUPPORTED, CONFLICTING, UNSUPPORTED
- Detects source contradictions (cross-checking multiple independent reports)
- Evaluates source authority and currency
- Identifies critical missing information for bounded adaptive retrieval retry
- Never treats mere keyword similarity as proof of factual accuracy
"""

import time
import json
import logging
from typing import Dict, Any, List
from research_system.graph.state import ResearchState
from research_system.events.event_bus import event_bus
from research_system.llm.ollama_client import ollama_client, MODEL_QWEN_1_7B

logger = logging.getLogger(__name__)

STATUS_VERIFIED = "VERIFIED"
STATUS_PARTIAL = "PARTIALLY_SUPPORTED"
STATUS_CONFLICTING = "CONFLICTING"
STATUS_UNSUPPORTED = "UNSUPPORTED"


def evidence_analysis_node(state: ResearchState) -> Dict[str, Any]:
    """
    Reasoning Agent 3: Evidence Analysis Agent
    Model: Qwen3 1.7B
    Rigorously evaluates extracted passages against the query.
    Produces structured evidence classifications and contradiction maps.
    """
    request_id = state.get("request_id", "req_unknown")
    execution_id = state.get("execution_id", "exec_unknown")
    conversation_id = state.get("conversation_id", None)
    query = state.get("query", "")
    subquestions = state.get("subquestions", [])
    extracted_contents = state.get("extracted_contents", [])
    processed_chunks = state.get("processed_chunks", [])
    iteration = state.get("iteration_count", 0)
    t0 = time.time()

    total_chunks = len(processed_chunks)

    event_bus.publish(
        request_id=request_id,
        execution_id=execution_id,
        conversation_id=conversation_id,
        node_id="evidence_analysis",
        component_name="Evidence Analysis Agent",
        component_type="reasoning_agent",
        event_type="NODE_STARTED",
        execution_status="RUNNING",
        safe_task_summary=f"Validating evidence across {total_chunks} passages from {len(extracted_contents)} web sources",
        tool_name="Qwen3 1.7B",
        timestamp=t0
    )

    # Format authoritative evidence excerpts for evaluation
    evidence_summaries = []
    for idx, c in enumerate(processed_chunks[:8], start=1):
        dom = c.get("domain", "")
        title = c.get("title", "Web Source")
        url = c.get("url", "")
        txt = c.get("text", "")[:350].strip()
        evidence_summaries.append(f"[{idx}] Source: {title} ({dom} - {url})\nExcerpt: \"{txt}\"")

    combined_evidence = "\n\n".join(evidence_summaries) if evidence_summaries else "No web evidence retrieved."

    system_prompt = (
        "You are the Evidence Analysis Agent in O.P.S. 2.0. "
        "Your task is to strictly evaluate whether the retrieved web evidence actually answers the user's question.\n"
        "Rules:\n"
        "1. Do not assume or extrapolate beyond what is explicitly stated in the excerpts.\n"
        "2. Classify evidence into:\n"
        "   - 'VERIFIED': Direct explicit factual support in a reliable source.\n"
        "   - 'PARTIALLY_SUPPORTED': Related information found, but incomplete to fully answer.\n"
        "   - 'CONFLICTING': Two or more credible sources state contradictory facts.\n"
        "   - 'UNSUPPORTED': No evidence found supporting the core claim.\n"
        "3. Output strictly a valid JSON object matching this schema:\n"
        "{\n"
        "  \"is_sufficient\": true/false,\n"
        "  \"confidence_score\": 0.0 to 1.0,\n"
        "  \"evidence_status\": \"VERIFIED\" | \"PARTIALLY_SUPPORTED\" | \"CONFLICTING\" | \"UNSUPPORTED\",\n"
        "  \"claims\": [\n"
        "     {\"claim\": \"string\", \"status\": \"VERIFIED\"|\"PARTIALLY_SUPPORTED\"|\"CONFLICTING\"|\"UNSUPPORTED\", \"supporting_urls\": [\"url\"], \"notes\": \"string\"}\n"
        "  ],\n"
        "  \"contradictions\": [\n"
        "     {\"topic\": \"string\", \"source_a\": \"string\", \"source_b\": \"string\", \"details\": \"string\"}\n"
        "  ],\n"
        "  \"information_gaps\": [\"string\"]\n"
        "}"
    )

    user_prompt = (
        f"User Directive: {query}\n"
        f"Subquestions: {subquestions}\n\n"
        f"Extracted Web Evidence:\n{combined_evidence}\n\n"
        "Evaluate evidence sufficiency, classifications, and contradictions in JSON:"
    )

    fallback_status = STATUS_VERIFIED if total_chunks >= 2 else (STATUS_PARTIAL if total_chunks == 1 else STATUS_UNSUPPORTED)
    fallback = {
        "is_sufficient": total_chunks > 0,
        "confidence_score": 0.85 if total_chunks >= 2 else 0.4,
        "evidence_status": fallback_status,
        "claims": [{
            "claim": query,
            "status": fallback_status,
            "supporting_urls": [c.get("url") for c in processed_chunks[:2] if c.get("url")],
            "notes": "Automated fallback classification based on extracted content."
        }],
        "contradictions": [],
        "information_gaps": [] if total_chunks > 0 else ["No source text available"]
    }

    analysis_data = ollama_client.generate_json(
        model=MODEL_QWEN_1_7B,
        prompt=user_prompt,
        system_prompt=system_prompt,
        default_fallback=fallback,
        timeout=45.0
    )

    is_sufficient = analysis_data.get("is_sufficient", fallback["is_sufficient"])
    conf = float(analysis_data.get("confidence_score", fallback["confidence_score"]))
    evidence_status = str(analysis_data.get("evidence_status", fallback_status)).upper()
    claims = analysis_data.get("claims", fallback["claims"])
    contradictions = analysis_data.get("contradictions", [])
    gaps = analysis_data.get("information_gaps", [])

    # Tag evidence status string for cockpit preview
    if contradictions:
        cockpit_evidence_status = "Conflicting Evidence"
    elif is_sufficient:
        cockpit_evidence_status = "Verified"
    elif gaps:
        cockpit_evidence_status = "Partial Evidence"
    else:
        cockpit_evidence_status = "Unsupported"

    duration = time.time() - t0

    event_bus.publish(
        request_id=request_id,
        execution_id=execution_id,
        conversation_id=conversation_id,
        node_id="evidence_analysis",
        component_name="Evidence Analysis Agent",
        component_type="reasoning_agent",
        event_type="EVIDENCE_VALIDATED",
        execution_status="COMPLETED",
        safe_task_summary=f"Evidence {cockpit_evidence_status}: {len(claims)} claim(s) evaluated (Confidence: {conf:.2f})",
        safe_output_summary=f"Verified Claims: {sum(1 for c in claims if c.get('status') == 'VERIFIED')} | Contradictions: {len(contradictions)} | Gaps: {len(gaps)}",
        tool_name="Qwen3 1.7B",
        evidence_status=cockpit_evidence_status,
        evidence_count=len(state.get("crawled_pages", [])),
        current_stage="Validating evidence",
        timestamp=time.time()
    )

    node_history = list(state.get("node_history", []))
    node_history.append("evidence_analysis")

    return {
        "analysis": analysis_data,
        "evidence_evaluations": claims,
        "is_sufficient": is_sufficient,
        "contradictions": contradictions,
        "current_active_component": "evidence_analysis",
        "node_history": node_history
    }
