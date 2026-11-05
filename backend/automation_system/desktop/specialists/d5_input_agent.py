"""
O.P.S. 2.0 Desktop Automation Specialist — Agent D5: Keyboard and Input Agent
Responsibilities:
- Type text into focused or targeted desktop windows
- Enforce UIA ValuePattern injection to bypass UIPI privilege isolation
- Dispatch system shortcuts (Ctrl+S, Ctrl+A, Alt+F4, Enter) via Win32 keybd_event
- Clear text and handle special keystrokes
"""

import logging
from typing import Dict, Any, Union, Optional
from automation_system.desktop.gui_controller import GUIController

logger = logging.getLogger("OPS.Desktop.D5_InputAgent")


class D5_InputAgent:
    """Specialist Agent D5: Manages keyboard input, text typing, and shortcut dispatches."""

    def __init__(self, backend: str = "uia"):
        self.agent_id = "agent_d5_input"
        self.agent_name = "Keyboard and Input Agent"
        self.controller = GUIController(default_backend=backend)

    def type_text(
        self,
        title: str,
        text: str,
        control_locator: Optional[Union[str, Dict[str, Any]]] = None,
        replace: bool = False
    ) -> Dict[str, Any]:
        """Types text into window or targeted edit control."""
        try:
            res = self.controller.type_text(title, text=text, control_locator=control_locator, replace=replace)
            res["agent_id"] = self.agent_id
            return res
        except Exception as e:
            logger.error(f"D5_InputAgent typing error: {e}")
            return {"success": False, "agent_id": self.agent_id, "action": "type_text", "error": str(e)}

    def send_keys(self, title: str, keys: str) -> Dict[str, Any]:
        """Dispatches keyboard shortcuts (e.g. '^s' for Ctrl+S, '^a' for Ctrl+A, '%{F4}' for Alt+F4)."""
        try:
            res = self.controller.send_keys(title, keys=keys)
            res["agent_id"] = self.agent_id
            return res
        except Exception as e:
            return {"success": False, "agent_id": self.agent_id, "action": "send_keys", "error": str(e)}
