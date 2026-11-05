"""
O.P.S. 2.0 Desktop Automation Specialist — Agent D2: Window Management Agent
Responsibilities:
- Discover open top-level windows on the interactive Windows desktop
- Match window titles via exact, substring, or regex patterns
- Maximize, minimize, restore, resize, and reposition windows
- Bring targeted window to foreground
"""

import sys
import time
import logging
from typing import Dict, Any, List, Optional
from automation_system.desktop.application_controller import ApplicationController, ensure_desktop_access

logger = logging.getLogger("OPS.Desktop.D2_WindowAgent")

if sys.platform == "win32":
    import win32gui
    import win32con
    import win32service


class D2_WindowAgent:
    """Specialist Agent D2: Handles window discovery, state, and geometry."""

    def __init__(self):
        self.agent_id = "agent_d2_window"
        self.agent_name = "Window Management Agent"
        self.controller = ApplicationController()

    def find_window(self, title_query: str) -> Dict[str, Any]:
        """Finds open window matching query string."""
        win_info = self.controller.find_running_window(title_query)
        if win_info:
            return {
                "success": True,
                "agent_id": self.agent_id,
                "action": "find_window",
                "found": True,
                "window": win_info
            }
        return {
            "success": False,
            "agent_id": self.agent_id,
            "action": "find_window",
            "found": False,
            "error": f"No open window matching '{title_query}'"
        }

    def list_open_windows(self, min_title_len: int = 2) -> Dict[str, Any]:
        """Enumerates visible interactive desktop windows."""
        ensure_desktop_access()
        windows = []
        if sys.platform != "win32":
            return {"success": False, "windows": [], "error": "Non-windows platform"}

        def _enum_cb(hwnd, _):
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd).strip()
                if len(title) >= min_title_len:
                    rect = win32gui.GetWindowRect(hwnd)
                    # Ignore zero-size windows
                    if rect[2] - rect[0] > 0 and rect[3] - rect[1] > 0:
                        windows.append({
                            "hwnd": hwnd,
                            "title": title,
                            "rect": rect
                        })
            return True

        try:
            hdesk = win32service.OpenDesktop("default", 0, False, 0x0100)
            if hdesk:
                win32gui.EnumDesktopWindows(int(hdesk), _enum_cb, None)
            else:
                win32gui.EnumWindows(_enum_cb, None)
            return {"success": True, "agent_id": self.agent_id, "windows": windows, "count": len(windows)}
        except Exception as e:
            logger.error(f"Error enumerating windows: {e}")
            return {"success": False, "agent_id": self.agent_id, "error": str(e), "windows": []}

    def focus_window(self, title_query: str) -> Dict[str, Any]:
        """Brings targeted window to foreground."""
        win_res = self.find_window(title_query)
        if not win_res.get("found"):
            return win_res
        hwnd = win_res["window"]["hwnd"]
        ok = self.controller.bring_to_front(hwnd)
        return {
            "success": ok,
            "agent_id": self.agent_id,
            "action": "focus_window",
            "hwnd": hwnd,
            "title": win_res["window"]["title"]
        }

    def set_window_state(self, title_query: str, state: str = "maximize") -> Dict[str, Any]:
        """Changes window state: 'maximize', 'minimize', 'restore'."""
        win_res = self.find_window(title_query)
        if not win_res.get("found"):
            return win_res
        hwnd = win_res["window"]["hwnd"]

        cmd_map = {
            "maximize": win32con.SW_MAXIMIZE,
            "minimize": win32con.SW_MINIMIZE,
            "restore": win32con.SW_RESTORE
        }
        cmd = cmd_map.get(state.lower(), win32con.SW_RESTORE)
        win32gui.ShowWindow(hwnd, cmd)
        time.sleep(0.3)
        return {
            "success": True,
            "agent_id": self.agent_id,
            "action": "set_window_state",
            "state": state,
            "hwnd": hwnd
        }
