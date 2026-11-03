"""
Agent 4: Web Research Agent
Group 2: Answering Engine
Multi-tool Research Stack: HTTPX, Crawlee, BeautifulSoup4, ScrapeGraphAI, Playwright
Discovers external web sources, queries search providers, extracts cleaned content passages,
and compiles raw research evidence.
"""

import time
import logging
from typing import Dict, Any, List
from research_system.orchestrator.state import CentralGraphState
from research_system.orchestrator.agents.base import emit_agent_started, emit_agent_progress, emit_agent_completed, emit_agent_failed
from research_system.graph.workers.search_worker import search_worker_node
from research_system.graph.workers.url_selection_worker import url_selection_worker_node
from research_system.graph.workers.crawling_worker import crawling_worker_node
from research_system.graph.workers.content_extraction_worker import content_extraction_worker_node
from research_system.graph.workers.content_processing_worker import content_processing_worker_node
from research_system.events.event_bus import EventBus

logger = logging.getLogger("OPS.Agent.WebResearch")
event_bus = EventBus()

AGENT_ID = "web_research_agent"
AGENT_NAME = "Web Research Agent"
GROUP_ID = "answering_engine"
COMPONENT_TYPE = "execution_worker"


def web_research_agent_node(state: CentralGraphState) -> Dict[str, Any]:
    """
    Agent 4 node: Executes the multi-stage web research retrieval pipeline.
    Reuses existing O.P.S. search, crawling, and content extraction workers.
    """
    t0 = time.time()
    query = state.get("user_query", "").strip()
    req_id = state.get("request_id") or f"req_{state.get('task_id', 'task')}"
    conv_id = state.get("conversation_id")
    task_id = state.get("task_id", "task")

    emit_agent_started(state, AGENT_ID, AGENT_NAME, GROUP_ID, COMPONENT_TYPE, f"Initiating web research for: '{query[:60]}...'")

    try:
        # Build synthetic research state for the sub-workers
        from research_system.graph.state import ResearchState
        sub_state: ResearchState = {
            "conversation_id": conv_id,
            "request_id": req_id,
            "user_query": query,
            "core_topic": query,
            "key_entities": [],
            "complexity_level": "moderate",
            "is_ambiguous": False,
            "clarification_prompt": "",
            "subquestions": [query],
            "search_queries": [query],
            "raw_search_results": [],
            "selected_urls": [],
            "retrieved_pages": [],
            "extracted_contents": [],
            "processed_chunks": [],
            "analyzed_evidence": [],
            "evidence_gaps": [],
            "has_contradictions": False,
            "loop_count": 0,
            "max_loops": 1,
            "ranked_evidence": [],
            "final_answer": "",
            "citations": [],
            "errors": [],
            "current_step": "search",
            "start_time": time.time(),
            "telemetry": {}
        }

        # Step 4.1: Search Worker
        emit_agent_progress(state, AGENT_ID, AGENT_NAME, GROUP_ID, "Querying search provider for authoritative sources...")
        search_res = search_worker_node(sub_state)
        sub_state.update(search_res)

        sources_count = len(sub_state.get("raw_search_results", []))
        event_bus.publish(
            request_id=req_id,
            execution_id=task_id,
            conversation_id=conv_id,
            node_id=AGENT_ID,
            component_name=AGENT_NAME,
            component_type=COMPONENT_TYPE,
            event_type="SEARCH_COMPLETED",
            execution_status="ACTIVE",
            safe_task_summary=f"Discovered {sources_count} potential source(s).",
            sources_discovered=sources_count,
            timestamp=time.time()
        )

        # Step 4.2: URL Selection Worker
        url_res = url_selection_worker_node(sub_state)
        sub_state.update(url_res)
        selected_urls = sub_state.get("selected_urls", [])

        # Step 4.3: Crawling Worker (HTTPX connection pooling & Crawlee)
        emit_agent_progress(state, AGENT_ID, AGENT_NAME, GROUP_ID, f"Retrieving page contents across {len(selected_urls)} target domain(s)...")
        crawl_res = crawling_worker_node(sub_state)
        sub_state.update(crawl_res)

        pages_count = len(sub_state.get("retrieved_pages", []))
        event_bus.publish(
            request_id=req_id,
            execution_id=task_id,
            conversation_id=conv_id,
            node_id=AGENT_ID,
            component_name=AGENT_NAME,
            component_type=COMPONENT_TYPE,
            event_type="PAGE_RETRIEVED",
            execution_status="ACTIVE",
            safe_task_summary=f"Retrieved and normalized {pages_count} external webpage(s).",
            pages_retrieved=pages_count,
            timestamp=time.time()
        )

        # Step 4.4: Content Extraction Worker (BeautifulSoup4 & ScrapeGraphAI)
        extract_res = content_extraction_worker_node(sub_state)
        sub_state.update(extract_res)

        # Step 4.5: Content Processing Worker (Chunking and semantic normalization)
        proc_res = content_processing_worker_node(sub_state)
        sub_state.update(proc_res)

        processed_chunks = sub_state.get("processed_chunks", [])
        retrieved_pages = sub_state.get("retrieved_pages", [])

        research_results = {
            "search_queries": sub_state.get("search_queries", [query]),
            "selected_urls": selected_urls,
            "pages_retrieved": len(retrieved_pages),
            "chunks_count": len(processed_chunks),
            "chunks": processed_chunks[:12],  # Cap representative passages
            "sources": [
                {
                    "title": p.get("title", "Online Source"),
                    "url": p.get("url", ""),
                    "snippet": (p.get("text", "")[:200] + "...") if p.get("text") else ""
                }
                for p in retrieved_pages[:5]
            ]
        }

        duration = round(time.time() - t0, 2)
        emit_agent_completed(
            state, AGENT_ID, AGENT_NAME, GROUP_ID, COMPONENT_TYPE,
            f"Web research completed across {len(selected_urls)} source(s) and {len(processed_chunks)} passage(s).",
            output_summary=f"{len(selected_urls)} sources retrieved in {duration}s",
            duration_s=duration
        )

        return {
            "current_agent": AGENT_ID,
            "research_results": research_results
        }

    except Exception as e:
        logger.error(f"Web Research Agent error: {e}")
        emit_agent_failed(state, AGENT_ID, AGENT_NAME, GROUP_ID, str(e))
        return {
            "current_agent": AGENT_ID,
            "research_results": {
                "sources": [],
                "chunks": [],
                "error": str(e)
            },
            "errors": [f"Web research failed: {e}"]
        }
