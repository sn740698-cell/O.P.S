"""
O.P.S. 2.0 Google Search Automation Adapter
Handles Google searches, clicking organic search results, and verifying destination pages.
"""

import time
import logging
from typing import Dict, Any
from playwright.sync_api import Page
from automation_system.browser.navigation_engine import NavigationEngine
from automation_system.browser.interaction_engine import InteractionEngine
from automation_system.browser.verification_engine import BrowserVerificationEngine

logger = logging.getLogger("OPS.Adapter.Google")


class GoogleAdapter:
    """Specialized adapter for Google search and result exploration."""

    @classmethod
    def open_home(cls, page: Page) -> Dict[str, Any]:
        """Navigates to Google homepage."""
        return NavigationEngine.navigate(page, "https://www.google.com")

    @classmethod
    def search(cls, page: Page, query: str) -> Dict[str, Any]:
        """Navigates to Google search results for the given query."""
        t0 = time.time()
        import urllib.parse
        encoded = urllib.parse.quote_plus(query)
        url = f"https://www.google.com/search?q={encoded}"
        res = NavigationEngine.navigate(page, url)
        time.sleep(1.0)
        return res

    @classmethod
    def inspect_results(cls, page: Page, max_items: int = 5) -> Dict[str, Any]:
        """Extracts visible organic search result titles and destination links from Google."""
        try:
            results = []
            links = page.locator("div.g a:has(h3)")
            count = min(links.count(), max_items)
            for i in range(count):
                el = links.nth(i)
                h3 = el.locator("h3").first
                title = h3.text_content() if h3.is_visible(timeout=500) else ""
                href = el.get_attribute("href") or ""
                if title.strip() and href.startswith("http"):
                    results.append({
                        "rank": i + 1,
                        "title": title.strip(),
                        "url": href
                    })

            return {
                "success": len(results) > 0,
                "action": "google_inspect_results",
                "results_count": len(results),
                "items": results
            }
        except Exception as e:
            return {"success": False, "action": "google_inspect_results", "error": str(e)}

    @classmethod
    def click_top_result(cls, page: Page) -> Dict[str, Any]:
        """Clicks the highest-ranked organic Google result."""
        res = InteractionEngine.click_first_result(page)
        time.sleep(1.5)
        verif = BrowserVerificationEngine.verify_page_state(page)
        res["verification"] = verif
        return res

    @classmethod
    def extract_page_content(cls, page: Page, max_chars: int = 4000) -> Dict[str, Any]:
        """Extracts text content from the currently open Google result page."""
        try:
            title = page.title()
            url = page.url
            # Extract main readable text
            text = page.locator("body").inner_text() or ""
            clean_text = " ".join(text.split())[:max_chars]
            return {
                "success": True,
                "action": "google_extract_content",
                "title": title,
                "url": url,
                "content_preview": clean_text
            }
        except Exception as e:
            return {"success": False, "action": "google_extract_content", "error": str(e)}
