"""
O.P.S. 2.0 Browser Automation Specialist — Agent B1: Browser Lifecycle Agent
Responsibilities:
- Launch browser and maintain persistent Chromium context via BrowserSessionManager
- Connect to existing browser instance
- Monitor browser health, process state, and handle crashes
- Enforce O.P.S. browser lifecycle and cleanup policy
"""

import time
import logging
from typing import Dict, Any, Optional
from automation_system.browser.browser_manager import BrowserSessionManager

logger = logging.getLogger("OPS.Browser.B1_LifecycleAgent")


class B1_LifecycleAgent:
    """Specialist Agent B1: Manages Playwright browser instance lifecycle and health."""

    def __init__(self, conversation_id: str = "default_session"):
        self.agent_id = "agent_b1_lifecycle"
        self.agent_name = "Browser Lifecycle Agent"
        self.conversation_id = conversation_id or "default_session"
        self.manager = BrowserSessionManager()

    def ensure_browser_ready(self, headless: Optional[bool] = None) -> Dict[str, Any]:
        """Ensures that the browser is running and connected."""
        t0 = time.time()
        try:
            proxy = self.manager.get_or_create_page(self.conversation_id, headless=headless)
            _ = proxy.url  # Trigger page initialization
            is_active = self.manager.get_active_page(self.conversation_id) is not None
            duration = round(time.time() - t0, 2)
            return {
                "success": is_active,
                "agent_id": self.agent_id,
                "action": "ensure_browser_ready",
                "session_active": is_active,
                "browser_type": "chromium",
                "duration_s": duration
            }
        except Exception as e:
            logger.error(f"LifecycleAgent failed to ensure browser ready: {e}")
            return {
                "success": False,
                "agent_id": self.agent_id,
                "action": "ensure_browser_ready",
                "error": str(e)
            }

    def get_session_status(self) -> Dict[str, Any]:
        """Returns live telemetry about the current browser session."""
        is_active = self.manager.get_active_page(self.conversation_id) is not None
        worker = getattr(self.manager._browser_manager, "_worker", None)
        return {
            "success": True,
            "agent_id": self.agent_id,
            "session_active": is_active,
            "has_worker": bool(worker and worker._thread.is_alive())
        }

    def restart_session(self) -> Dict[str, Any]:
        """Recovers from browser crash by closing and restarting clean session."""
        try:
            self.manager.close_session(self.conversation_id)
            time.sleep(0.5)
            return self.ensure_browser_ready()
        except Exception as e:
            return {"success": False, "agent_id": self.agent_id, "error": str(e)}

    def close_browser(self) -> Dict[str, Any]:
        """Gracefully closes browser session per lifecycle policy."""
        try:
            self.manager.close_session(self.conversation_id)
            return {"success": True, "agent_id": self.agent_id, "action": "close_browser"}
        except Exception as e:
            return {"success": False, "agent_id": self.agent_id, "error": str(e)}
