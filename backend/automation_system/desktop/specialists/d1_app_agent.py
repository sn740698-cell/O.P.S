"""
O.P.S. 2.0 Desktop Automation Specialist — Agent D1: Application Controller Agent
Responsibilities:
- Discover installed desktop applications across system
- Resolve executable paths, canonical aliases, and UWP app package identities
- Launch applications with Windows 11 background suspension prevention
- Activate running instances and bring windows to foreground
- Gracefully close applications handling unsaved changes
"""

import time
import logging
from typing import Dict, Any, Optional
from automation_system.desktop.application_controller import ApplicationController

logger = logging.getLogger("OPS.Desktop.D1_AppAgent")


class D1_AppAgent:
    """Specialist Agent D1: Manages native Windows application resolution, launch, and termination."""

    def __init__(self):
        self.agent_id = "agent_d1_app"
        self.agent_name = "Application Controller Agent"
        self.controller = ApplicationController()

    def resolve_app(self, app_name: str) -> Dict[str, Any]:
        """Resolves binary path or UWP identity for an application name or alias."""
        path = self.controller.resolve_application(app_name)
        return {
            "success": path is not None,
            "agent_id": self.agent_id,
            "action": "resolve_app",
            "app_name": app_name,
            "resolved_path": path
        }

    def launch(self, app_name: str, path: Optional[str] = None, args: Optional[Any] = None, reuse_existing: bool = True, wait_seconds: Optional[float] = None, **kwargs) -> Dict[str, Any]:
        """Launches or focuses application instance."""
        try:
            res = self.controller.launch(app_name, path=path, args=args, reuse_existing=reuse_existing)
            res["agent_id"] = self.agent_id
            if wait_seconds:
                time.sleep(wait_seconds)
            return res
        except Exception as e:
            logger.error(f"D1_AppAgent launch failed for '{app_name}': {e}")
            return {"success": False, "agent_id": self.agent_id, "action": "launch", "error": str(e)}

    def close(self, app_name: str, force: bool = False, timeout: float = 4.0, **kwargs) -> Dict[str, Any]:
        """Gracefully or forcefully closes application."""
        try:
            res = self.controller.close(app_name, force=force, timeout=timeout)
            res["agent_id"] = self.agent_id
            return res
        except Exception as e:
            return {"success": False, "agent_id": self.agent_id, "action": "close", "error": str(e)}

    def bring_to_front(self, hwnd: int) -> Dict[str, Any]:
        """Brings specific window handle to foreground."""
        ok = self.controller.bring_to_front(hwnd)
        return {"success": ok, "agent_id": self.agent_id, "hwnd": hwnd}
