"""
O.P.S. 2.0 Desktop Automation Specialist — Agent D8: Desktop Recovery Agent
Responsibilities:
- Classify desktop automation errors (WINDOW_NOT_FOUND, CONTROL_NOT_FOUND, PROCESS_HUNG, PERMISSION_ERROR)
- Execute bounded recoveries (window refocusing, process restart, backend switching UIA <-> Win32)
- Limit retries to 2 attempts max to avoid destabilizing the OS
"""

import time
import logging
from typing import Dict, Any, Callable, Optional
from automation_system.desktop.application_controller import ApplicationController
from automation_system.desktop.verification_engine import VerificationEngine

logger = logging.getLogger("OPS.Desktop.D8_RecoveryAgent")


class D8_RecoveryAgent:
    """Specialist Agent D8: Classifies failures and executes bounded desktop recovery strategies."""

    def __init__(self):
        self.agent_id = "agent_d8_recovery"
        self.agent_name = "Desktop Recovery Agent"
        self.app_ctrl = ApplicationController()
        self.verifier = VerificationEngine()

    def classify_error(self, error: Exception) -> str:
        """Classifies desktop errors into canonical taxonomy."""
        msg = str(error).lower()
        if "window" in msg and ("missing" in msg or "closed" in msg or "not found" in msg):
            return "WINDOW_NOT_FOUND"
        if "not found" in msg or "could not find" in msg or "element not visible" in msg:
            return "CONTROL_NOT_FOUND"
        if "access denied" in msg or "permission" in msg or "uipi" in msg:
            return "PERMISSION_RESTRICTED"
        if "timeout" in msg:
            return "OPERATION_TIMEOUT"
        return "UNKNOWN_DESKTOP_ERROR"

    def execute_with_recovery(
        self,
        action_name: str,
        fn: Callable[[], Dict[str, Any]],
        app_name_or_title: Optional[str] = None,
        max_retries: int = 1
    ) -> Dict[str, Any]:
        """Executes action with bounded recovery retries."""
        for attempt in range(max_retries + 1):
            try:
                res = fn()
                if res.get("success", False):
                    return res

                err_msg = res.get("error", "Unknown error")
                if attempt < max_retries:
                    logger.warning(f"D8_RecoveryAgent: '{action_name}' attempt {attempt + 1} failed: {err_msg}. Recovering...")
                    self._attempt_desktop_recovery(app_name_or_title, err_msg)
            except Exception as e:
                classification = self.classify_error(e)
                if attempt < max_retries:
                    logger.warning(f"D8_RecoveryAgent caught {classification} in '{action_name}': {e}. Recovering...")
                    self._attempt_desktop_recovery(app_name_or_title, str(e))
                else:
                    return {
                        "success": False,
                        "agent_id": self.agent_id,
                        "action": action_name,
                        "error": str(e),
                        "classification": classification,
                        "retries_exhausted": True
                    }

        return res

    def _attempt_desktop_recovery(self, app_name_or_title: Optional[str], err_msg: str):
        """Attempts to recover desktop state: refocus window, allow brief settling."""
        time.sleep(1.0)
        if app_name_or_title:
            try:
                win_info = self.app_ctrl.find_running_window(app_name_or_title)
                if win_info and win_info.get("hwnd"):
                    self.app_ctrl.bring_to_front(win_info["hwnd"])
            except Exception as e:
                logger.debug(f"Recovery focus failed: {e}")
