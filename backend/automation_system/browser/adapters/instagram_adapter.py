"""
O.P.S. 2.0 Instagram Automation Adapter
Handles Instagram navigation, Reels discovery, login barrier handling,
and empirical state verification.
"""

import time
import logging
from typing import Dict, Any, Optional
from playwright.sync_api import Page
from automation_system.browser.navigation_engine import NavigationEngine
from automation_system.browser.search_engine import SearchEngine
from automation_system.browser.verification_engine import BrowserVerificationEngine

logger = logging.getLogger("OPS.Adapter.Instagram")


class InstagramAdapter:
    """Specialized adapter for Instagram automation workflows."""

    BASE_URL = "https://www.instagram.com"
    REELS_URL = "https://www.instagram.com/reels/"

    @classmethod
    def open_home(cls, page: Page) -> Dict[str, Any]:
        """Navigates to Instagram homepage."""
        res = NavigationEngine.navigate(page, cls.BASE_URL)
        cls.handle_login_barrier(page)
        return res

    @classmethod
    def navigate_reels(cls, page: Page) -> Dict[str, Any]:
        """Navigates directly to Instagram Reels feed."""
        t0 = time.time()
        res = NavigationEngine.navigate(page, cls.REELS_URL)
        time.sleep(1.5)
        cls.handle_login_barrier(page)

        verif = BrowserVerificationEngine.verify_instagram_view(page, expected_section="reels")
        duration = round(time.time() - t0, 2)

        return {
            "success": verif.get("verified", True),
            "action": "instagram_reels",
            "url": page.url,
            "page_title": page.title(),
            "duration_s": duration,
            "verification": verif
        }

    @classmethod
    def handle_login_barrier(cls, page: Page):
        """
        Detects login walls or cookie modals on Instagram and attempts graceful dismissal.
        Does not crash if Instagram requests authentication.
        """
        dismiss_candidates = [
            "button:has-text('Not Now')",
            "button:has-text('Not now')",
            "button:has-text('Decline optional cookies')",
            "button:has-text('Only allow essential cookies')",
            "button:has-text('Allow all cookies')",
            "div[role='dialog'] button:has-text('Close')",
            "svg[aria-label='Close']"
        ]
        for sel in dismiss_candidates:
            try:
                btn = page.locator(sel).first
                if btn.is_visible(timeout=800):
                    btn.click(timeout=1000)
                    time.sleep(0.3)
                    logger.info(f"Dismissed Instagram prompt: {sel}")
                    break
            except Exception:
                continue

    @classmethod
    def search_profile_or_tag(cls, page: Page, query: str) -> Dict[str, Any]:
        """Searches Instagram for a profile or hashtag."""
        clean_q = query.lstrip("@#").strip()
        target_url = f"https://www.instagram.com/explore/tags/{clean_q}/" if query.startswith("#") else f"https://www.instagram.com/{clean_q}/"
        res = NavigationEngine.navigate(page, target_url)
        cls.handle_login_barrier(page)
        return res
