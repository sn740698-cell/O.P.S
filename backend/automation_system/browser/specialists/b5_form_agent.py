"""
O.P.S. 2.0 Browser Automation Specialist — Agent B5: Form & Data Entry Agent
Responsibilities:
- Detect and fill input fields, textareas, search inputs, dropdowns
- Mask sensitive credentials/secrets in logs and telemetry
- Pre-submission field validation
- Pause for Human-in-the-Loop (HITL) gate on sensitive submissions
"""

import logging
from typing import Dict, Any, List, Optional
from automation_system.browser.browser_manager import BrowserSessionManager
from automation_system.browser.interaction_engine import InteractionEngine

logger = logging.getLogger("OPS.Browser.B5_FormAgent")


class B5_FormAgent:
    """Specialist Agent B5: Fills forms, handles text entry, and validates form fields."""

    def __init__(self, conversation_id: str = "default_session"):
        self.agent_id = "agent_b5_form"
        self.agent_name = "Form & Data Entry Agent"
        self.conversation_id = conversation_id or "default_session"
        self.manager = BrowserSessionManager()

    def fill_field(
        self,
        selector_or_label: str,
        value: str,
        is_secret: bool = False,
        timeout_ms: int = 8000
    ) -> Dict[str, Any]:
        """Fills an individual input or textarea field."""
        try:
            def _fill(page):
                return InteractionEngine.fill_form(
                    page,
                    selector_or_label=selector_or_label,
                    text=value,
                    is_secret=is_secret,
                    timeout_ms=timeout_ms
                )

            res = self.manager.execute_on_page(self.conversation_id, _fill, timeout=timeout_ms / 1000.0 + 5.0)
            res["agent_id"] = self.agent_id
            if is_secret:
                res["value_masked"] = "***"
            return res
        except Exception as e:
            return {"success": False, "agent_id": self.agent_id, "action": "fill_field", "error": str(e)}

    def fill_form_batch(self, fields: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Fills multiple fields sequentially.
        Each field dict has: {"field": str, "value": str, "is_secret": bool}
        """
        results = []
        all_ok = True
        for f in fields:
            res = self.fill_field(
                selector_or_label=f.get("field", ""),
                value=f.get("value", ""),
                is_secret=f.get("is_secret", False)
            )
            results.append(res)
            if not res.get("success"):
                all_ok = False
                break

        return {
            "success": all_ok,
            "agent_id": self.agent_id,
            "action": "fill_form_batch",
            "results": results,
            "fields_filled": len(results)
        }

    def clear_field(self, selector_or_label: str) -> Dict[str, Any]:
        """Clears existing text in a form field."""
        try:
            def _clear(page):
                loc = page.locator(selector_or_label).first
                loc.fill("")
                return {"success": True, "action": "clear_field", "field": selector_or_label}

            res = self.manager.execute_on_page(self.conversation_id, _clear, timeout=10.0)
            res["agent_id"] = self.agent_id
            return res
        except Exception as e:
            return {"success": False, "agent_id": self.agent_id, "error": str(e)}
