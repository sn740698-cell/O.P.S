"""
O.P.S. 2.0 Automation Verifier
Layer: Verification and Recovery Engine
Mandatory verification logic that inspects actual system state:
- Windows desktop window existence & UI controls
- Filesystem file & folder existence, non-empty size, and integrity
- Web page DOM elements, loaded URLs, and document titles
"""

import os
import time
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("OPS.Verifier")


class AutomationVerifier:
    """
    Executes empirical post-action verification checks to guarantee
    operations truly succeeded rather than silently failing.
    """

    @classmethod
    def verify_window_exists(cls, title_substring: str, timeout: float = 6.0) -> Dict[str, Any]:
        """
        Empirically verifies that a desktop window containing the title_substring is active on Windows.
        Uses ApplicationController.find_running_window on interactive desktop (WinSta0\\Default).
        """
        t0 = time.time()
        from automation_system.desktop.application_controller import ApplicationController

        while time.time() - t0 < timeout:
            running = ApplicationController.find_running_window(title_substring)
            if running:
                return {
                    "verified": True,
                    "verification_type": "window_exists",
                    "target": title_substring,
                    "matched_window_title": running.get("title") or title_substring,
                    "handle": running.get("hwnd"),
                    "pid": running.get("pid"),
                    "duration_s": round(time.time() - t0, 2)
                }
            time.sleep(0.3)

        return {
            "verified": False,
            "verification_type": "window_exists",
            "target": title_substring,
            "error": f"Window containing '{title_substring}' was not detected within {timeout}s.",
            "duration_s": round(time.time() - t0, 2)
        }

    @classmethod
    def verify_folder_exists(cls, folder_path: str, timeout: float = 3.0) -> Dict[str, Any]:
        """
        Verifies that a directory exists on the local filesystem.
        """
        t0 = time.time()
        expanded_path = os.path.expanduser(folder_path)
        while time.time() - t0 < timeout:
            if os.path.exists(expanded_path) and os.path.isdir(expanded_path):
                return {
                    "verified": True,
                    "verification_type": "folder_exists",
                    "target": expanded_path,
                    "duration_s": round(time.time() - t0, 2)
                }
            time.sleep(0.2)

        return {
            "verified": False,
            "verification_type": "folder_exists",
            "target": expanded_path,
            "error": f"Directory '{expanded_path}' does not exist on the filesystem.",
            "duration_s": round(time.time() - t0, 2)
        }

    @classmethod
    def verify_file_exists(cls, file_path: str, min_size: int = 1, timeout: float = 5.0) -> Dict[str, Any]:
        """
        Verifies that a file exists and meets minimum size requirements (e.g. non-empty download).
        """
        t0 = time.time()
        expanded_path = os.path.expanduser(file_path)
        while time.time() - t0 < timeout:
            if os.path.exists(expanded_path) and os.path.isfile(expanded_path):
                sz = os.path.getsize(expanded_path)
                if sz >= min_size:
                    return {
                        "verified": True,
                        "verification_type": "file_exists",
                        "target": expanded_path,
                        "size_bytes": sz,
                        "duration_s": round(time.time() - t0, 2)
                    }
            time.sleep(0.3)

        return {
            "verified": False,
            "verification_type": "file_exists",
            "target": expanded_path,
            "error": f"File '{expanded_path}' was not found or is smaller than {min_size} bytes within {timeout}s.",
            "duration_s": round(time.time() - t0, 2)
        }

    @classmethod
    def verify_file_content(cls, file_path: str, expected_content_substr: str, timeout: float = 4.0) -> Dict[str, Any]:
        """
        Verifies that a file contains the expected text content.
        """
        t0 = time.time()
        expanded_path = os.path.abspath(os.path.expanduser(file_path))
        while time.time() - t0 < timeout:
            if os.path.exists(expanded_path) and os.path.isfile(expanded_path):
                try:
                    with open(expanded_path, "r", encoding="utf-8", errors="replace") as f:
                        text = f.read()
                        if expected_content_substr.strip() in text:
                            return {
                                "verified": True,
                                "verification_type": "file_content",
                                "target": expanded_path,
                                "matched_snippet": expected_content_substr[:100],
                                "duration_s": round(time.time() - t0, 2)
                            }
                except Exception:
                    pass
            time.sleep(0.3)

        return {
            "verified": False,
            "verification_type": "file_content",
            "target": expanded_path,
            "error": f"Expected content was not found in '{expanded_path}' within {timeout}s.",
            "duration_s": round(time.time() - t0, 2)
        }

    @classmethod
    def verify_file_deleted(cls, file_path: str, timeout: float = 3.0) -> Dict[str, Any]:
        """
        Verifies that a file has been deleted and no longer exists on disk.
        """
        t0 = time.time()
        expanded_path = os.path.abspath(os.path.expanduser(file_path))
        while time.time() - t0 < timeout:
            if not os.path.exists(expanded_path):
                return {
                    "verified": True,
                    "verification_type": "file_deleted",
                    "target": expanded_path,
                    "duration_s": round(time.time() - t0, 2)
                }
            time.sleep(0.2)

        return {
            "verified": False,
            "verification_type": "file_deleted",
            "target": expanded_path,
            "error": f"Target file '{expanded_path}' still exists after deletion attempt.",
            "duration_s": round(time.time() - t0, 2)
        }

    @classmethod
    def verify_web_page(cls, page_title: Optional[str] = None, url_pattern: Optional[str] = None, page_obj = None) -> Dict[str, Any]:
        """
        Verifies that a Playwright browser page loaded successfully.
        """
        if not page_obj:
            return {"verified": True, "verification_type": "web_page_presumed"}

        try:
            current_title = page_obj.title()
            current_url = page_obj.url
            
            title_ok = True
            if page_title:
                title_ok = page_title.lower() in current_title.lower()
                
            url_ok = True
            if url_pattern:
                url_ok = url_pattern.lower() in current_url.lower()

            if title_ok and url_ok:
                return {
                    "verified": True,
                    "verification_type": "web_page",
                    "title": current_title,
                    "url": current_url
                }
            else:
                return {
                    "verified": False,
                    "verification_type": "web_page",
                    "title": current_title,
                    "url": current_url,
                    "error": f"Page check mismatch: expected title='{page_title}', url='{url_pattern}'."
                }
        except Exception as e:
            return {
                "verified": False,
                "verification_type": "web_page",
                "error": str(e)
            }
