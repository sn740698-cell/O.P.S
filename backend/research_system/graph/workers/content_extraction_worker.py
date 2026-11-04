"""
O.P.S. 2.0 — Content Extraction Worker (BeautifulSoup4 Engine)
Execution Worker 5: Pure BeautifulSoup4 HTML Parsing and Structured Content Extraction.

Responsibilities:
- Parsing retrieved HTML with BeautifulSoup4.
- Extracting page title, semantic headings (h1, h2, h3), paragraphs, lists, and tables.
- Converting HTML tables into clean GitHub-flavored Markdown tables.
- Converting ordered and unordered lists into structured Markdown items.
- Filtering out boilerplate, navigation, footers, headers, scripts, styles, and advertisements.
- Extracting authoritative, relevant links with normalized absolute URLs.
- Tracking extraction status: SUCCESS, INSUFFICIENT_CONTENT, or EXTRACTION_FAILED.
"""

import time
import logging
import re
import urllib.parse
from typing import Dict, Any, List, Optional
from bs4 import BeautifulSoup, Tag

from research_system.graph.state import ResearchState
from research_system.events.event_bus import event_bus

logger = logging.getLogger("OPS.Research.BS4Extractor")


def _convert_table_to_markdown(table: Tag) -> Optional[str]:
    """Converts an HTML <table> element into a GitHub-flavored Markdown table string."""
    try:
        rows = []
        for tr in table.find_all("tr"):
            cells = [re.sub(r"\s+", " ", c.get_text(strip=True)) for c in tr.find_all(["th", "td"])]
            if any(cells):
                rows.append(cells)

        if not rows:
            return None

        # Determine column count
        col_count = max(len(r) for r in rows)
        if col_count == 0:
            return None

        # Normalize all rows to equal length
        normalized_rows = []
        for r in rows:
            padded = list(r) + [""] * (col_count - len(r))
            # Escape pipe symbols in cell text
            cleaned_row = [cell.replace("|", "\\|") for cell in padded]
            normalized_rows.append(cleaned_row)

        header = normalized_rows[0]
        separator = ["---"] * col_count
        lines = [
            "| " + " | ".join(header) + " |",
            "| " + " | ".join(separator) + " |"
        ]
        for row in normalized_rows[1:]:
            lines.append("| " + " | ".join(row) + " |")

        return "\n".join(lines)
    except Exception as e:
        logger.debug(f"Table markdown conversion error: {e}")
        return None


def _extract_lists_to_markdown(container: Tag) -> List[str]:
    """Extracts unordered and ordered lists into structured markdown strings."""
    extracted_lists = []
    try:
        for ul_or_ol in container.find_all(["ul", "ol"]):
            items = []
            is_ordered = ul_or_ol.name == "ol"
            for idx, li in enumerate(ul_or_ol.find_all("li", recursive=False), 1):
                txt = re.sub(r"\s+", " ", li.get_text(strip=True))
                if txt and len(txt) > 3:
                    prefix = f"{idx}." if is_ordered else "-"
                    items.append(f"{prefix} {txt}")
            if items:
                extracted_lists.append("\n".join(items))
    except Exception as e:
        logger.debug(f"List extraction error: {e}")
    return extracted_lists


def _extract_relevant_links(soup: Tag, base_url: str) -> List[Dict[str, str]]:
    """Extracts high-signal navigation and resource links, resolved to absolute URLs."""
    relevant_links = []
    seen_urls = set()
    try:
        for a in soup.find_all("a", href=True):
            href = a.get("href", "").strip()
            anchor_text = re.sub(r"\s+", " ", a.get_text(strip=True))
            if not href or href.startswith("#") or href.startswith("javascript:"):
                continue
            if len(anchor_text) < 4:
                continue

            absolute_url = urllib.parse.urljoin(base_url, href)
            # Filter obvious noise
            if any(term in anchor_text.lower() for term in ["cookie", "privacy policy", "terms of service", "sign in", "login"]):
                continue

            if absolute_url not in seen_urls:
                seen_urls.add(absolute_url)
                relevant_links.append({
                    "text": anchor_text[:80],
                    "url": absolute_url
                })
            if len(relevant_links) >= 12:
                break
    except Exception as e:
        logger.debug(f"Relevant link extraction error: {e}")
    return relevant_links


def extract_with_bs4(
    html: str,
    url: str,
    title: str = "",
    domain: str = "",
    status_code: int = 200,
    retrieved_at: Optional[float] = None
) -> Dict[str, Any]:
    """
    Core BeautifulSoup4 extraction function.
    Cleans HTML, extracts semantic structure (title, headings, text, tables, lists, links),
    and produces structured output with extraction status.
    """
    now = retrieved_at or time.time()
    effective_domain = domain or (urllib.parse.urlparse(url).netloc.lower() if url else "")

    if not html or not html.strip():
        return {
            "page_title": title or "Empty Document",
            "url": url,
            "domain": effective_domain,
            "headings": [],
            "clean_text": "",
            "tables": [],
            "lists": [],
            "relevant_links": [],
            "retrieval_timestamp": now,
            "http_status": status_code,
            "extraction_status": "EXTRACTION_FAILED",
            "extraction_method": "BeautifulSoup4 HTML Parser"
        }

    soup = BeautifulSoup(html, "html.parser")

    # Extract page title before removing head/meta tags
    page_title = title
    if not page_title or page_title == "Web Page":
        if soup.title and soup.title.string:
            page_title = soup.title.string.strip()
        elif soup.find("h1"):
            page_title = soup.find("h1").get_text(strip=True)
    page_title = page_title or "Web Document"

    # 1. Extract markdown tables before decomposing elements
    tables: List[str] = []
    for table_tag in soup.find_all("table"):
        table_md = _convert_table_to_markdown(table_tag)
        if table_md and len(table_md) > 20:
            tables.append(table_md)

    # 2. Extract structured lists
    lists: List[str] = _extract_lists_to_markdown(soup)

    # 3. Extract relevant links
    relevant_links: List[Dict[str, str]] = _extract_relevant_links(soup, url)

    # 4. Extract semantic headings (h1, h2, h3)
    headings: List[str] = []
    for h in soup.find_all(["h1", "h2", "h3"]):
        h_text = re.sub(r"\s+", " ", h.get_text(strip=True))
        if h_text and len(h_text) > 3 and h_text not in headings:
            headings.append(h_text)

    # 5. Remove unwanted elements, boilerplate, ads, scripts, navigation
    noise_selectors = [
        "script", "style", "nav", "footer", "header", "noscript", "svg",
        "form", "aside", "iframe", "dialog",
        '[class*="cookie"]', '[id*="cookie"]',
        '[class*="ad-"]', '[class*="advertisement"]', '[id*="banner"]',
        '[class*="sidebar"]', '[id*="sidebar"]',
        '[class*="menu"]', '[id*="navigation"]'
    ]
    for sel in noise_selectors:
        for element in soup.select(sel):
            element.decompose()

    # 6. Locate main content container if present, otherwise body
    main_container = soup.find(["main", "article", "div[role='main']", "div#content", "div.content", "body"])
    container = main_container or soup

    # 7. Extract substantive paragraphs and text blocks
    paragraphs: List[str] = []
    for block in container.find_all(["p", "article", "section", "div", "pre", "blockquote"]):
        txt = re.sub(r"\s+", " ", block.get_text(separator=" ", strip=True))
        if len(txt) > 35 and txt not in paragraphs:
            # Avoid repeating text that is already a substring of an earlier block
            if not any(txt in p for p in paragraphs):
                paragraphs.append(txt)

    if paragraphs:
        clean_text = "\n\n".join(paragraphs[:20])
    else:
        raw_text = container.get_text(separator="\n", strip=True)
        clean_text = re.sub(r"\n{3,}", "\n\n", raw_text)

    # Normalize whitespace
    clean_text = re.sub(r"[ \t]+", " ", clean_text).strip()

    # Determine extraction status
    if len(clean_text) >= 150 or tables:
        extraction_status = "SUCCESS"
    elif len(clean_text) >= 30:
        extraction_status = "INSUFFICIENT_CONTENT"
    else:
        extraction_status = "EXTRACTION_FAILED"

    return {
        "page_title": page_title,
        "title": page_title,
        "url": url,
        "domain": effective_domain,
        "headings": headings[:10],
        "clean_text": clean_text[:6000],
        "tables": tables[:5],
        "lists": lists[:8],
        "relevant_links": relevant_links[:10],
        "retrieval_timestamp": now,
        "http_status": status_code,
        "extraction_status": extraction_status,
        "extraction_method": "BeautifulSoup4 HTML Parser"
    }


def content_extraction_worker_node(state: ResearchState) -> Dict[str, Any]:
    """
    Execution Worker 5: Content Extraction Worker
    Pure BeautifulSoup4 parsing and content cleaning for all retrieved HTML documents.
    """
    request_id = state.get("request_id", "req_unknown")
    execution_id = state.get("execution_id", "exec_unknown")
    conversation_id = state.get("conversation_id", None)
    crawled_pages = state.get("crawled_pages", [])
    t0 = time.time()

    event_bus.publish(
        request_id=request_id,
        execution_id=execution_id,
        conversation_id=conversation_id,
        node_id="content_extraction_worker",
        component_name="Content Extraction Worker",
        component_type="execution_worker",
        event_type="NODE_STARTED",
        execution_status="RUNNING",
        safe_task_summary=f"Extracting structured content from {len(crawled_pages)} pages via BeautifulSoup4",
        tool_name="BeautifulSoup4 Parser",
        timestamp=t0
    )

    extracted_contents = []
    for page in crawled_pages:
        html = page.get("html", "")
        url = page.get("url", "")
        title = page.get("title", "")
        domain = page.get("domain", "")
        status_code = page.get("status_code", 200)
        retrieved_at = page.get("retrieved_at", time.time())

        extracted = extract_with_bs4(
            html=html,
            url=url,
            title=title,
            domain=domain,
            status_code=status_code,
            retrieved_at=retrieved_at
        )
        extracted_contents.append(extracted)

    duration = time.time() - t0
    success_count = sum(1 for e in extracted_contents if e.get("extraction_status") == "SUCCESS")

    event_bus.publish(
        request_id=request_id,
        execution_id=execution_id,
        conversation_id=conversation_id,
        node_id="content_extraction_worker",
        component_name="Content Extraction Worker",
        component_type="execution_worker",
        event_type="NODE_COMPLETED",
        execution_status="COMPLETED",
        safe_task_summary=f"BeautifulSoup4 parsed {len(extracted_contents)} documents ({success_count} SUCCESS) in {duration:.2f}s",
        safe_output_summary=f"Parsed {len(extracted_contents)} docs, {sum(len(e['tables']) for e in extracted_contents)} tables extracted",
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
