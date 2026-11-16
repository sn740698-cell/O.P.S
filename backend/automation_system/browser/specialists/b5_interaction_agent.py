"""
O.P.S. 2.0 Browser Automation Specialist — Agent B5: Browser Interaction Specialist
Responsibilities:
- Locate search boxes, input fields, buttons, and links using resilient Playwright locators
- Perform clicks, keyboard inputs, search submissions, and link clicks
- Auto-scroll to elements when off-screen
- Handle YouTube video playback and media controls
"""

import logging
from typing import Dict, Any, Optional
from automation_system.browser.browser_manager import BrowserSessionManager
from automation_system.browser.interaction_engine import InteractionEngine
from automation_system.browser.adapters.youtube_adapter import YouTubeAdapter

logger = logging.getLogger("OPS.Browser.B5_InteractionAgent")


class B5_InteractionAgent:
    """Specialist Agent B5: Handles element clicking, typing, and media interaction."""

    def __init__(self, conversation_id: str = "default_session"):
        self.agent_id = "agent_b5_interaction"
        self.agent_name = "Browser Interaction Agent"
        self.conversation_id = conversation_id or "default_session"
        self.manager = BrowserSessionManager()

    def click(self, selector: str, timeout_ms: int = 10000) -> Dict[str, Any]:
        """Clicks element matched by selector."""
        try:
            def _click(page):
                return InteractionEngine.click(page, selector, timeout_ms=timeout_ms)

            res = self.manager.execute_on_page(self.conversation_id, _click, timeout=timeout_ms / 1000.0 + 5.0)
            res["agent_id"] = self.agent_id
            return res
        except Exception as e:
            return {"success": False, "agent_id": self.agent_id, "action": "click", "selector": selector, "error": str(e)}

    def enter_search(self, query: str, selector: Optional[str] = None, submit: bool = True) -> Dict[str, Any]:
        """Finds search input, enters query, and optionally presses Enter."""
        try:
            def _search(page):
                return InteractionEngine.enter_search(page, query, selector=selector, submit=submit)

            res = self.manager.execute_on_page(self.conversation_id, _search, timeout=20.0)
            res["agent_id"] = self.agent_id
            return res
        except Exception as e:
            return {"success": False, "agent_id": self.agent_id, "action": "enter_search", "query": query, "error": str(e)}

    def click_first_result(self) -> Dict[str, Any]:
        """Finds and clicks top organic search result on Google/YouTube/etc."""
        try:
            def _click_res(page):
                return InteractionEngine.click_first_result(page)

            res = self.manager.execute_on_page(self.conversation_id, _click_res, timeout=20.0)
            res["agent_id"] = self.agent_id
            return res
        except Exception as e:
            return {"success": False, "agent_id": self.agent_id, "action": "click_first_result", "error": str(e)}

    def play_youtube_video(self, query: Optional[str] = None) -> Dict[str, Any]:
        """Searches or plays active YouTube video and verifies playing state."""
        try:
            def _play(page):
                if query:
                    return YouTubeAdapter.execute_full_search_and_play(page, query)
                else:
                    return YouTubeAdapter.play_video(page)

            res = self.manager.execute_on_page(self.conversation_id, _play, timeout=30.0)
            res["agent_id"] = self.agent_id
            return res
        except Exception as e:
            return {"success": False, "agent_id": self.agent_id, "action": "play_youtube_video", "error": str(e)}
