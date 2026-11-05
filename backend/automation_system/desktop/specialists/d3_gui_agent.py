"""
O.P.S. 2.0 Desktop Automation Specialist — Agent D3: GUI Interaction Agent
Responsibilities:
- Attach to application window via Pywinauto UIA / Win32 backend
- Inspect control trees and accessibility properties
- Click buttons, menus, and interactive controls
- Read text and states from UI controls
- Handle standard system dialogs (Open, Save As, Alert)
"""

import logging
from typing import Dict, Any, Union, Optional
from automation_system.desktop.gui_controller import GUIController

logger = logging.getLogger("OPS.Desktop.D3_GUIAgent")


class D3_GUIAgent:
    """Specialist Agent D3: Manages GUI elements, button actuation, and control inspection."""

    def __init__(self, backend: str = "uia"):
        self.agent_id = "agent_d3_gui"
        self.agent_name = "GUI Interaction Agent"
        self.controller = GUIController(default_backend=backend)

    def inspect_controls(self, title: str, max_elements: int = 40) -> Dict[str, Any]:
        """Inspects accessible controls in window."""
        res = self.controller.inspect_controls(title, max_elements=max_elements)
        res["agent_id"] = self.agent_id
        if "controls" not in res:
            res["controls"] = []
        return res

    def click_button(self, title: str, button_locator: Union[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Clicks button by name or locator specification."""
        try:
            res = self.controller.click_button(title, button_locator)
            res["agent_id"] = self.agent_id
            return res
        except Exception as e:
            logger.error(f"D3_GUIAgent click error: {e}")
            return {"success": False, "agent_id": self.agent_id, "action": "click_button", "error": str(e)}

    def read_control(self, title: str, locator: Optional[Union[str, Dict[str, Any]]] = None) -> Dict[str, Any]:
        """Reads text from window or specific control."""
        try:
            res = self.controller.read_control_text(title, control_locator=locator)
            res["agent_id"] = self.agent_id
            return res
        except Exception as e:
            return {"success": False, "agent_id": self.agent_id, "action": "read_control", "error": str(e)}
