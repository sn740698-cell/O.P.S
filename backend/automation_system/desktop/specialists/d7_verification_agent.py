"""
O.P.S. 2.0 Desktop Automation Specialist — Agent D7: Desktop Verification Agent
Responsibilities:
- Empirically verify application window existence, title, and handles
- Verify file creation, existence, modification timestamp, and non-empty content
- Verify file content matches expected patterns
- Verify application process termination
"""

import logging
from typing import Dict, Any, List, Optional
from automation_system.desktop.verification_engine import VerificationEngine

logger = logging.getLogger("OPS.Desktop.D7_VerificationAgent")


class D7_VerificationAgent:
    """Specialist Agent D7: Empirically verifies desktop windows, files, and process states."""

    def __init__(self):
        self.agent_id = "agent_d7_verification"
        self.agent_name = "Desktop Verification Agent"
        self.verifier = VerificationEngine()

    def verify_window(self, app_name_or_title: str, timeout: float = 5.0) -> Dict[str, Any]:
        """Empirically verifies window is open and visible."""
        res = self.verifier.verify_window_exists(app_name_or_title, timeout=timeout)
        res["agent_id"] = self.agent_id
        res["success"] = res.get("verified", False)
        return res

    def verify_file(self, file_path: str, check_non_empty: bool = True, timeout: float = 4.0, expected_snippet: Optional[str] = None) -> Dict[str, Any]:
        """Empirically verifies file exists on disk with non-zero size, and optionally snippet."""
        min_size = 1 if check_non_empty else 0
        res = self.verifier.verify_file_exists(file_path, min_size=min_size, timeout=timeout)
        if res.get("verified") and expected_snippet:
            return self.verify_file_content(file_path, expected_snippet, max_wait=timeout)
        res["agent_id"] = self.agent_id
        res["success"] = res.get("verified", False)
        return res

    def verify_file_content(self, file_path: str, expected_substrings: Any, max_wait: float = 3.0) -> Dict[str, Any]:
        """Verifies file contains required strings or signatures."""
        if isinstance(expected_substrings, list):
            res = {"verified": True, "path": file_path}
            for sub in expected_substrings:
                r = self.verifier.verify_file_content(file_path, expected_text=str(sub), timeout=max_wait)
                if not r.get("verified"):
                    res = r
                    break
        else:
            res = self.verifier.verify_file_content(file_path, expected_text=str(expected_substrings), timeout=max_wait)
        res["agent_id"] = self.agent_id
        res["success"] = res.get("verified", False)
        return res

    def verify_closed(self, app_name: str, timeout: float = 5.0) -> Dict[str, Any]:
        """Verifies process has terminated and window is closed."""
        res = self.verifier.verify_process_closed(app_name, timeout=timeout)
        res["agent_id"] = self.agent_id
        res["success"] = res.get("verified", False)
        return res
