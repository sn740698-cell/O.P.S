"""
O.P.S. 2.0 Browser Automation Specialist — Agent B3: Navigation Agent
Responsibilities:
- Navigate to URLs with protocol normalization
- History traversal (back, forward, reload)
- Waiting for load states (domcontentloaded, networkidle)
- Cookie / consent / modal overlay dismissal
"""

import logging
from typing import Dict, Any, Optional
from automation_system.browser.browser_manager import BrowserSessionManager
from automation_system.browser.navigation_engine import NavigationEngine

logger = logging.getLogger("OPS.Browser.B3_NavigationAgent")


class B3_NavigationAgent:
    """Specialist Agent B3: Handles web page navigation, history, and reload."""

    def __init__(self, conversation_id: str = "default_session"):
        self.agent_id = "agent_b3_navigation"
        self.agent_name = "Navigation Agent"
        self.conversation_id = conversation_id or "default_session"
        self.manager = BrowserSessionManager()

    def navigate(self, url: str, wait_until: str = "domcontentloaded", timeout_ms: int = 25000) -> Dict[str, Any]:
        """Navigates to URL safely on the worker thread."""
        try:
            def _nav(page):
                return NavigationEngine.navigate(page, url, wait_until=wait_until, timeout_ms=timeout_ms)

            res = self.manager.execute_on_page(self.conversation_id, _nav, timeout=timeout_ms / 1000.0 + 5.0)
            res["agent_id"] = self.agent_id
            return res
        except Exception as e:
            logger.error(f"B3_NavigationAgent error navigating to {url}: {e}")
            return {"success": False, "agent_id": self.agent_id, "action": "navigate", "url": url, "error": str(e)}

    def go_back(self, timeout_ms: int = 15000) -> Dict[str, Any]:
        """Navigates back in browser history."""
        try:
            def _back(page):
                return NavigationEngine.go_back(page, timeout_ms=timeout_ms)

            res = self.manager.execute_on_page(self.conversation_id, _back, timeout=timeout_ms / 1000.0 + 5.0)
            res["agent_id"] = self.agent_id
            return res
        except Exception as e:
            return {"success": False, "agent_id": self.agent_id, "action": "go_back", "error": str(e)}

    def go_forward(self, timeout_ms: int = 15000) -> Dict[str, Any]:
        """Navigates forward in browser history."""
        try:
            def _forward(page):
                return NavigationEngine.go_forward(page, timeout_ms=timeout_ms)

            res = self.manager.execute_on_page(self.conversation_id, _forward, timeout=timeout_ms / 1000.0 + 5.0)
            res["agent_id"] = self.agent_id
            return res
        except Exception as e:
            return {"success": False, "agent_id": self.agent_id, "action": "go_forward", "error": str(e)}

    def reload(self, timeout_ms: int = 15000) -> Dict[str, Any]:
        """Reloads the current page."""
        try:
            def _reload(page):
                return NavigationEngine.reload(page, timeout_ms=timeout_ms)

            res = self.manager.execute_on_page(self.conversation_id, _reload, timeout=timeout_ms / 1000.0 + 5.0)
            res["agent_id"] = self.agent_id
            return res
        except Exception as e:
            return {"success": False, "agent_id": self.agent_id, "action": "reload", "error": str(e)}
