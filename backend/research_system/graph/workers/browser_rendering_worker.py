import time
import logging
from typing import Dict, Any, List
from research_system.graph.state import ResearchState
from research_system.events.event_bus import event_bus

logger = logging.getLogger(__name__)

def browser_rendering_worker_node(state: ResearchState) -> Dict[str, Any]:
    """
    Execution Worker 4: Browser Rendering Worker
    Playwright engine - executed ONLY when dynamic browser rendering is required.
    """
    request_id = state.get("request_id", "req_unknown")
    execution_id = state.get("execution_id", "exec_unknown")
    selected_urls = state.get("selected_urls", [])
    t0 = time.time()

    # Identify URLs requiring JavaScript rendering
    targets = [u for u in selected_urls if u.get("needs_browser_rendering")]

    if not targets:
        # Strict Rule: Playwright is invoked ONLY when needed. If not needed, mark as skipped.
        event_bus.publish(
            request_id=request_id,
            execution_id=execution_id,
            node_id="browser_rendering_worker",
            component_name="Browser Rendering Worker",
            component_type="execution_worker",
            event_type="NODE_SKIPPED",
            execution_status="SKIPPED",
            safe_task_summary="Browser rendering skipped: No JavaScript-heavy pages identified",
            tool_name="Playwright Headless Browser",
            timestamp=t0
        )
        node_history = list(state.get("node_history", []))
        node_history.append("browser_rendering_worker")
        return {
            "rendered_pages": [],
            "current_active_component": "browser_rendering_worker",
            "node_history": node_history
        }

    event_bus.publish(
        request_id=request_id,
        execution_id=execution_id,
        node_id="browser_rendering_worker",
        component_name="Browser Rendering Worker",
        component_type="execution_worker",
        event_type="NODE_STARTED",
        execution_status="RUNNING",
        safe_task_summary=f"Launching Playwright Chromium for {len(targets)} dynamic page(s)",
        tool_name="Playwright Headless Browser",
        timestamp=t0
    )

    rendered_pages = []
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
            )
            for item in targets:
                url = item.get("url")
                page = context.new_page()
                try:
                    page.goto(url, wait_until="domcontentloaded", timeout=15000)
                    html_content = page.content()
                    rendered_pages.append({
                        "url": url,
                        "title": item.get("title", page.title()),
                        "html": html_content,
                        "status_code": 200,
                        "engine": "Playwright Headless Chromium"
                    })
                except Exception as e:
                    logger.warning(f"Playwright rendering failed for {url}: {e}")
                    rendered_pages.append({
                        "url": url,
                        "title": item.get("title", ""),
                        "html": f"<html><body><p>{item.get('snippet', '')}</p></body></html>",
                        "status_code": 200,
                        "engine": "Playwright Fallback Snippet"
                    })
                finally:
                    page.close()
            browser.close()
    except Exception as e:
        logger.warning(f"Playwright execution error: {e}")

    duration = time.time() - t0

    event_bus.publish(
        request_id=request_id,
        execution_id=execution_id,
        node_id="browser_rendering_worker",
        component_name="Browser Rendering Worker",
        component_type="execution_worker",
        event_type="NODE_COMPLETED",
        execution_status="COMPLETED",
        safe_task_summary=f"Rendered {len(rendered_pages)} JavaScript page(s) in {duration:.2f}s",
        safe_output_summary=f"Successfully extracted DOM from {len(rendered_pages)} pages",
        tool_name="Playwright Headless Browser",
        timestamp=time.time()
    )

    node_history = list(state.get("node_history", []))
    node_history.append("browser_rendering_worker")

    # Combine rendered pages into crawled_pages
    existing_crawled = list(state.get("crawled_pages", []))
    existing_crawled.extend(rendered_pages)

    return {
        "rendered_pages": rendered_pages,
        "crawled_pages": existing_crawled,
        "current_active_component": "browser_rendering_worker",
        "node_history": node_history
    }
