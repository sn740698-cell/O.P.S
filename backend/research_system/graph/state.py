from typing import TypedDict, List, Dict, Any, Optional

class ResearchState(TypedDict, total=False):
    """
    Central typed state for the O.P.S. 2.0 Web Research & Hybrid LangGraph graph.
    Propagates data deterministically between reasoning agents, execution workers,
    and parallel hybrid synthesis branches.
    """
    request_id: str
    execution_id: str
    session_id: str
    conversation_id: str
    query: str
    input_type: str  # 'text' or 'voice'
    response_mode: str  # 'WEB' or 'HYBRID'
    mode_reason: str
    stages: List[str]

    # Multi-Turn Conversation Context
    conversation_history: List[Dict[str, Any]]
    conversation_summary: str
    long_term_memories: List[Dict[str, Any]]
    project_knowledge: List[Dict[str, Any]]

    # 1. Request Understanding Agent (Qwen3 0.6B / 1.7B)
    intent: Dict[str, Any]
    is_simple_query: bool

    # Hybrid Mode: Parallel Local Reasoning Branch (Qwen3 1.7B)
    local_reasoning: str

    # 2. Research Planner Agent (Qwen3 1.7B)
    research_plan: Dict[str, Any]
    subquestions: List[str]
    search_queries: List[str]

    # 3. Search Worker (DuckDuckGo / Brave / Wikipedia)
    search_results: List[Dict[str, Any]]

    # 4. URL Selection Worker (Authority & Relevance Scoring)
    selected_urls: List[Dict[str, Any]]

    # 5. Crawling Worker (Concurrent Pooled HTTPX)
    crawled_pages: List[Dict[str, Any]]

    # 6. Browser Rendering Worker (Playwright)
    rendered_pages: List[Dict[str, Any]]

    # 7. Content Extraction Worker (BeautifulSoup4)
    extracted_contents: List[Dict[str, Any]]

    # 8. Content Processing Worker (Semantic Passage Chunking)
    processed_chunks: List[Dict[str, Any]]

    # 9. Evidence Analysis Agent (Qwen3 1.7B)
    analysis: Dict[str, Any]
    evidence_evaluations: List[Dict[str, Any]]
    contradictions: List[Dict[str, Any]]
    is_sufficient: bool

    # 10. Adaptive Research Controller
    iteration_count: int
    max_iterations: int
    routing_decision: str

    # 11. Evidence Retrieval Worker
    retrieved_evidence: List[Dict[str, Any]]

    # 12. Answer Generation Agent (Qwen3 1.7B)
    final_answer: str

    # 13. Citation and Result Worker
    citations: List[Dict[str, Any]]

    # Telemetry & Operational Tracking
    current_active_component: str
    node_history: List[str]
    errors: List[str]
