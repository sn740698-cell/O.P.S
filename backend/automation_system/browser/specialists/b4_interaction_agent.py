"""
O.P.S. 2.0 Browser Automation Specialist — Agent B4: Web Interaction Agent
Responsibilities:
- Click buttons, links, search results, tabs
- Select dropdown options and radio/checkbox controls
- Scroll page (up, down, to element)
- Send keyboard keys (Enter, Tab, Escape, etc.)
"""

import logging
from typing import Dict, Any, Optional
from automation_system.browser.browser_manager import BrowserSessionManager
from automation_system.browser.interaction_engine import InteractionEngine

logger = logging.getLogger("OPS.Browser.B4_InteractionAgent")


class B4_InteractionAgent:
    """Specialist Agent B4: Executes DOM clicks, selections, scrolling, and keypresses."""

    def __init__(self, conversation_id: str = "default_session"):
        self.agent_id = "agent_b4_interaction"
        self.agent_name = "Web Interaction Agent"
        self.conversation_id = conversation_id or "default_session"
        self.manager = BrowserSessionManager()

    def click(
        self,
        selector: Optional[str] = None,
        name: Optional[str] = None,
        role: Optional[str] = None,
        timeout_ms: int = 10000
    ) -> Dict[str, Any]:
        """Clicks an element using accessible role, text, or CSS selector."""
        try:
            def _click(page):
                return InteractionEngine.click(page, selector=selector, name=name, role=role, timeout_ms=timeout_ms)

            res = self.manager.execute_on_page(self.conversation_id, _click, timeout=timeout_ms / 1000.0 + 5.0)
            res["agent_id"] = self.agent_id
            return res
        except Exception as e:
            return {"success": False, "agent_id": self.agent_id, "action": "click", "error": str(e)}

    def click_first_result(self, timeout_ms: int = 15000) -> Dict[str, Any]:
        """Intelligently clicks the first primary result (e.g. YouTube video or search hit)."""
        try:
            def _first(page):
                return InteractionEngine.click_first_result(page, timeout_ms=timeout_ms)

            res = self.manager.execute_on_page(self.conversation_id, _first, timeout=timeout_ms / 1000.0 + 5.0)
            res["agent_id"] = self.agent_id
            return res
        except Exception as e:
            return {"success": False, "agent_id": self.agent_id, "action": "click_first_result", "error": str(e)}

    def scroll(self, direction: str = "down", amount: int = 500) -> Dict[str, Any]:
        """Scrolls the active page."""
        try:
            def _scroll(page):
                return InteractionEngine.scroll(page, direction=direction, amount=amount)

            res = self.manager.execute_on_page(self.conversation_id, _scroll, timeout=10.0)
            res["agent_id"] = self.agent_id
            return res
        except Exception as e:
            return {"success": False, "agent_id": self.agent_id, "action": "scroll", "error": str(e)}

    def press_key(self, key: str = "Enter") -> Dict[str, Any]:
        """Dispatches a keyboard key to the active page."""
        try:
            def _key(page):
                return InteractionEngine.press_key(page, key=key)

            res = self.manager.execute_on_page(self.conversation_id, _key, timeout=10.0)
            res["agent_id"] = self.agent_id
            return res
        except Exception as e:
            return {"success": False, "agent_id": self.agent_id, "action": "press_key", "error": str(e)}
