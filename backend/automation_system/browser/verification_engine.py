"""
O.P.S. 2.0 Browser Verification Engine
Empirically verifies loaded pages, URL structures, DOM elements, and video players.
Captures verification screenshots for audit trails.
"""

import os
import time
import logging
from typing import Dict, Any, Optional
from playwright.sync_api import Page

logger = logging.getLogger("OPS.BrowserVerification")


class BrowserVerificationEngine:
    """
    Executes empirical post-action checks for web browser operations.
    """

    @classmethod
    def verify_page_state(
        cls,
        page: Page,
        url_substring: Optional[str] = None,
        title_substring: Optional[str] = None,
        element_selector: Optional[str] = None
    ) -> Dict[str, Any]:
        """Verifies current page matches expected URL, title, or DOM selector."""
        cur_url = getattr(page, "url", "")
        cur_title = getattr(page, "title", lambda: "")()

        url_ok = True
        if url_substring:
            url_ok = url_substring.lower() in cur_url.lower()

        title_ok = True
        if title_substring:
            title_ok = title_substring.lower() in cur_title.lower()

        elem_ok = True
        if element_selector:
            try:
                loc = page.locator(element_selector).first
                elem_ok = loc.is_visible(timeout=3000)
            except Exception:
                elem_ok = False

        verified = url_ok and title_ok and elem_ok
        return {
            "verified": verified,
            "verification_type": "browser_page_state",
            "current_url": cur_url,
            "page_title": cur_title,
            "url_matched": url_ok,
            "title_matched": title_ok,
            "element_visible": elem_ok,
            "error": None if verified else f"Expected url='{url_substring}', title='{title_substring}', selector='{element_selector}'"
        }

    @classmethod
    def verify_youtube_video_playing(cls, page: Page) -> Dict[str, Any]:
        """Empirically verifies that browser is on a YouTube watch page."""
        cur_url = page.url
        title = page.title()
        is_watch = "watch?v=" in cur_url or "/shorts/" in cur_url

        has_player = False
        try:
            player = page.locator(".html5-video-player, video.html5-main-video, #player").first
            has_player = player.is_visible(timeout=3000)
        except Exception:
            pass

        verified = is_watch or has_player
        return {
            "verified": verified,
            "verification_type": "youtube_video_active",
            "url": cur_url,
            "title": title,
            "is_watch_url": is_watch,
            "player_detected": has_player
        }

    @classmethod
    def verify_instagram_view(cls, page: Page, expected_section: Optional[str] = None) -> Dict[str, Any]:
        """Empirically verifies Instagram page state."""
        cur_url = page.url
        title = page.title()
        is_instagram = "instagram.com" in cur_url.lower()

        section_matched = True
        if expected_section:
            section_matched = expected_section.lower() in cur_url.lower()

        return {
            "verified": is_instagram and section_matched,
            "verification_type": "instagram_view",
            "url": cur_url,
            "title": title,
            "section": expected_section
        }

    @classmethod
    def capture_screenshot(cls, page: Page, output_path: str) -> Dict[str, Any]:
        """Captures page screenshot to disk."""
        try:
            os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
            page.screenshot(path=output_path, full_page=False)
            return {
                "success": True,
                "screenshot_path": output_path,
                "file_size": os.path.getsize(output_path)
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
