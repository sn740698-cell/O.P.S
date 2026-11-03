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

    @classmethod
    def pause_playback(cls, page: Page) -> Dict[str, Any]:
        """Pauses the currently playing YouTube video using player shortcut."""
        try:
            # YouTube standard shortcut 'k' toggles pause
            page.keyboard.press("k")
            time.sleep(1.0)
            verif = BrowserVerificationEngine.verify_page_state(page, url_substring="watch")
            return {
                "success": True,
                "action": "youtube_pause",
                "state": "PAUSED",
                "verification": verif
            }
        except Exception as e:
            return {"success": False, "action": "youtube_pause", "error": str(e)}

    @classmethod
    def resume_playback(cls, page: Page) -> Dict[str, Any]:
        """Resumes YouTube playback."""
        try:
            page.keyboard.press("k")
            time.sleep(1.0)
            verif = BrowserVerificationEngine.verify_youtube_video_playing(page)
            return {
                "success": True,
                "action": "youtube_resume",
                "state": "PLAYING",
                "verification": verif
            }
        except Exception as e:
            return {"success": False, "action": "youtube_resume", "error": str(e)}

    @classmethod
    def stop_playback(cls, page: Page) -> Dict[str, Any]:
        """Stops YouTube playback and resets player."""
        try:
            # Pauses video and rewinds to 0
            page.keyboard.press("0")
            page.keyboard.press("k")
            return {"success": True, "action": "youtube_stop", "state": "STOPPED"}
        except Exception as e:
            return {"success": False, "action": "youtube_stop", "error": str(e)}

    @classmethod
    def inspect_search_results(cls, page: Page, max_items: int = 5) -> Dict[str, Any]:
        """Extracts visible video titles and links from YouTube search page."""
        try:
            time.sleep(1.5)
            titles = []
            links = page.locator("ytd-video-renderer a#video-title")
            count = min(links.count(), max_items)
            for i in range(count):
                el = links.nth(i)
                t_text = el.text_content() or ""
                href = el.get_attribute("href") or ""
                if t_text.strip():
                    titles.append({
                        "rank": i + 1,
                        "title": t_text.strip(),
                        "url": f"https://www.youtube.com{href}" if href.startswith("/") else href
                    })

            return {
                "success": len(titles) > 0,
                "action": "youtube_inspect_results",
                "results_count": len(titles),
                "items": titles
            }
        except Exception as e:
            return {"success": False, "action": "youtube_inspect_results", "error": str(e)}
