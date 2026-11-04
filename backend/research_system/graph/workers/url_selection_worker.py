"""
O.P.S. 2.0 — URL Selection Worker
Execution Worker 2: Intelligently filters and ranks candidate URLs based on:
1. Source credibility and authority (Official docs, .org, .edu, .gov, primary vendor sites)
2. Direct entity match against official technology domains (python.org, djangoproject.com, react.dev, nodejs.org, fastapi.tiangolo.com)
3. Relevance of snippet and title to user directive
4. Freshness and domain diversity
5. Selective browser rendering tagging (Playwright ONLY for JS-heavy sites)
"""

import time
import re
import logging
import urllib.parse
from typing import Dict, Any, List
from research_system.graph.state import ResearchState
from research_system.events.event_bus import event_bus

logger = logging.getLogger("OPS.Research.UrlSelection")

# Domains known to require client-side JavaScript execution
JS_HEAVY_PATTERNS = [
    "twitter.com", "x.com", "instagram.com", "linkedin.com",
    "medium.com", "reddit.com", "youtube.com"
]

# High-authority domains for technical & factual grounding
HIGH_AUTHORITY_PATTERNS = [
    "docs.", "devguide.", "developer.", "blog.", "github.com",
    "djangoproject.com", "django-rest-framework.org", "fastapi.tiangolo.com", "python.org",
    "react.dev", "nodejs.org", "postgresql.org",
    "langchain.com", "huggingface.co", "wikipedia.org",
    "arxiv.org", "pypi.org", "mozilla.org", "microsoft.com", "google.com"
]

# Primary official domains mapped to canonical technologies
PRIMARY_TECH_DOMAINS = {
    "django": "djangoproject.com",
    "drf": "django-rest-framework.org",
    "rest_framework": "django-rest-framework.org",
    "serializers": "django-rest-framework.org",
    "python": "python.org",
    "venv": "python.org",
    "react": "react.dev",
    "node": "nodejs.org",
    "nodejs": "nodejs.org",
    "fastapi": "fastapi.tiangolo.com",
    "postgres": "postgresql.org",
    "postgresql": "postgresql.org"
}

# Low-quality SEO content farms / automated aggregators to deprioritize
LOW_QUALITY_PATTERNS = [
    "pinterest.", "tiktok.", "quora.", "answers.yahoo.", "softonic.",
    "geekforgeeks.", "tutorialspoint."  # frequently outdated or scrapers
]


def _score_candidate_url(item: Dict[str, Any], query_terms: List[str]) -> float:
    """Scores candidate URL on a scale from 0.0 to 100.0 based on credibility and relevance."""
    url = item.get("url", "")
    title = (item.get("title") or "").lower()
    snippet = (item.get("snippet") or "").lower()
    domain = urllib.parse.urlparse(url).netloc.lower()

    score = 10.0

    # 1. Primary tech domain exact match bonus (+45)
    for tech, tech_dom in PRIMARY_TECH_DOMAINS.items():
        if any(tech == q.strip() for q in query_terms) and tech_dom in domain:
            score += 45.0
            break

    # 2. Authority bonus
    if item.get("is_authoritative"):
        score += 35.0
    if any(pat in domain for pat in HIGH_AUTHORITY_PATTERNS):
        score += 25.0
    if domain.endswith(".org") or domain.endswith(".edu") or domain.endswith(".gov"):
        score += 15.0

    # 3. Penalty for spam / low quality aggregators
    if any(pat in domain for pat in LOW_QUALITY_PATTERNS):
        score -= 25.0

    # 4. Query keyword relevance in title (+8 each) and snippet (+3 each)
    for term in query_terms:
        if term in title:
            score += 8.0
        if term in snippet:
            score += 3.0

    # 5. HTTPS preference
    if url.startswith("https://"):
        score += 5.0

    return max(0.0, score)


def url_selection_worker_node(state: ResearchState) -> Dict[str, Any]:
    """
    Execution Worker 2: URL Selection Worker
    Filters and ranks candidate URLs using multi-criteria authority and relevance scoring.
    """
    request_id = state.get("request_id", "req_unknown")
    execution_id = state.get("execution_id", "exec_unknown")
    conversation_id = state.get("conversation_id", None)
    search_results = state.get("search_results", [])
    query = state.get("query", "")
    is_simple = state.get("is_simple_query", False)
    t0 = time.time()

    event_bus.publish(
        request_id=request_id,
        execution_id=execution_id,
        conversation_id=conversation_id,
        node_id="url_selection_worker",
        component_name="URL Selection Worker",
        component_type="execution_worker",
        event_type="NODE_STARTED",
        execution_status="RUNNING",
        safe_task_summary=f"Scoring and selecting top authoritative URLs from {len(search_results)} candidates",
        tool_name="Deterministic Authority & Relevance Ranker",
        timestamp=t0
    )

    query_terms = [w.lower() for w in re.findall(r"\w+", query) if len(w) > 2]

    # Score each search candidate
    scored_items = []
    for item in search_results:
        u = item.get("url", "").strip()
        if not u or not u.startswith("http"):
            continue
        path_only = u.lower().split("?")[0]
        if any(path_only.endswith(ext) for ext in [".pdf", ".zip", ".tar.gz", ".tgz", ".exe", ".dmg", ".pkg", ".png", ".jpg", ".jpeg", ".gif"]):
            continue
        sc = _score_candidate_url(item, query_terms)
        scored_items.append((sc, item))

    # Sort descending by composite score
    scored_items.sort(key=lambda x: x[0], reverse=True)

    limit = 2 if is_simple else 4
    selected = []
    domain_counts: Dict[str, int] = {}

    for score, item in scored_items:
        url = item.get("url", "").strip()
        domain = urllib.parse.urlparse(url).netloc.lower()

        # Allow max 2 URLs from the same domain to preserve diversity unless it's official docs
        current_dom_count = domain_counts.get(domain, 0)
        is_official = any(p in domain for p in HIGH_AUTHORITY_PATTERNS)
        if current_dom_count >= (2 if is_official else 1) and len(selected) >= 2:
            continue

        domain_counts[domain] = current_dom_count + 1

        needs_js = any(pattern in domain for pattern in JS_HEAVY_PATTERNS)

        selected.append({
            "url": url,
            "title": item.get("title", ""),
            "snippet": item.get("snippet", ""),
            "score": score,
            "domain": domain,
            "is_authoritative": item.get("is_authoritative", False) or is_official,
            "needs_browser_rendering": needs_js,
            "provider": item.get("provider", "Web Search")
        })

        if len(selected) >= limit:
            break

    duration = time.time() - t0

    event_bus.publish(
        request_id=request_id,
        execution_id=execution_id,
        conversation_id=conversation_id,
        node_id="url_selection_worker",
        component_name="URL Selection Worker",
        component_type="execution_worker",
        event_type="NODE_COMPLETED",
        execution_status="COMPLETED",
        safe_task_summary=f"Selected {len(selected)} high-credibility target URLs in {duration:.2f}s",
        safe_output_summary=f"Top Targets: {', '.join([u.get('domain', '') for u in selected])}",
        tool_name="Deterministic Authority & Relevance Ranker",
        timestamp=time.time()
    )

    node_history = list(state.get("node_history", []))
    node_history.append("url_selection_worker")

    return {
        "selected_urls": selected,
        "current_active_component": "url_selection_worker",
        "node_history": node_history
    }
