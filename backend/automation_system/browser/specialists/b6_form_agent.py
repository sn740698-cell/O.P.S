"""
O.P.S. 2.0 Browser Automation Specialist — Agent B6: Browser Input and Form Specialist
Responsibilities:
- Fill form fields, text inputs, textareas, and dropdowns
- Sensitive action approval checking before submission
- Intercept and process file transfers and downloads
- Form validation error detection
"""

import logging
from typing import Dict, Any, Optional
from automation_system.browser.browser_manager import BrowserSessionManager
from automation_system.browser.specialists.b6_transfer_agent import B6_TransferAgent

logger = logging.getLogger("OPS.Browser.B6_FormAgent")


class B6_FormAgent:
    """Specialist Agent B6: Handles web form entry, inputs, and file transfers."""

    def __init__(self, conversation_id: str = "default_session"):
        self.agent_id = "agent_b6_form"
        self.agent_name = "Browser Input and Form Specialist"
        self.conversation_id = conversation_id or "default_session"
        self.manager = BrowserSessionManager()
        self.transfer_specialist = B6_TransferAgent(self.conversation_id)

    def fill_input(self, selector: str, text: str, clear_first: bool = True) -> Dict[str, Any]:
        """Fills input element with specified text."""
        try:
            def _fill(page):
                loc = page.locator(selector).first
                loc.wait_for(state="visible", timeout=10000)
                if clear_first:
                    loc.fill("")
                loc.fill(text)
                return {"success": True, "action": "fill_input", "selector": selector, "value": text}

            res = self.manager.execute_on_page(self.conversation_id, _fill, timeout=15.0)
            res["agent_id"] = self.agent_id
            return res
        except Exception as e:
            return {"success": False, "agent_id": self.agent_id, "action": "fill_input", "selector": selector, "error": str(e)}

    def submit_form(self, selector: str, authorized: bool = False) -> Dict[str, Any]:
        """Submits a form with strict safety authorization gating."""
        if not authorized:
            return {
                "success": False,
                "agent_id": self.agent_id,
                "action": "submit_form",
                "blocked": True,
                "error": "Form submission requires operator approval."
            }

        try:
            def _submit(page):
                loc = page.locator(selector).first
                loc.click()
                return {"success": True, "action": "submit_form", "selector": selector}

            res = self.manager.execute_on_page(self.conversation_id, _submit, timeout=15.0)
            res["agent_id"] = self.agent_id
            return res
        except Exception as e:
            return {"success": False, "agent_id": self.agent_id, "action": "submit_form", "error": str(e)}

    def download_file(self, target_url: str, output_path: str, timeout_ms: int = 30000) -> Dict[str, Any]:
        """Downloads file to output path."""
        return self.transfer_specialist.download_file(target_url, output_path, timeout_ms=timeout_ms)
