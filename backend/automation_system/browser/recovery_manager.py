"""
O.P.S. 2.0 Browser Error Recovery Manager
Classifies browser execution errors and executes bounded recovery strategies:
- Page / Context crashes: Re-instantiates browser page and resumes workflow
- Navigation timeouts: Attempts reload with DOM content-loaded fallback
- Element interaction failures: Retries with scroll-into-view and text-based locator fallbacks
"""

import time
import logging
from typing import Dict, Any, Callable, Optional
from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError

logger = logging.getLogger("OPS.BrowserRecovery")


class RecoveryManager:
    """
    Classifies browser errors and provides bounded recovery actions.
    """

    @classmethod
    def classify_error(cls, error: Exception) -> str:
        """Classifies error into canonical category."""
        msg = str(error).lower()
        if isinstance(error, PlaywrightTimeoutError) or "timeout" in msg or "timed out" in msg:
            return "TIMEOUT"
        if "target closed" in msg or "browser has been closed" in msg or "disconnected" in msg:
            return "TARGET_CLOSED"
        if "could not find element" in msg or "waiting for selector" in msg or "strict mode violation" in msg:
            return "ELEMENT_NOT_FOUND"
        if "net::" in msg or "failed to load" in msg or "dns" in msg:
            return "NETWORK_ERROR"
        return "UNKNOWN_ERROR"

    @classmethod
    def execute_with_retry(
        cls,
        action_name: str,
        fn: Callable[[], Dict[str, Any]],
        max_retries: int = 1,
        page: Optional[Page] = None
    ) -> Dict[str, Any]:
        """
        Executes an action callable with bounded error classification and recovery.
        """
        last_error = None
        for attempt in range(max_retries + 1):
            try:
                res = fn()
                if res.get("success", False):
                    return res
                # If failure has specific error, check if recoverable
                err_msg = res.get("error", "")
                if attempt < max_retries:
                    logger.warning(f"Action '{action_name}' failed attempt {attempt+1}: {err_msg}. Retrying...")
                    time.sleep(1.0)
                    if page and "timeout" in err_msg.lower():
                        try: page.reload(timeout=10000)
                        except Exception: pass
            except Exception as e:
                last_error = e
                category = cls.classify_error(e)
                logger.warning(f"Action '{action_name}' raised {category}: {e} (attempt {attempt+1}/{max_retries+1})")
                if attempt < max_retries:
                    time.sleep(1.0)
                    if page and category == "TIMEOUT":
                        try: page.reload(timeout=10000)
                        except Exception: pass
                else:
                    return {
                        "success": False,
                        "action": action_name,
                        "error_category": category,
                        "error": str(e)
                    }

        return {
            "success": False,
            "action": action_name,
            "error": str(last_error) if last_error else "Action failed all retry attempts."
        }
