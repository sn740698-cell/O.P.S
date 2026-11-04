"""
Agent 4: Web Research Agent (Crawlee + BeautifulSoup4 Redesign)
Group 2: Answering Engine

Architecture:
1. Query Understanding & Decomposition:
   - Analyzes intent, temporal freshness requirements (latest/current), and target entities.
   - Generates targeted official search queries (official releases, documentation).
2. Authoritative Source Discovery:
   - Discovers candidate URLs across search backends prioritizing primary documentation.
   - Ranks and filters using URL Selection Worker.
3. Crawlee Crawling Engine:
   - Employs Crawlee BeautifulSoupCrawler for controlled, concurrent, and resilient HTML retrieval.
4. BeautifulSoup4 Extraction Engine:
   - Extracts structured headings, body paragraphs, GitHub-flavored markdown tables, lists, and links.
   - Filters boilerplate and assigns explicit extraction status (SUCCESS, INSUFFICIENT_CONTENT, EXTRACTION_FAILED).
5. Evidence Compilation:
   - Formats evidence with stable canonical Source IDs ([S1], [S2], [S3]).
"""

import time
import re
import logging
from typing import Dict, Any, List

from research_system.orchestrator.state import CentralGraphState
from research_system.orchestrator.agents.base import (
    emit_agent_started, emit_agent_progress, emit_agent_completed, emit_agent_failed
)
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


def _understand_and_decompose_query(query: str) -> Dict[str, Any]:
    """
    Decomposes the user query into structured search parameters:
    - requires_freshness: whether the user seeks the latest/current version or news
    - is_comparison: whether multiple technologies/entities are compared
    - target_entities: extracted tech/software names
    - generated_queries: list of search query strings optimized for authoritative retrieval
    """
    q_lower = query.lower()

    # Freshness / temporal keywords
    freshness_words = ["latest", "current", "newest", "recent", "today", "now", "release", "version", "2025", "2026"]
    requires_freshness = any(w in q_lower for w in freshness_words)

    # Comparison detection
    is_comparison = any(term in q_lower for term in [" vs ", " versus ", " compare ", " difference between "])

    # Recognized technical entities (order matters for substring matching)
    tech_keywords = [
        "django rest framework", "django", "fastapi", "python", "react", "node", "nodejs",
        "flask", "rust", "golang", "go", "postgres", "postgresql",
        "docker", "kubernetes", "langchain", "ollama", "playwright"
    ]
    matched_entities = [tech for tech in tech_keywords if re.search(rf"\b{re.escape(tech)}\b", q_lower)]

    queries = []

    # 1. Specialized topic handling for exact official documentation
    if "django rest framework" in q_lower or "drf" in q_lower:
        queries.append("django rest framework authentication serializers views official documentation")
    if "model" in q_lower and "django" in q_lower:
        queries.append("django models official documentation")
    if "migration" in q_lower and "django" in q_lower:
        queries.append("django migrations makemigrations migrate official documentation")
    if ("virtual environment" in q_lower or "venv" in q_lower) and "python" in q_lower:
        queries.append("python venv virtual environment windows official documentation")
    if "react" in q_lower and ("django" in q_lower or "api" in q_lower):
        queries.append("react communicate with django rest framework api")
    if "postgresql" in q_lower and ("release" in q_lower or "version" in q_lower):
        queries.append("postgresql official release version latest")

    # 2. Freshness and release queries
    if requires_freshness and matched_entities:
        for ent in matched_entities[:2]:
            queries.append(f"{ent} official latest release version documentation")
    elif is_comparison and len(matched_entities) >= 2:
        queries.append(f"{matched_entities[0]} official documentation features")
        queries.append(f"{matched_entities[1]} official documentation features")
    elif matched_entities:
        for ent in matched_entities[:2]:
            queries.append(f"{ent} official documentation")

    # 3. Add clean user query
    clean_q = re.sub(r"^(?:find|search|explain|research|tell me about)\s+", "", query, flags=re.IGNORECASE).strip()
    if clean_q:
        queries.append(clean_q)
    queries.append(query)

    return {
        "requires_freshness": requires_freshness,
        "is_comparison": is_comparison,
        "matched_entities": matched_entities,
        "search_queries": list(dict.fromkeys(queries))[:4]
    }


def web_research_agent_node(state: CentralGraphState) -> Dict[str, Any]:
    """
    Agent 4 node: Executes the Crawlee + BeautifulSoup4 web research pipeline.
    """
    t0 = time.time()
    query = state.get("user_query", "").strip()
    req_id = state.get("request_id") or f"req_{state.get('task_id', 'task')}"
    conv_id = state.get("conversation_id")
    task_id = state.get("task_id", "task")

    emit_agent_started(state, AGENT_ID, AGENT_NAME, GROUP_ID, COMPONENT_TYPE, f"Initiating web research for: '{query[:60]}...'")

    try:
        # Step 4.0: Query Understanding and Decomposition
        query_meta = _understand_and_decompose_query(query)
        event_bus.publish(
            request_id=req_id,
            execution_id=task_id,
            conversation_id=conv_id,
            node_id=AGENT_ID,
            component_name=AGENT_NAME,
            component_type=COMPONENT_TYPE,
            event_type="QUERY_ANALYSIS",
            execution_status="ACTIVE",
            safe_task_summary=f"Query analyzed: Freshness={query_meta['requires_freshness']}, Entities={query_meta['matched_entities']}",
            query_decomposition=query_meta,
            timestamp=time.time()
        )

        from research_system.graph.state import ResearchState

        sub_state: ResearchState = {
            "conversation_id": conv_id,
            "request_id": req_id,
            "user_query": query,
            "query": query,
            "core_topic": query_meta["matched_entities"][0] if query_meta["matched_entities"] else query,
            "key_entities": query_meta["matched_entities"],
            "complexity_level": "moderate",
            "is_ambiguous": False,
            "clarification_prompt": "",
            "subquestions": query_meta["search_queries"],
            "search_queries": query_meta["search_queries"],
            "raw_search_results": [],
            "search_results": [],
            "selected_urls": [],
            "retrieved_pages": [],
            "crawled_pages": [],
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

        # Step 4.1: Authoritative Source Discovery
        emit_agent_progress(state, AGENT_ID, AGENT_NAME, GROUP_ID, "Discovering authoritative primary sources...")
        search_res = search_worker_node(sub_state)
        sub_state.update(search_res)
        found_results = sub_state.get("search_results", []) or sub_state.get("raw_search_results", [])
        sub_state["search_results"] = found_results

        event_bus.publish(
            request_id=req_id,
            execution_id=task_id,
            conversation_id=conv_id,
            node_id=AGENT_ID,
            component_name=AGENT_NAME,
            component_type=COMPONENT_TYPE,
            event_type="SOURCE_DISCOVERY",
            execution_status="ACTIVE",
            safe_task_summary=f"Discovered {len(found_results)} potential external sources",
            sources_count=len(found_results),
            timestamp=time.time()
        )

        # Step 4.2: URL Selection Worker (Deterministic Authority Scoring)
        url_res = url_selection_worker_node(sub_state)
        sub_state.update(url_res)
        selected_urls = sub_state.get("selected_urls", [])

        # Step 4.3: Crawlee Web Crawling Engine
        emit_agent_progress(state, AGENT_ID, AGENT_NAME, GROUP_ID, f"Crawlee engine dispatching crawl across {len(selected_urls)} target(s)...")
        crawl_res = crawling_worker_node(sub_state)
        sub_state.update(crawl_res)

        crawled_pages = sub_state.get("crawled_pages", [])
        event_bus.publish(
            request_id=req_id,
            execution_id=task_id,
            conversation_id=conv_id,
            node_id=AGENT_ID,
            component_name=AGENT_NAME,
            component_type=COMPONENT_TYPE,
            event_type="CRAWLING",
            execution_status="ACTIVE",
            safe_task_summary=f"Crawlee retrieved {len(crawled_pages)} full web page(s)",
            pages_retrieved=len(crawled_pages),
            timestamp=time.time()
        )

        # Step 4.4: Pure BeautifulSoup4 Structured HTML Extraction
        emit_agent_progress(state, AGENT_ID, AGENT_NAME, GROUP_ID, "BeautifulSoup4 parsing semantic DOM, tables, lists, and headings...")
        extract_res = content_extraction_worker_node(sub_state)
        sub_state.update(extract_res)
        extracted_contents = sub_state.get("extracted_contents", [])

        # Step 4.5: Content Processing Worker (Semantic Chunking & Passage Extraction)
        proc_res = content_processing_worker_node(sub_state)
        sub_state.update(proc_res)
        processed_chunks = sub_state.get("processed_chunks", [])

        # Ensure chunks have chunk_text attribute
        for ch in processed_chunks:
            if "chunk_text" not in ch:
                ch["chunk_text"] = ch.get("text", "")

        # Step 4.6: Compile structured, verifiable source references with canonical IDs [S1], [S2]
        rich_sources = []
        source_index = 1

        for p in crawled_pages:
            p_url = p.get("url", "")
            ext = next((e for e in extracted_contents if e.get("url") == p_url), None)
            
            clean_text = ext.get("clean_text", "") if ext else p.get("snippet", "")
            tables = ext.get("tables", []) if ext else []
            headings = ext.get("headings", []) if ext else []
            status = ext.get("extraction_status", "SUCCESS") if ext else "SUCCESS"

            source_id = f"S{source_index}"
            rich_sources.append({
                "source_id": source_id,
                "citation_tag": f"[{source_id}]",
                "title": p.get("title") or (ext.get("page_title") if ext else "Online Source"),
                "url": p_url,
                "domain": p.get("domain", ""),
                "clean_text": clean_text[:4000],
                "snippet": clean_text[:350] + ("..." if len(clean_text) > 350 else ""),
                "tables": tables,
                "headings": headings,
                "extraction_status": status,
                "engine": p.get("engine", "Crawlee + BeautifulSoup4")
            })
            source_index += 1

        # Fallback if no pages were successfully crawled
        if not rich_sources:
            for item in (selected_urls or found_results)[:3]:
                source_id = f"S{source_index}"
                rich_sources.append({
                    "source_id": source_id,
                    "citation_tag": f"[{source_id}]",
                    "title": item.get("title", "Search Result"),
                    "url": item.get("url", ""),
                    "domain": item.get("domain", ""),
                    "clean_text": item.get("snippet", ""),
                    "snippet": item.get("snippet", ""),
                    "tables": [],
                    "headings": [],
                    "extraction_status": "SEARCH_SNIPPET_ONLY",
                    "engine": "Search Provider Snippet"
                })
                source_index += 1

        research_results = {
            "search_queries": query_meta["search_queries"],
            "selected_urls": selected_urls,
            "pages_retrieved": len(crawled_pages),
            "chunks_count": len(processed_chunks),
            "chunks": processed_chunks[:15],
            "sources": rich_sources,
            "query_meta": query_meta
        }

        duration = round(time.time() - t0, 2)
        emit_agent_completed(
            state, AGENT_ID, AGENT_NAME, GROUP_ID, COMPONENT_TYPE,
            f"Crawlee + BS4 completed research across {len(rich_sources)} source(s) and {len(processed_chunks)} passage(s).",
            output_summary=f"{len(rich_sources)} sources retrieved in {duration}s",
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
