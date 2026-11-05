"""
O.P.S. 2.0 Browser Automation Specialist — Agent B8: Browser Recovery Agent
Responsibilities:
- Classify browser errors (TIMEOUT, TARGET_CLOSED, ELEMENT_NOT_FOUND, NETWORK_ERROR)
- Execute bounded recoveries (reload, tab reopen, session re-init)
- Limit retries to 2 attempts max to prevent runaway loops
"""

import time
import logging
from typing import Dict, Any, Callable, Optional
from automation_system.browser.browser_manager import BrowserSessionManager
from automation_system.browser.recovery_manager import RecoveryManager

logger = logging.getLogger("OPS.Browser.B8_RecoveryAgent")


class B8_RecoveryAgent:
    """Specialist Agent B8: Recovers from browser errors, timeouts, and stale contexts."""

    def __init__(self, conversation_id: str = "default_session"):
        self.agent_id = "agent_b8_recovery"
        self.agent_name = "Browser Recovery Agent"
        self.conversation_id = conversation_id or "default_session"
        self.manager = BrowserSessionManager()

    def classify(self, error: Exception) -> str:
        """Classifies error using RecoveryManager taxonomy."""
        return RecoveryManager.classify_error(error)

    def execute_with_recovery(
        self,
        action_name: str,
        fn: Callable[[], Dict[str, Any]],
        max_retries: int = 1
    ) -> Dict[str, Any]:
        """Executes action with bounded retries and recovery intervention."""
        for attempt in range(max_retries + 1):
            try:
                res = fn()
                if res.get("success", False):
                    return res
                
                # Check error
                err = res.get("error", "Unknown error")
                if attempt < max_retries:
                    logger.warning(f"B8_RecoveryAgent: '{action_name}' attempt {attempt + 1} failed: {err}. Attempting recovery...")
                    self._attempt_page_recovery(err)
            except Exception as e:
                category = self.classify(e)
                if attempt < max_retries:
                    logger.warning(f"B8_RecoveryAgent caught {category} on '{action_name}': {e}. Recovering...")
                    self._attempt_page_recovery(str(e))
                else:
                    return {
                        "success": False,
                        "agent_id": self.agent_id,
                        "action": action_name,
                        "error": str(e),
                        "classification": category,
                        "retries_exhausted": True
                    }

        return res

    def _attempt_page_recovery(self, error_msg: str):
        """Internal recovery routine based on error message."""
        msg = str(error_msg).lower()
        if "target closed" in msg or "disconnected" in msg:
            self.manager.close_session(self.conversation_id)
            self.manager.get_or_create_page(self.conversation_id)
            time.sleep(1.0)
        elif "timeout" in msg:
            try:
                def _reload(page):
                    page.reload(wait_until="domcontentloaded", timeout=10000)
                self.manager.execute_on_page(self.conversation_id, _reload, timeout=15.0)
            except Exception:
                pass
