"""
O.P.S. 2.0 — Search Worker
Execution Worker 1: Queries search providers separately from the crawling engine.
Features:
- Shared persistent HTTP connection pool (no per-request TCP/TLS handshake overhead)
- In-memory TTL query caching (instant responses for repeated or related searches)
- Multi-provider search resilience (DuckDuckGo HTML, Wikipedia API, Brave Search, Bing fallback)
- Query focus cleaning (removes conversational noise for crisp keyword searches)
- Source authority tagging (detects primary/official docs, institutional domains)
"""

import os
import re
import time
import logging
import urllib.parse
from typing import Dict, Any, List, Optional, Tuple
import httpx
from bs4 import BeautifulSoup

from research_system.graph.state import ResearchState
from research_system.events.event_bus import event_bus

logger = logging.getLogger(__name__)

BRAVE_API_KEY = os.environ.get("BRAVE_SEARCH_API_KEY", "")

# Persistent connection-pooled HTTP client for search requests
_SEARCH_CLIENT = httpx.Client(
    timeout=httpx.Timeout(10.0, connect=4.0),
    limits=httpx.Limits(max_keepalive_connections=20, max_connections=40, keepalive_expiry=120.0),
    follow_redirects=True,
    headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9"
    }
)

# In-memory LRU TTL search cache: {clean_query: (timestamp, results)}
_SEARCH_CACHE: Dict[str, Tuple[float, List[Dict[str, Any]]]] = {}
CACHE_TTL_SECONDS = 900.0  # 15 minutes


def _clean_search_query(query: str) -> str:
    """Extracts concise, high-signal search keywords from conversational user prompts."""
    q = (query or "").strip()
    # Strip conversational prefixes
    noise_prefixes = [
        r"^(?:please\s+)?(?:can\s+you\s+)?(?:tell\s+me|explain|search\s+for|look\s+up|find\s+out|what\s+is|what\s+are)\s+",
        r"^(?:i\s+want\s+to\s+know|help\s+me\s+find|give\s+me\s+the\s+details\s+on)\s+",
    ]
    cleaned = q
    for pat in noise_prefixes:
        cleaned = re.sub(pat, "", cleaned, flags=re.IGNORECASE)
    cleaned = cleaned.rstrip("?!.;,").strip()
    return cleaned if len(cleaned) >= 3 else q


def _is_authoritative_domain(domain: str) -> bool:
    """Returns True if the domain is a known primary documentation or authoritative source."""
    d = domain.lower()
    authoritative_tlds = [".org", ".gov", ".edu"]
    if any(d.endswith(tld) for tld in authoritative_tlds):
        return True
    authoritative_substrings = [
        "docs.", "developer.", "devguide.", "blog.", "github.com",
        "arxiv.org", "wikipedia.org", "python.org", "langchain.com",
        "microsoft.com", "google.com", "mozilla.org", "w3.org"
    ]
    return any(sub in d for sub in authoritative_substrings)


def _execute_brave_search(query: str, count: int = 5) -> List[Dict[str, Any]]:
    """Executes a search query against Brave Search API if configured."""
    if not BRAVE_API_KEY:
        return []

    url = "https://api.search.brave.com/res/v1/web/search"
    headers = {
        "Accept": "application/json",
        "X-Subscription-Token": BRAVE_API_KEY
    }
    params = {"q": query, "count": count}

    try:
        resp = _SEARCH_CLIENT.get(url, headers=headers, params=params)
        if resp.status_code == 200:
            data = resp.json()
            results = []
            for item in data.get("web", {}).get("results", []):
                u = item.get("url", "")
                parsed_dom = urllib.parse.urlparse(u).netloc.lower()
                results.append({
                    "title": item.get("title", ""),
                    "url": u,
                    "snippet": item.get("description", ""),
                    "domain": parsed_dom,
                    "is_authoritative": _is_authoritative_domain(parsed_dom),
                    "provider": "Brave Search API",
                    "retrieved_at": time.time()
                })
            return results
    except Exception as e:
        logger.warning(f"Brave Search API notice: {e}")
    return []


def _execute_duckduckgo_search(query: str, count: int = 6) -> List[Dict[str, Any]]:
    """
    Executes resilient DuckDuckGo HTML search.
    Decodes 'uddg=' redirection URLs to obtain direct target destination URLs.
    """
    results = []
    try:
        resp = _SEARCH_CLIENT.post("https://html.duckduckgo.com/html/", data={"q": query}, timeout=8.0)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, "html.parser")
            for div in soup.find_all("div", class_="result__body"):
                a = div.find("a", class_="result__a")
                snip = div.find("a", class_="result__snippet")
                if not a:
                    continue
                href = a.get("href", "")
                # Decode DuckDuckGo redirect link
                if "uddg=" in href:
                    qs = urllib.parse.parse_qs(urllib.parse.urlparse(href).query)
                    clean_url = qs.get("uddg", [href])[0]
                else:
                    clean_url = href

                if clean_url.startswith("http") and not clean_url.startswith("https://duckduckgo.com"):
                    dom = urllib.parse.urlparse(clean_url).netloc.lower()
                    results.append({
                        "title": a.get_text(strip=True),
                        "url": clean_url,
                        "snippet": snip.get_text(strip=True) if snip else "",
                        "domain": dom,
                        "is_authoritative": _is_authoritative_domain(dom),
                        "provider": "DuckDuckGo Web Search",
                        "retrieved_at": time.time()
                    })
                if len(results) >= count:
                    break
    except Exception as e:
        logger.warning(f"DuckDuckGo search notice: {e}")
    return results


def _execute_wikipedia_search(query: str, count: int = 3) -> List[Dict[str, Any]]:
    """Queries Wikipedia Search API for authoritative factual definitions and overviews."""
    results = []
    try:
        resp = _SEARCH_CLIENT.get(
            "https://en.wikipedia.org/w/api.php",
            params={"action": "query", "list": "search", "srsearch": query, "format": "json"},
            headers={"User-Agent": "OPSResearchBot/2.0 (contact: ops@local.dev)"},
            timeout=6.0
        )
        if resp.status_code == 200:
            data = resp.json()
            for item in data.get("query", {}).get("search", [])[:count]:
                page_title = item.get("title", "")
                slug = urllib.parse.quote(page_title.replace(" ", "_"))
                clean_url = f"https://en.wikipedia.org/wiki/{slug}"
                raw_snip = item.get("snippet", "")
                clean_snip = re.sub(r"<[^>]+>", "", raw_snip).strip()
                results.append({
                    "title": page_title,
                    "url": clean_url,
                    "snippet": clean_snip,
                    "domain": "en.wikipedia.org",
                    "is_authoritative": True,
                    "provider": "Wikipedia Search API",
                    "retrieved_at": time.time()
                })
    except Exception as e:
        logger.warning(f"Wikipedia search notice: {e}")
    return results


def _execute_bing_fallback(query: str, count: int = 3) -> List[Dict[str, Any]]:
    """
    Fallback Bing search with strict bot-block validation.
    Discards regional homepage feeds (e.g. Navratri/Panchang calendars) if detected.
    """
    results = []
    try:
        resp = _SEARCH_CLIENT.get("https://www.bing.com/search", params={"q": query}, timeout=6.0)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, "html.parser")
            q_keywords = [w.lower() for w in re.findall(r"\w+", query) if len(w) > 3]

            for li in soup.find_all("li", class_="b_algo", limit=count + 3):
                h2 = li.find("h2")
                a = h2.find("a") if h2 else None
                caption = li.find("p") or li.find("div", class_="b_caption")
                if a and a.get("href"):
                    raw_href = a.get("href").strip()
                    title = a.get_text(strip=True)
                    # Bot-block detection: If title has zero overlap with query keywords, discard
                    title_words = [w.lower() for w in re.findall(r"\w+", title)]
                    if q_keywords and not any(kw in title_words for kw in q_keywords):
                        continue  # Skip bot-blocked unrelated feed

                    dom = urllib.parse.urlparse(raw_href).netloc.lower()
                    results.append({
                        "title": title,
                        "url": raw_href,
                        "snippet": caption.get_text(strip=True) if caption else "",
                        "domain": dom,
                        "is_authoritative": _is_authoritative_domain(dom),
                        "provider": "Bing Web Search",
                        "retrieved_at": time.time()
                    })
                if len(results) >= count:
                    break
    except Exception as e:
        logger.warning(f"Bing fallback search notice: {e}")
    return results


def execute_multi_provider_search(query: str, max_results: int = 8) -> List[Dict[str, Any]]:
    """
    Executes resilient multi-provider search with in-memory TTL caching.
    Order of preference:
    1. Check Search Cache
    2. Brave Search API (if key available)
    3. DuckDuckGo HTML Search (primary public provider)
    4. Wikipedia Search API (authoritative reference grounding)
    5. Bing Search (fallback with bot-block validation)
    """
    clean_q = _clean_search_query(query).lower()
    now = time.time()

    # 1. Cache hit check
    if clean_q in _SEARCH_CACHE:
        cached_time, cached_results = _SEARCH_CACHE[clean_q]
        if (now - cached_time) < CACHE_TTL_SECONDS:
            logger.info(f"[SEARCH CACHE HIT] '{clean_q}' ({len(cached_results)} items)")
            return cached_results

    all_results: List[Dict[str, Any]] = []
    seen_urls = set()

    # 2. Brave Search (if configured)
    brave_res = _execute_brave_search(query, count=max_results)
    for r in brave_res:
        u = r.get("url")
        if u and u not in seen_urls:
            seen_urls.add(u)
            all_results.append(r)

    # 3. DuckDuckGo HTML (primary resilient public provider)
    if len(all_results) < max_results:
        ddg_res = _execute_duckduckgo_search(query, count=max_results - len(all_results) + 2)
        for r in ddg_res:
            u = r.get("url")
            if u and u not in seen_urls:
                seen_urls.add(u)
                all_results.append(r)

    # 4. Wikipedia API (factual context)
    if len(all_results) < max_results:
        wiki_res = _execute_wikipedia_search(query, count=2)
        for r in wiki_res:
            u = r.get("url")
            if u and u not in seen_urls:
                seen_urls.add(u)
                all_results.append(r)

    # 5. Bing Fallback (only if needed)
    if len(all_results) < 3:
        bing_res = _execute_bing_fallback(query, count=max_results - len(all_results))
        for r in bing_res:
            u = r.get("url")
            if u and u not in seen_urls:
                seen_urls.add(u)
                all_results.append(r)

    # Store in memory cache
    if all_results:
        _SEARCH_CACHE[clean_q] = (now, all_results)

    return all_results


def search_worker_node(state: ResearchState) -> Dict[str, Any]:
    """
    Execution Worker 1: Search Worker
    Queries search providers with connection reuse, focus cleaning, and caching.
    """
    request_id = state.get("request_id", "req_unknown")
    execution_id = state.get("execution_id", "exec_unknown")
    conversation_id = state.get("conversation_id", None)
    queries = state.get("search_queries", [state.get("query", "")])
    t0 = time.time()

    provider_name = "DuckDuckGo / Multi-Engine Search Pool"

    event_bus.publish(
        request_id=request_id,
        execution_id=execution_id,
        conversation_id=conversation_id,
        node_id="search_worker",
        component_name="Search Worker",
        component_type="execution_worker",
        event_type="NODE_STARTED",
        execution_status="RUNNING",
        safe_task_summary=f"Dispatching focused searches across {provider_name}",
        tool_name=provider_name,
        timestamp=t0
    )

    all_results = list(state.get("search_results", []))
    seen_urls = {r.get("url") for r in all_results}

    # Execute up to 2 distinct search queries to balance depth and speed
    for q in queries[:2]:
        results = execute_multi_provider_search(q, max_results=6)
        for res in results:
            u = res.get("url")
            if u and u not in seen_urls:
                all_results.append(res)
                seen_urls.add(u)

    duration = time.time() - t0

    event_bus.publish(
        request_id=request_id,
        execution_id=execution_id,
        conversation_id=conversation_id,
        node_id="search_worker",
        component_name="Search Worker",
        component_type="execution_worker",
        event_type="SEARCH_COMPLETED",
        execution_status="COMPLETED",
        safe_task_summary=f"Discovered {len(all_results)} credible web sources in {duration:.2f}s",
        safe_output_summary=f"Authoritative sources: {', '.join([r.get('domain', '') for r in all_results[:3]])}",
        tool_name=provider_name,
        sources_discovered=len(all_results),
        sources_count=len(all_results),
        current_stage="Searching the web",
        timestamp=time.time()
    )

    node_history = list(state.get("node_history", []))
    node_history.append("search_worker")

    return {
        "search_results": all_results,
        "current_active_component": "search_worker",
        "node_history": node_history
    }
