"""
O.P.S. 2.0 Browser Automation Specialist — Agent B7: Browser Verification Agent
Responsibilities:
- Verify page state (URL substrings, title matches, element presence)
- Verify media playback (YouTube videos, HTML5 video players)
- Check text content in DOM elements
- Capture verification screenshots for audit trails
"""

import logging
from typing import Dict, Any, Optional
from automation_system.browser.browser_manager import BrowserSessionManager
from automation_system.browser.verification_engine import BrowserVerificationEngine

logger = logging.getLogger("OPS.Browser.B7_VerificationAgent")


class B7_VerificationAgent:
    """Specialist Agent B7: Empirically verifies browser state and page reactions."""

    def __init__(self, conversation_id: str = "default_session"):
        self.agent_id = "agent_b7_verification"
        self.agent_name = "Browser Verification Agent"
        self.conversation_id = conversation_id or "default_session"
        self.manager = BrowserSessionManager()

    def verify_state(
        self,
        url_substring: Optional[str] = None,
        title_substring: Optional[str] = None,
        element_selector: Optional[str] = None
    ) -> Dict[str, Any]:
        """Empirically verifies URL, title, or element visibility."""
        try:
            def _verify(page):
                return BrowserVerificationEngine.verify_page_state(
                    page,
                    url_substring=url_substring,
                    title_substring=title_substring,
                    element_selector=element_selector
                )

            res = self.manager.execute_on_page(self.conversation_id, _verify, timeout=10.0)
            res["agent_id"] = self.agent_id
            return res
        except Exception as e:
            return {"verified": False, "agent_id": self.agent_id, "error": str(e)}

    def verify_youtube_playing(self) -> Dict[str, Any]:
        """Verifies active YouTube playback and title."""
        try:
            def _yt(page):
                return BrowserVerificationEngine.verify_youtube_video_playing(page)

            res = self.manager.execute_on_page(self.conversation_id, _yt, timeout=10.0)
            res["agent_id"] = self.agent_id
            return res
        except Exception as e:
            return {"verified": False, "agent_id": self.agent_id, "error": str(e)}

    def capture_screenshot(self, filename: Optional[str] = None) -> Dict[str, Any]:
        """Captures page screenshot for verification audit."""
        try:
            def _shot(page):
                return BrowserVerificationEngine.capture_verification_screenshot(page, filename=filename)

            res = self.manager.execute_on_page(self.conversation_id, _shot, timeout=15.0)
            res["agent_id"] = self.agent_id
            return res
        except Exception as e:
            return {"verified": False, "agent_id": self.agent_id, "error": str(e)}
