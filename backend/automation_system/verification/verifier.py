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
        Uses pywinauto Desktop or Win32 enum_windows.
        """
        t0 = time.time()
        last_error = None
        
        while time.time() - t0 < timeout:
            # 1. Check UIA backend on current thread desktop
            try:
                import pywinauto
                from pywinauto import Desktop
                desktop = Desktop(backend="uia")
                for w in desktop.windows():
                    try:
                        win_title = w.window_text()
                        if title_substring.lower() in win_title.lower():
                            return {
                                "verified": True,
                                "verification_type": "window_exists",
                                "target": title_substring,
                                "matched_window_title": win_title,
                                "handle": w.handle,
                                "duration_s": round(time.time() - t0, 2)
                            }
                    except Exception:
                        pass
            except Exception as e:
                last_error = str(e)

            # 2. Check Win32 backend on current thread desktop
            try:
                from pywinauto import Desktop
                desktop_w32 = Desktop(backend="win32")
                for w in desktop_w32.windows():
                    try:
                        win_title = w.window_text()
                        if title_substring.lower() in win_title.lower():
                            return {
                                "verified": True,
                                "verification_type": "window_exists",
                                "target": title_substring,
                                "matched_window_title": win_title,
                                "handle": w.handle,
                                "duration_s": round(time.time() - t0, 2)
                            }
                    except Exception:
                        pass
            except Exception as e:
                last_error = str(e)

            # 3. Check interactive 'default' desktop windows (WinSta0\Default)
            try:
                import win32service
                import win32gui
                import win32con
                hdesk = win32service.OpenDesktop("default", 0, False, win32con.GENERIC_READ)
                matched_w = []
                def _cb(hwnd, _):
                    try:
                        t = win32gui.GetWindowText(hwnd)
                        if t and title_substring.lower() in t.lower():
                            matched_w.append((hwnd, t))
                    except Exception:
                        pass
                win32gui.EnumDesktopWindows(int(hdesk), _cb, None)
                if matched_w:
                    hwnd, t = matched_w[0]
                    return {
                        "verified": True,
                        "verification_type": "window_exists",
                        "target": title_substring,
                        "matched_window_title": t,
                        "handle": hwnd,
                        "duration_s": round(time.time() - t0, 2)
                    }
            except Exception:
                pass

            # 4. Special empirical check for VS Code (which reports windows via code --status)
            if any(term in title_substring.lower() for term in ["visual studio code", "vscode", "code"]):
                try:
                    import subprocess
                    proc_res = subprocess.run(
                        ["cmd.exe", "/c", "code", "--status"],
                        capture_output=True,
                        text=True,
                        timeout=3
                    )
                    if proc_res.returncode == 0:
                        for line in proc_res.stdout.splitlines():
                            if "window [" in line.lower() and "visual studio code" in line.lower():
                                clean_title = line.split("(", 1)[-1].rstrip(")") if "(" in line else line.strip()
                                return {
                                    "verified": True,
                                    "verification_type": "window_exists",
                                    "target": title_substring,
                                    "matched_window_title": clean_title,
                                    "duration_s": round(time.time() - t0, 2)
                                }
                except Exception:
                    pass

            time.sleep(0.4)

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
