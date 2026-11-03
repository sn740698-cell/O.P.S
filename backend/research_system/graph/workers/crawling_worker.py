"""
O.P.S. 2.0 — Crawling Worker
Execution Worker 3: High-performance concurrent webpage retrieval.
Features:
- Persistent connection pooling with keep-alive HTTP/1.1 connections
- Concurrent multi-threaded page retrieval via ThreadPoolExecutor (sub-second fetching)
- In-memory TTL page cache (prevents redundant fetches for recently visited pages)
- Source-aware evidence metadata preservation (URL, title, domain, retrieval timestamp)
- Graceful snippet fallback if remote server blocks or times out
"""

import time
import logging
import urllib.parse
from typing import Dict, Any, List, Tuple
from concurrent.futures import ThreadPoolExecutor
import httpx

from research_system.graph.state import ResearchState
from research_system.events.event_bus import event_bus

logger = logging.getLogger(__name__)

# Persistent connection-pooled HTTP client for web retrieval
_CRAWL_CLIENT = httpx.Client(
    timeout=httpx.Timeout(10.0, connect=3.0, read=8.0),
    limits=httpx.Limits(max_keepalive_connections=25, max_connections=50, keepalive_expiry=120.0),
    follow_redirects=True,
    headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Sec-Ch-Ua": '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": '"Windows"'
    }
)

# In-memory page cache: {url: (cached_at, page_dict)}
_PAGE_CACHE: Dict[str, Tuple[float, Dict[str, Any]]] = {}
PAGE_CACHE_TTL = 1800.0  # 30 minutes


def _fetch_single_page(target: Dict[str, Any]) -> Dict[str, Any]:
    """Fetches a single page using connection pool with cache checking and snippet fallback."""
    url = target.get("url", "").strip()
    title = target.get("title", "")
    snippet = target.get("snippet", "")
    domain = target.get("domain", urllib.parse.urlparse(url).netloc.lower())
    now = time.time()

    # 1. Check in-memory page cache
    if url in _PAGE_CACHE:
        cached_at, cached_page = _PAGE_CACHE[url]
        if (now - cached_at) < PAGE_CACHE_TTL:
            logger.info(f"[PAGE CACHE HIT] {url}")
            return cached_page

    t0 = time.time()
    try:
        resp = _CRAWL_CLIENT.get(url)
        if resp.status_code == 200:
            page_data = {
                "url": url,
                "title": title,
                "snippet": snippet,
                "domain": domain,
                "html": resp.text,
                "status_code": resp.status_code,
                "engine": "HTTPX High-Speed Pool",
                "retrieved_at": now,
                "fetch_ms": round((time.time() - t0) * 1000, 1)
            }
            _PAGE_CACHE[url] = (now, page_data)
            return page_data
        else:
            logger.warning(f"HTTP {resp.status_code} fetching {url}. Using search snippet.")
            return {
                "url": url,
                "title": title,
                "snippet": snippet,
                "domain": domain,
                "html": f"<html><body><h1>{title}</h1><p>{snippet}</p></body></html>",
                "status_code": resp.status_code,
                "engine": "Search Snippet Fallback",
                "retrieved_at": now,
                "fetch_ms": round((time.time() - t0) * 1000, 1)
            }
    except Exception as e:
        logger.warning(f"Failed to fetch {url}: {e}. Using search snippet.")
        return {
            "url": url,
            "title": title,
            "snippet": snippet,
            "domain": domain,
            "html": f"<html><body><h1>{title}</h1><p>{snippet}</p></body></html>",
            "status_code": 200,
            "engine": "Search Snippet Fallback",
            "retrieved_at": now,
            "fetch_ms": round((time.time() - t0) * 1000, 1)
        }


def crawling_worker_node(state: ResearchState) -> Dict[str, Any]:
    """
    Execution Worker 3: Crawling Worker
    Performs concurrent, connection-pooled page retrieval for non-JS target URLs.
    """
    request_id = state.get("request_id", "req_unknown")
    execution_id = state.get("execution_id", "exec_unknown")
    conversation_id = state.get("conversation_id", None)
    selected_urls = state.get("selected_urls", [])
    t0 = time.time()

    # Filter out targets reserved for Playwright browser rendering
    http_targets = [u for u in selected_urls if not u.get("needs_browser_rendering")]

    event_bus.publish(
        request_id=request_id,
        execution_id=execution_id,
        conversation_id=conversation_id,
        node_id="crawling_worker",
        component_name="Crawling Worker",
        component_type="execution_worker",
        event_type="NODE_STARTED",
        execution_status="RUNNING",
        safe_task_summary=f"Concurrently retrieving {len(http_targets)} target pages via connection pool",
        tool_name="Concurrent HTTPX Engine",
        timestamp=t0
    )

    crawled_pages = list(state.get("crawled_pages", []))

    if http_targets:
        # Fetch pages concurrently with ThreadPoolExecutor
        max_workers = min(len(http_targets), 4)
        with ThreadPoolExecutor(max_workers=max_workers) as pool:
            fetched_results = list(pool.map(_fetch_single_page, http_targets))
            crawled_pages.extend(fetched_results)

    duration = time.time() - t0
    domains = list({p.get("domain", "") for p in crawled_pages if p.get("domain")})

    event_bus.publish(
        request_id=request_id,
        execution_id=execution_id,
        conversation_id=conversation_id,
        node_id="crawling_worker",
        component_name="Crawling Worker",
        component_type="execution_worker",
        event_type="PAGE_RETRIEVED",
        execution_status="COMPLETED",
        safe_task_summary=f"Retrieved {len(crawled_pages)} pages in {duration:.2f}s",
        safe_output_summary=f"Domains: {', '.join(domains[:3])}",
        tool_name="Concurrent HTTPX Engine",
        pages_retrieved=len(crawled_pages),
        pages_count=len(crawled_pages),
        domains=domains,
        current_stage="Retrieving relevant pages",
        timestamp=time.time()
    )

    node_history = list(state.get("node_history", []))
    node_history.append("crawling_worker")

    return {
        "crawled_pages": crawled_pages,
        "current_active_component": "crawling_worker",
        "node_history": node_history
    }
