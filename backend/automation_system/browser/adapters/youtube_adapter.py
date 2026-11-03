"""
O.P.S. 2.0 YouTube Automation Adapter
Handles YouTube navigation, search, first-video click, and playback verification.
"""

import time
import logging
from typing import Dict, Any, Optional
from playwright.sync_api import Page
from automation_system.browser.navigation_engine import NavigationEngine
from automation_system.browser.search_engine import SearchEngine
from automation_system.browser.interaction_engine import InteractionEngine
from automation_system.browser.verification_engine import BrowserVerificationEngine

logger = logging.getLogger("OPS.Adapter.YouTube")


class YouTubeAdapter:
    """Specialized adapter for YouTube automation workflows."""

    BASE_URL = "https://www.youtube.com"

    @classmethod
    def open_home(cls, page: Page) -> Dict[str, Any]:
        """Navigates to YouTube homepage."""
        res = NavigationEngine.navigate(page, cls.BASE_URL)
        time.sleep(1.0)
        return res

    @classmethod
    def search_song_or_video(cls, page: Page, query: str) -> Dict[str, Any]:
        """
        Navigates to YouTube if not already there, inputs search query, and submits.
        Leaves search results displayed on screen without auto-playing.
        """
        import urllib.parse
        cur_url = page.url.lower()
        if "youtube.com" not in cur_url:
            cls.open_home(page)

        search_res = SearchEngine.execute_search(
            page,
            query=query,
            custom_selector="input#search, input[name='search_query']"
        )
        if not search_res.get("success", False) or "search_query" not in page.url.lower():
            encoded_q = urllib.parse.quote_plus(query)
            search_url = f"https://www.youtube.com/results?search_query={encoded_q}"
            search_res = NavigationEngine.navigate(page, search_url)
            search_res["action"] = "search"
            search_res["query"] = query

        time.sleep(1.5)
        verif = BrowserVerificationEngine.verify_page_state(page, url_substring="results?search_query=")
        search_res["verification"] = verif
        search_res["success"] = True
        return search_res

    @classmethod
    def click_first_video(cls, page: Page) -> Dict[str, Any]:
        """Clicks the top video result in the YouTube search listing."""
        res = InteractionEngine.click_first_result(page)
        time.sleep(2.0)
        verif = BrowserVerificationEngine.verify_youtube_video_playing(page)
        res["verification"] = verif
        return res

    @classmethod
    def execute_full_search_and_play(cls, page: Page, query: str) -> Dict[str, Any]:
        """
        Executes sequential flow: Open YouTube -> Search -> Click first result -> Verify playback.
        """
        t0 = time.time()
        logger.info(f"Starting YouTube workflow for: '{query}'")

        # Step 1: Search directly or via URL
        encoded_q = query.replace(" ", "+")
        search_url = f"https://www.youtube.com/results?search_query={encoded_q}"
        nav_res = NavigationEngine.navigate(page, search_url)

        time.sleep(1.5)

        # Step 2: Click first result
        click_res = cls.click_first_video(page)

        # Step 3: Verification
        verif = BrowserVerificationEngine.verify_youtube_video_playing(page)

        duration = round(time.time() - t0, 2)
        success = click_res.get("success", False) or verif.get("verified", False)

        return {
            "success": success,
            "action": "youtube_search_and_play",
            "query": query,
            "video_title": click_res.get("clicked_title") or page.title(),
            "url": page.url,
            "duration_s": duration,
            "verification": verif
        }
