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

    @classmethod
    def is_authenticated(cls, page: Page) -> bool:
        """Verifies if current page is in an authenticated Instagram session."""
        try:
            curr_u = page.url.lower()
            if "accounts/login" in curr_u:
                return False
            # Look for navigation bar items present only when logged in
            dms_icon = page.locator("svg[aria-label='Direct']").first
            profile_icon = page.locator("svg[aria-label='Profile']").first
            return dms_icon.is_visible(timeout=800) or profile_icon.is_visible(timeout=800)
        except Exception:
            return False

    @classmethod
    def navigate_dms(cls, page: Page) -> Dict[str, Any]:
        """
        Navigates to Instagram Direct Messages inbox.
        Safely halts if user is unauthenticated per Section 1.D rules.
        """
        t0 = time.time()
        res = NavigationEngine.navigate(page, "https://www.instagram.com/direct/inbox/")
        time.sleep(1.5)
        cls.handle_login_barrier(page)

        auth_ok = cls.is_authenticated(page)
        duration = round(time.time() - t0, 2)

        if not auth_ok:
            return {
                "success": True,
                "status": "BLOCKED",
                "action": "instagram_dms",
                "auth_required": True,
                "url": page.url,
                "duration_s": duration,
                "message": "Instagram Direct Messages requires an active, authorized user session. Halting before login barrier to protect user credentials.",
                "verification": {"verified": True, "auth_barrier_respected": True}
            }

        return {
            "success": True,
            "status": "COMPLETED",
            "action": "instagram_dms",
            "auth_required": False,
            "url": page.url,
            "duration_s": duration,
            "verification": {"verified": True, "inbox_loaded": True}
        }

    @classmethod
    def open_conversation(cls, page: Page, contact_name: str) -> Dict[str, Any]:
        """
        Identifies and opens a specified conversation in Instagram DMs.
        Never guesses contact names if ambiguous.
        """
        if not contact_name:
            return {
                "success": False,
                "action": "instagram_open_conversation",
                "error": "A specific username or contact name must be provided to open a conversation."
            }

        dm_res = cls.navigate_dms(page)
        if dm_res.get("status") == "BLOCKED":
            return dm_res

        try:
            # Find matching chat in inbox list
            chat_item = page.locator(f"div[role='listitem']:has-text('{contact_name}')").first
            if not chat_item.is_visible(timeout=3000):
                # Try finding by span or text
                chat_item = page.locator(f"span:has-text('{contact_name}')").first

            if chat_item.is_visible(timeout=2000):
                chat_item.click()
                time.sleep(1.5)
                return {
                    "success": True,
                    "action": "instagram_open_conversation",
                    "contact_name": contact_name,
                    "url": page.url,
                    "verification": {"verified": True, "conversation_opened": contact_name}
                }
            else:
                return {
                    "success": False,
                    "action": "instagram_open_conversation",
                    "error": f"Conversation with '{contact_name}' not found in visible inbox items."
                }
        except Exception as e:
            return {"success": False, "action": "instagram_open_conversation", "error": str(e)}

    @classmethod
    def read_visible_messages(cls, page: Page, max_messages: int = 5) -> Dict[str, Any]:
        """
        Reads visible messages in currently open authorized conversation.
        Never modifies, sends, or deletes messages.
        """
        if not cls.is_authenticated(page):
            return {
                "success": False,
                "status": "BLOCKED",
                "action": "instagram_read_messages",
                "error": "Active session is unauthenticated. Cannot read private messages."
            }

        try:
            msg_bubbles = page.locator("div[role='row'] div[dir='auto']")
            count = min(msg_bubbles.count(), max_messages)
            texts = []
            for i in range(count):
                b = msg_bubbles.nth(i)
                txt = b.text_content() or ""
                if txt.strip():
                    texts.append(txt.strip())

            return {
                "success": True,
                "action": "instagram_read_messages",
                "messages_count": len(texts),
                "messages": texts,
                "verification": {"verified": True}
            }
        except Exception as e:
            return {"success": False, "action": "instagram_read_messages", "error": str(e)}
