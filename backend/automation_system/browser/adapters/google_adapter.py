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
    def search(cls, page: Page, query: str) -> Dict[str, Any]:
        """Navigates to Google search results for the given query."""
        t0 = time.time()
        encoded = query.replace(" ", "+")
        url = f"https://www.google.com/search?q={encoded}"
        res = NavigationEngine.navigate(page, url)
        time.sleep(1.0)
        return res

    @classmethod
    def click_top_result(cls, page: Page) -> Dict[str, Any]:
        """Clicks the highest-ranked organic Google result."""
        res = InteractionEngine.click_first_result(page)
        time.sleep(1.5)
        verif = BrowserVerificationEngine.verify_page_state(page)
        res["verification"] = verif
        return res
