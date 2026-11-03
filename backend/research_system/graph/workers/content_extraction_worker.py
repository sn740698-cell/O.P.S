import time
import logging
import re
import urllib.parse
from typing import Dict, Any, List
from bs4 import BeautifulSoup
from research_system.graph.state import ResearchState
from research_system.events.event_bus import event_bus

logger = logging.getLogger(__name__)

def _extract_with_bs4(html: str, url: str, title: str, domain: str = "") -> Dict[str, Any]:
    """
    Standard HTML extraction using BeautifulSoup4: removes boilerplate, scripts, ads, and navigation.
    """
    soup = BeautifulSoup(html, "html.parser")

    # Remove unwanted tags, cookie notices, and navigation elements
    for tag in soup(["script", "style", "nav", "footer", "header", "noscript", "svg", "form", "aside", "iframe"]):
        tag.decompose()

    # Extract headings
    headings = []
    for h in soup.find_all(["h1", "h2", "h3"]):
        text = h.get_text(strip=True)
        if text and len(text) > 3:
            headings.append(text)

    # Extract paragraphs and body text
    paragraphs = []
    for p in soup.find_all(["p", "article", "section", "div"]):
        text = p.get_text(separator=" ", strip=True)
        if len(text) > 40 and text not in paragraphs:
            paragraphs.append(text)

    clean_text = "\n\n".join(paragraphs[:15]) if paragraphs else soup.get_text(separator=" ", strip=True)
    # Normalize excessive whitespace
    clean_text = re.sub(r"\s+", " ", clean_text).strip()

    page_title = title or (soup.title.string.strip() if soup.title and soup.title.string else "Web Page")
    return {
        "url": url,
        "title": page_title,
        "domain": domain or (urllib.parse.urlparse(url).netloc.lower() if url else ""),
        "clean_text": clean_text[:4000],
        "headings": headings[:8],
        "extraction_method": "BeautifulSoup4 Standard HTML"
    }

def content_extraction_worker_node(state: ResearchState) -> Dict[str, Any]:
    """
    Execution Worker 5: Content Extraction Worker
    BeautifulSoup4 for normal HTML parsing and content cleaning; ScrapeGraphAI for specialized extraction.
    """
    request_id = state.get("request_id", "req_unknown")
    execution_id = state.get("execution_id", "exec_unknown")
    crawled_pages = state.get("crawled_pages", [])
    t0 = time.time()

    event_bus.publish(
        request_id=request_id,
        execution_id=execution_id,
        node_id="content_extraction_worker",
        component_name="Content Extraction Worker",
        component_type="execution_worker",
        event_type="NODE_STARTED",
        execution_status="RUNNING",
        safe_task_summary=f"Parsing and cleaning HTML from {len(crawled_pages)} pages using BeautifulSoup4",
        tool_name="BeautifulSoup4 & ScrapeGraphAI",
        timestamp=t0
    )

    extracted_contents = []
    conversation_id = state.get("conversation_id", None)
    for page in crawled_pages:
        html = page.get("html", "")
        url = page.get("url", "")
        title = page.get("title", "")
        domain = page.get("domain", "")
        if html:
            extracted = _extract_with_bs4(html, url, title, domain=domain)
            extracted_contents.append(extracted)

    duration = time.time() - t0

    event_bus.publish(
        request_id=request_id,
        execution_id=execution_id,
        node_id="content_extraction_worker",
        component_name="Content Extraction Worker",
        component_type="execution_worker",
        event_type="NODE_COMPLETED",
        execution_status="COMPLETED",
        safe_task_summary=f"Extracted clean text from {len(extracted_contents)} web documents in {duration:.2f}s",
        safe_output_summary=f"Average text length: {int(sum(len(e['clean_text']) for e in extracted_contents) / max(len(extracted_contents), 1))} chars",
        tool_name="BeautifulSoup4 Parser",
        timestamp=time.time()
    )

    node_history = list(state.get("node_history", []))
    node_history.append("content_extraction_worker")

    return {
        "extracted_contents": extracted_contents,
        "current_active_component": "content_extraction_worker",
        "node_history": node_history
    }
