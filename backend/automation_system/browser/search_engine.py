"""
O.P.S. 2.0 Browser Search Engine
Locates search fields dynamically across web portals, enters search queries,
executes search submission, and waits for results to render.
"""

import time
import logging
from typing import Dict, Any, List, Optional
from playwright.sync_api import Page, Locator

logger = logging.getLogger("OPS.BrowserSearch")


class SearchEngine:
    """
    Automates search bars, inputs, submission, and result container waiting.
    """

    SEARCH_SELECTORS = [
        # YouTube
        "input#search",
        "input[name='search_query']",
        # Google
        "textarea[name='q']",
        "input[name='q']",
        # Instagram
        "input[aria-label='Search input']",
        "input[placeholder*='Search' i]",
        # Generic HTML5 / Web search bars
        "input[type='search']",
        "input[name='search']",
        "input[name='query']",
        "input[placeholder*='search' i]",
        "input[placeholder*='Search' i]"
    ]

    @classmethod
    def execute_search(
        cls,
        page: Page,
        query: str,
        custom_selector: Optional[str] = None,
        timeout_ms: int = 15000
    ) -> Dict[str, Any]:
        """
        Finds search input on page, enters query, presses Enter, and awaits results.
        """
        t0 = time.time()
        selectors = [custom_selector] if custom_selector else cls.SEARCH_SELECTORS

        search_input: Optional[Locator] = None
        matched_sel = None

        for sel in selectors:
            if not sel:
                continue
            try:
                loc = page.locator(sel).first
                if loc.is_visible(timeout=1000):
                    search_input = loc
                    matched_sel = sel
                    break
            except Exception:
                continue

        if not search_input:
            # Fallback: look by placeholder or role
            try:
                loc = page.get_by_placeholder("Search", exact=False).first
                if loc.is_visible(timeout=1000):
                    search_input = loc
                    matched_sel = "placeholder:Search"
            except Exception:
                pass

        if not search_input:
            return {
                "success": False,
                "action": "search",
                "query": query,
                "error": "No recognizable search input field found on current page."
            }

        try:
            # Click, clear, and fill query
            search_input.click()
            time.sleep(0.2)
            search_input.fill(query)
            time.sleep(0.3)
            # Submit via Enter
            search_input.press("Enter")
            time.sleep(1.5)

            # Wait for URL change or DOM load
            try:
                page.wait_for_load_state("domcontentloaded", timeout=timeout_ms)
            except Exception:
                pass

            duration = round(time.time() - t0, 2)
            logger.info(f"Executed search for '{query}' using '{matched_sel}' in {duration}s")

            return {
                "success": True,
                "action": "search",
                "query": query,
                "matched_selector": matched_sel,
                "current_url": page.url,
                "page_title": page.title(),
                "duration_s": duration
            }
        except Exception as e:
            logger.error(f"Search execution error: {e}")
            return {
                "success": False,
                "action": "search",
                "query": query,
                "error": str(e)
            }
