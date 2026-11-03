"""
Agent 3: Local Reasoning Agent
Group 2: Answering Engine
Model: Qwen3 1.7B (hf.co/Qwen/Qwen3-1.7B-GGUF:Q8_0)
Performs local reasoning, answers general knowledge questions, explains technical
concepts, programming logic, and code structures without external web crawling.
"""

import time
import logging
from typing import Dict, Any
from research_system.orchestrator.state import CentralGraphState
from research_system.orchestrator.agents.base import emit_agent_started, emit_agent_completed, emit_agent_failed
from research_system.llm.ollama_client import get_ollama_client, MODEL_QWEN_1_7B

logger = logging.getLogger("OPS.Agent.LocalReasoning")

AGENT_ID = "local_reasoning_agent"
AGENT_NAME = "Local Reasoning Agent"
GROUP_ID = "answering_engine"
COMPONENT_TYPE = "reasoning_agent"


def local_reasoning_agent_node(state: CentralGraphState) -> Dict[str, Any]:
    """
    Agent 3 node: Executes local analytical reasoning using Qwen3 1.7B.
    """
    t0 = time.time()
    query = state.get("user_query", "").strip()
    emit_agent_started(state, AGENT_ID, AGENT_NAME, GROUP_ID, COMPONENT_TYPE, f"Reasoning locally on: '{query[:60]}'...")

    try:
        ollama_client = get_ollama_client()
        conv_id = state.get("conversation_id", "")
        answering_mode = state.get("answering_mode", "LLM")
        is_doc_mode = (answering_mode == "DOCUMENT") or state.get("rag_retrieval_active", False)

        from research_system.services.temporary_rag_service import get_temporary_rag_service
        rag_service = get_temporary_rag_service()

        if is_doc_mode and conv_id and rag_service.has_active_documents(conv_id):
            # 1. Retrieve relevant passages from temporary Pinecone namespace
            emit_agent_started(state, AGENT_ID, AGENT_NAME, GROUP_ID, COMPONENT_TYPE, "Retrieving passages from temporary document vector store...")
            passages = rag_service.query_context(conversation_id=conv_id, query=query, top_k=4)

            if not passages:
                response_text = (
                    f"Sir, the active document context does not contain information regarding '{query}'. "
                    f"No matching sections, tables, or relevant text excerpts were found in the uploaded document."
                )
                sources = []
            else:
                passages_text = "\n\n".join([
                    f"--- [Document: {p['doc_name']} | Page: {p['page']} | Section: {p['section']}] ---\n{p['text']}"
                    for p in passages
                ])
                sources = [
                    {
                        "title": f"{p['doc_name']} (Page {p['page']})",
                        "url": f"document://{p['doc_id']}/page/{p['page']}",
                        "section": p.get("section", "General"),
                        "snippet": p["text"][:160]
                    }
                    for p in passages
                ]

                system_prompt = (
                    "You are the Document Intelligence Reasoning Agent of O.P.S. 2.0 (Over-Engineered Programmed System).\n"
                    "Your objective is to answer the user's question strictly and accurately based on the provided document excerpts.\n"
                    "Grounding Rules:\n"
                    "1. Answer truthfully using ONLY the provided document passages. Do NOT invent, assume, or extrapolate facts.\n"
                    "2. If the document does not contain the answer, explicitly state that the document does not provide the information.\n"
                    "3. Format your response cleanly using structured bullet points for key items, findings, and explanations.\n"
                    "4. Include specific document, page, and section citations in your answer."
                )

                doc_prompt = (
                    f"Retrieved Document Context:\n{passages_text}\n\n"
                    f"User Query:\n{query}\n\n"
                    f"Provide an accurate, grounded answer strictly based on the excerpts above."
                )

                response_text = ollama_client.generate(
                    model=MODEL_QWEN_1_7B,
                    prompt=doc_prompt,
                    system_prompt=system_prompt,
                    temperature=0.1,
                    num_predict=1536
                )

            duration = round(time.time() - t0, 2)
            snippet = response_text[:120] + "..." if len(response_text) > 120 else response_text
            emit_agent_completed(
                state, AGENT_ID, AGENT_NAME, GROUP_ID, COMPONENT_TYPE,
                f"Document-grounded answer synthesized ({len(sources)} citations).",
                output_summary=snippet,
                duration_s=duration
            )

            return {
                "current_agent": AGENT_ID,
                "local_reasoning_output": response_text,
                "source_references": sources,
                "retrieved_document_chunks": passages
            }

        # Normal Local Reasoning
        system_prompt = (
            "You are the Local Reasoning Agent of O.P.S. 2.0 (Over-Engineered Programmed System). "
            "Your role is to provide deep, technically rigorous, clear, and comprehensive explanations "
            "using your local reasoning capabilities. Explain concepts thoroughly with structured sections, "
            "code examples where relevant, and clear conceptual breakdowns."
        )

        response_text = ollama_client.generate(
            model=MODEL_QWEN_1_7B,
            prompt=f"User Query:\n{query}\n\nProvide a comprehensive, authoritative explanation.",
            system_prompt=system_prompt,
            temperature=0.2,
            num_predict=512
        )

        duration = round(time.time() - t0, 2)
        snippet = response_text[:120] + "..." if len(response_text) > 120 else response_text
        emit_agent_completed(
            state, AGENT_ID, AGENT_NAME, GROUP_ID, COMPONENT_TYPE,
            "Local reasoning generated successfully.",
            output_summary=snippet,
            duration_s=duration
        )

        return {
            "current_agent": AGENT_ID,
            "local_reasoning_output": response_text
        }

    except Exception as e:
        logger.error(f"Local Reasoning Agent error: {e}")
        emit_agent_failed(state, AGENT_ID, AGENT_NAME, GROUP_ID, str(e))
        return {
            "current_agent": AGENT_ID,
            "local_reasoning_output": f"Local reasoning fallback: Could not complete inference ({e})",
            "errors": [f"Local reasoning failed: {e}"]
        }
