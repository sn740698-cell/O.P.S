"""
O.P.S. 2.0 Desktop Automation Engine — Module 5: Verification and Recovery Engine
Empirically verifies post-execution states: window visibility, file existence, content matches, and process closure.
Orchestrates bounded retries (max 3) with intelligent recovery actions and honest status reporting.
"""

import os
import time
import logging
from typing import Dict, Any, List, Optional, Callable
from automation_system.desktop.application_controller import ApplicationController, ensure_desktop_access

logger = logging.getLogger("OPS.Desktop.VerificationEngine")

# Standard Execution Statuses
STATUS_PENDING = "PENDING"
STATUS_EXECUTING = "EXECUTING"
STATUS_VERIFYING = "VERIFYING"
STATUS_COMPLETED = "COMPLETED"
STATUS_FAILED = "FAILED"
STATUS_CANCELLED = "CANCELLED_BY_USER"
STATUS_CLARIFICATION = "REQUIRES_CLARIFICATION"


class VerificationEngine:
    """
    Empirical state verification and bounded recovery controller.
    """

    @classmethod
    def verify_window_exists(
        cls,
        window_title: str,
        timeout: float = 5.0,
        poll_interval: float = 0.5
    ) -> Dict[str, Any]:
        """
        Polls until target window is detected and visible on the interactive desktop.
        """
        ensure_desktop_access()
        t_end = time.time() + timeout
        attempts = 0

        while time.time() < t_end:
            attempts += 1
            win_info = ApplicationController.find_running_window(window_title)
            if win_info and (win_info.get("hwnd") or win_info.get("pid")):
                return {
                    "verified": True,
                    "target": window_title,
                    "matched_title": win_info.get("title"),
                    "handle": win_info.get("hwnd"),
                    "pid": win_info.get("pid"),
                    "attempts": attempts,
                    "elapsed_s": round(timeout - (t_end - time.time()), 2)
                }
            time.sleep(poll_interval)

        return {
            "verified": False,
            "target": window_title,
            "error": f"Window matching '{window_title}' did not appear within {timeout}s.",
            "attempts": attempts
        }

    @classmethod
    def verify_file_exists(
        cls,
        path: str,
        min_size: int = 0,
        timeout: float = 4.0,
        poll_interval: float = 0.4
    ) -> Dict[str, Any]:
        """
        Polls until the targeted file exists on disk and meets the minimum size requirement.
        """
        target = os.path.abspath(os.path.expanduser(path))
        t_end = time.time() + timeout
        attempts = 0

        while time.time() < t_end:
            attempts += 1
            if os.path.exists(target) and os.path.isfile(target):
                size = os.path.getsize(target)
                if size >= min_size:
                    return {
                        "verified": True,
                        "path": target,
                        "size_bytes": size,
                        "attempts": attempts,
                        "elapsed_s": round(timeout - (t_end - time.time()), 2)
                    }
            time.sleep(poll_interval)

        return {
            "verified": False,
            "path": target,
            "error": f"File '{target}' was not found or size < {min_size} bytes after {timeout}s.",
            "attempts": attempts
        }

    @classmethod
    def verify_file_content(
        cls,
        path: str,
        expected_text: str,
        timeout: float = 3.0,
        poll_interval: float = 0.5
    ) -> Dict[str, Any]:
        """
        Verifies that the target file contains the expected substring or snippet.
        """
        target = os.path.abspath(os.path.expanduser(path))
        t_end = time.time() + timeout
        attempts = 0

        while time.time() < t_end:
            attempts += 1
            if os.path.exists(target) and os.path.isfile(target):
                try:
                    with open(target, "r", encoding="utf-8", errors="replace") as f:
                        content = f.read()
                    if expected_text in content:
                        return {
                            "verified": True,
                            "path": target,
                            "contains_expected": True,
                            "snippet_preview": expected_text[:100],
                            "attempts": attempts
                        }
                except Exception:
                    pass
            time.sleep(poll_interval)

        return {
            "verified": False,
            "path": target,
            "contains_expected": False,
            "error": f"File '{target}' does not contain expected text after {timeout}s.",
            "attempts": attempts
        }

    @classmethod
    def verify_process_closed(
        cls,
        app_name_or_title: str,
        timeout: float = 4.0,
        poll_interval: float = 0.5
    ) -> Dict[str, Any]:
        """
        Verifies that an application window or process is completely closed.
        """
        ensure_desktop_access()
        t_end = time.time() + timeout
        attempts = 0

        while time.time() < t_end:
            attempts += 1
            win_info = ApplicationController.find_running_window(app_name_or_title)
            if not win_info:
                return {
                    "verified": True,
                    "target": app_name_or_title,
                    "closed": True,
                    "attempts": attempts,
                    "elapsed_s": round(timeout - (t_end - time.time()), 2)
                }
            time.sleep(poll_interval)

        return {
            "verified": False,
            "target": app_name_or_title,
            "closed": False,
            "error": f"Application or window '{app_name_or_title}' is still running after {timeout}s.",
            "attempts": attempts
        }

    @classmethod
    def execute_with_recovery(
        cls,
        action_fn: Callable[[], Dict[str, Any]],
        verification_fn: Optional[Callable[[], Dict[str, Any]]] = None,
        max_retries: int = 3,
        recovery_fn: Optional[Callable[[int, str], None]] = None
    ) -> Dict[str, Any]:
        """
        Executes an automation function with bounded retries and recovery hooks.
        """
        last_result = {}
        for attempt in range(1, max_retries + 1):
            try:
                res = action_fn()
                if not res.get("success", False):
                    err_msg = res.get("error", "Action failed.")
                    if attempt < max_retries and recovery_fn:
                        recovery_fn(attempt, err_msg)
                    time.sleep(0.5 * attempt)
                    last_result = res
                    continue

                # If verification function provided, perform empirical check
                if verification_fn:
                    verif = verification_fn()
                    res["verification"] = verif
                    if not verif.get("verified", False):
                        err_msg = verif.get("error", "Verification failed.")
                        if attempt < max_retries and recovery_fn:
                            recovery_fn(attempt, err_msg)
                        time.sleep(0.5 * attempt)
                        last_result = res
                        continue

                res["attempt"] = attempt
                res["status"] = STATUS_COMPLETED
                return res

            except Exception as e:
                err_msg = str(e)
                if attempt < max_retries and recovery_fn:
                    recovery_fn(attempt, err_msg)
                time.sleep(0.5 * attempt)
                last_result = {"success": False, "error": err_msg, "attempt": attempt}

        last_result["status"] = STATUS_FAILED
        return last_result
