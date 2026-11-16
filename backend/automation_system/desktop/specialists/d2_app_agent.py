"""
O.P.S. 2.0 Desktop Automation Specialist — Agent D2: Application Launch and Lifecycle Specialist
Responsibilities:
- Launch desktop applications via binary executable, shortcut, or URI scheme
- Handle Windows 11 AppContainer (UWP) apps
- Wait for application readiness and handle startup delays
- Safely close requested applications with process tree cleanup
- Verify application process and window states
"""

import os
import time
import logging
from typing import Dict, Any, Optional

from automation_system.desktop.application_controller import ApplicationController

logger = logging.getLogger("OPS.Desktop.D2_AppAgent")


class D2_AppAgent:
    """Specialist Agent D2: Application Launch and Lifecycle Specialist."""

    def __init__(self):
        self.agent_id = "agent_d2_app"
        self.agent_name = "Application Launch & Lifecycle Specialist"
        self.controller = ApplicationController()

    def launch(
        self,
        app_name: str,
        path: Optional[str] = None,
        args: Optional[Any] = None,
        reuse_existing: bool = True,
        wait_seconds: Optional[float] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Launches application and waits for readiness."""
        try:
            # Check if path is a URI scheme (e.g. spotify:, whatsapp:, calculator:)
            if path and path.endswith(":") and " " not in path and not os.path.exists(path):
                import subprocess
                subprocess.Popen(f"start {path}", shell=True)
                time.sleep(1.5)
                return {
                    "success": True,
                    "agent_id": self.agent_id,
                    "action": "launch",
                    "app_name": app_name,
                    "launch_type": "uri_scheme",
                    "target": path
                }

            res = self.controller.launch(app_name, path=path, args=args, reuse_existing=reuse_existing)
            res["agent_id"] = self.agent_id
            if wait_seconds:
                time.sleep(wait_seconds)
            return res
        except Exception as e:
            logger.error(f"D2_AppAgent launch failed for '{app_name}': {e}")
            return {"success": False, "agent_id": self.agent_id, "action": "launch", "error": str(e)}

    def close(self, app_name: str, force: bool = False, timeout: float = 4.0, **kwargs) -> Dict[str, Any]:
        """Closes application and ensures process termination."""
        try:
            res = self.controller.close(app_name, force=force, timeout=timeout)
            res["agent_id"] = self.agent_id
            return res
        except Exception as e:
            return {"success": False, "agent_id": self.agent_id, "action": "close", "error": str(e)}
