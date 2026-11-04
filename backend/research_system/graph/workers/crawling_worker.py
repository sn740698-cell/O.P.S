"""
O.P.S. 2.0 — Web Crawling Worker (Crawlee Engine)
Execution Worker 3: High-performance, controlled webpage retrieval via Crawlee.

Core Features:
- Primary Engine: Crawlee BeautifulSoupCrawler with MemoryStorageClient
- Starting URL queue management and duplicate URL prevention (normalization & canonicalization)
- Bounded and polite crawling: max requests, max crawl depth, and request timeouts
- Concurrent page retrieval with automatic concurrency scaling
- In-memory isolated storage client (avoids cross-thread/loop lock collisions)
- Rich page metadata collection: URL, title, HTTP status, domain, retrieval timestamp, latency
- In-memory TTL page cache (prevents redundant fetches for recently visited pages)
- Graceful error handling and status tracking for blocked/failed requests
"""

import time
import logging
import asyncio
import concurrent.futures
import urllib.parse
from datetime import timedelta
from typing import Dict, Any, List, Optional, Tuple, Set

from crawlee.crawlers import BeautifulSoupCrawler, BeautifulSoupCrawlingContext
from crawlee.storage_clients import MemoryStorageClient

from research_system.graph.state import ResearchState
from research_system.events.event_bus import event_bus

logger = logging.getLogger("OPS.Research.CrawleeWorker")

# In-memory page cache: {normalized_url: (cached_at_timestamp, page_dict)}
_PAGE_CACHE: Dict[str, Tuple[float, Dict[str, Any]]] = {}
PAGE_CACHE_TTL = 1800.0  # 30 minutes


def _normalize_url(url: str) -> str:
    """Normalizes URL by stripping query tracking fragments and anchor hashes."""
    if not url:
        return ""
    try:
        parsed = urllib.parse.urlparse(url.strip())
        # Filter tracking query parameters
        tracking_params = {"utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content", "ref", "fbclid"}
        query_pairs = urllib.parse.parse_qsl(parsed.query)
        clean_query = [(k, v) for k, v in query_pairs if k.lower() not in tracking_params]
        encoded_query = urllib.parse.urlencode(clean_query)
        # Drop fragment
        return urllib.parse.urlunparse((
            parsed.scheme.lower(),
            parsed.netloc.lower(),
            parsed.path,
            parsed.params,
            encoded_query,
            ""  # No fragment
        ))
    except Exception:
        return url.strip()


def _run_coroutine_sync(coro_fn):
    """
    Safely executes an async coroutine from synchronous or async contexts.
    If an event loop is already running, submits to a dedicated background ThreadPoolExecutor.
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            return executor.submit(asyncio.run, coro_fn()).result()
    else:
        return asyncio.run(coro_fn())


class CrawleeWebCrawler:
    """
    Controlled Web Crawling Engine built on Crawlee BeautifulSoupCrawler.
    Manages starting URLs, crawl queues, concurrency, and rich metadata extraction.
    """

    def __init__(
        self,
        max_requests_per_crawl: int = 5,
        max_crawl_depth: int = 1,
        request_timeout_seconds: int = 15,
        max_retries: int = 2,
        allowed_domains: Optional[List[str]] = None
    ):
        self.max_requests_per_crawl = max(1, min(max_requests_per_crawl, 10))
        self.max_crawl_depth = max(1, min(max_crawl_depth, 2))
        self.request_timeout = timedelta(seconds=max(5, request_timeout_seconds))
        self.max_retries = max(0, min(max_retries, 3))
        self.allowed_domains = [d.lower() for d in allowed_domains] if allowed_domains else None

    async def _crawl_async(self, start_urls: List[str]) -> List[Dict[str, Any]]:
        """Internal asynchronous crawl execution using Crawlee BeautifulSoupCrawler with MemoryStorageClient."""
        retrieved_pages: List[Dict[str, Any]] = []
        visited_urls: Set[str] = set()

        storage_client = MemoryStorageClient()
        crawler = BeautifulSoupCrawler(
            max_requests_per_crawl=self.max_requests_per_crawl,
            max_request_retries=self.max_retries,
            request_handler_timeout=self.request_timeout,
            storage_client=storage_client,
            configure_logging=False,
            parser="html.parser"
        )

        @crawler.router.default_handler
        async def request_handler(context: BeautifulSoupCrawlingContext) -> None:
            nonlocal retrieved_pages
            url = context.request.url
            norm_url = _normalize_url(url)
            if norm_url in visited_urls:
                return
            visited_urls.add(norm_url)

            domain = urllib.parse.urlparse(url).netloc.lower()
            if self.allowed_domains and not any(allowed in domain for allowed in self.allowed_domains):
                logger.info(f"[Crawlee] Skipping out-of-scope domain: {domain}")
                return

            soup = context.soup
            title = ""
            if soup and soup.title and soup.title.string:
                title = soup.title.string.strip()
            elif soup and soup.find("h1"):
                title = soup.find("h1").get_text(strip=True)

            status_code = context.http_response.status_code if context.http_response else 200
            html_text = str(soup) if soup else ""

            page_entry = {
                "url": url,
                "normalized_url": norm_url,
                "title": title or "Web Page",
                "html": html_text,
                "status_code": status_code,
                "domain": domain,
                "engine": "Crawlee BeautifulSoupCrawler",
                "retrieved_at": time.time(),
                "error": None
            }
            retrieved_pages.append(page_entry)

            # Check if deeper crawling is enabled
            if self.max_crawl_depth > 1 and len(visited_urls) < self.max_requests_per_crawl:
                try:
                    await context.enqueue_links(
                        strategy="same-domain",
                        limit=2
                    )
                except Exception as e:
                    logger.debug(f"[Crawlee] enqueue_links note: {e}")

        @crawler.failed_request_handler
        async def failed_request_handler(context: BeautifulSoupCrawlingContext, error: Exception) -> None:
            nonlocal retrieved_pages
            url = context.request.url
            domain = urllib.parse.urlparse(url).netloc.lower()
            logger.warning(f"[Crawlee] Request failed for {url}: {error}")
            retrieved_pages.append({
                "url": url,
                "normalized_url": _normalize_url(url),
                "title": "Unreachable Source",
                "html": "",
                "status_code": getattr(error, "status_code", 500) if hasattr(error, "status_code") else 500,
                "domain": domain,
                "engine": "Crawlee BeautifulSoupCrawler (Failed)",
                "retrieved_at": time.time(),
                "error": str(error)
            })

        await crawler.run(start_urls)
        return retrieved_pages

    def crawl(self, start_urls: List[str]) -> List[Dict[str, Any]]:
        """Synchronous wrapper to execute Crawlee crawl."""
        clean_urls = [
            _normalize_url(u) for u in start_urls
            if u and u.strip() and not any(u.lower().split("?")[0].endswith(ext) for ext in [".pdf", ".zip", ".tar.gz", ".tgz", ".exe", ".dmg", ".pkg", ".png", ".jpg", ".jpeg", ".gif"])
        ]
        unique_urls = list(dict.fromkeys(clean_urls))[:self.max_requests_per_crawl]
        if not unique_urls:
            return []

        async def _run():
            return await self._crawl_async(unique_urls)

        return _run_coroutine_sync(_run)


def crawling_worker_node(state: ResearchState) -> Dict[str, Any]:
    """
    Execution Worker 3: Crawling Worker (Crawlee Engine)
    Performs controlled, high-speed page retrieval using Crawlee BeautifulSoupCrawler.
    """
    request_id = state.get("request_id", "req_unknown")
    execution_id = state.get("execution_id", "exec_unknown")
    conversation_id = state.get("conversation_id", None)
    selected_urls = state.get("selected_urls", [])
    t0 = time.time()

    # Filter out targets specifically flagged for headless browser execution
    http_targets = [u for u in selected_urls if not u.get("needs_browser_rendering")]
    target_urls = [u.get("url", "").strip() for u in http_targets if u.get("url")]

    event_bus.publish(
        request_id=request_id,
        execution_id=execution_id,
        conversation_id=conversation_id,
        node_id="crawling_worker",
        component_name="Crawling Worker",
        component_type="execution_worker",
        event_type="NODE_STARTED",
        execution_status="RUNNING",
        safe_task_summary=f"Crawlee engine dispatching crawl across {len(target_urls)} target URL(s)",
        tool_name="Crawlee BeautifulSoupCrawler",
        timestamp=t0
    )

    crawled_pages = list(state.get("crawled_pages", []))
    urls_to_fetch = []
    now = time.time()

    # 1. Check in-memory TTL page cache for instant reuse
    for item in http_targets:
        raw_url = item.get("url", "").strip()
        norm_url = _normalize_url(raw_url)
        if norm_url in _PAGE_CACHE:
            cached_at, cached_entry = _PAGE_CACHE[norm_url]
            if (now - cached_at) < PAGE_CACHE_TTL:
                logger.info(f"[Crawlee Cache HIT] {norm_url}")
                crawled_pages.append(cached_entry)
                continue
        urls_to_fetch.append(raw_url)

    # 2. Execute Crawlee on URLs requiring fresh retrieval
    if urls_to_fetch:
        max_pages = min(len(urls_to_fetch), 5)
        crawler = CrawleeWebCrawler(
            max_requests_per_crawl=max_pages,
            max_crawl_depth=1,
            request_timeout_seconds=15,
            max_retries=2
        )
        try:
            fetched_results = crawler.crawl(urls_to_fetch)
            for page in fetched_results:
                norm = page.get("normalized_url")
                if norm and page.get("html"):
                    _PAGE_CACHE[norm] = (time.time(), page)
                crawled_pages.append(page)
        except Exception as e:
            logger.error(f"[CrawleeWorker] Unhandled crawler exception: {e}")
            # Fallback for failed crawls using snippet from selected_urls
            for item in http_targets:
                if not any(p.get("url") == item.get("url") for p in crawled_pages):
                    crawled_pages.append({
                        "url": item.get("url", ""),
                        "title": item.get("title", "Search Result"),
                        "snippet": item.get("snippet", ""),
                        "domain": item.get("domain", ""),
                        "html": f"<html><body><h1>{item.get('title', '')}</h1><p>{item.get('snippet', '')}</p></body></html>",
                        "status_code": 200,
                        "engine": "Fallback Snippet Synthesizer",
                        "retrieved_at": time.time(),
                        "error": str(e)
                    })

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
        safe_task_summary=f"Crawlee retrieved {len(crawled_pages)} pages in {duration:.2f}s",
        safe_output_summary=f"Domains: {', '.join(domains[:3])}",
        tool_name="Crawlee BeautifulSoupCrawler",
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
