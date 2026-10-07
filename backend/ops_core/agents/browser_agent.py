"""
O.P.S. Browser Agent
Responsible for browser-based automation, DOM inspection, navigation, and web interaction using Playwright.
Uses: Qwen3 1.7B
Allowed capabilities: browser.open, browser.navigate, browser.click, browser.type, browser.extract
"""

import json
import logging
from typing import Dict, Any, Optional, List
from ops_core.agents.base import BaseAgent, AgentResult
from ops_core.services.event_bus import OPSEventBus

logger = logging.getLogger("ops.agents.browser")


class BrowserAgent(BaseAgent):
    name: str = "Browser"
    description: str = "Automates web browsers, DOM interactions, form fills, and web workflows."
    assigned_model: str = "Qwen3 1.7B"
    allowed_capabilities: List[str] = [
        "browser.open",
        "browser.navigate",
        "browser.click",
        "browser.type",
        "browser.extract"
    ]

    async def process(self, directive: str, context: Optional[Dict[str, Any]] = None) -> AgentResult:
        context = context or {}
        session_id = context.get("session_id", "default")
        mission_id = context.get("mission_id")

        await OPSEventBus.emit_thought_async(
            thought=f"Executing browser workflow: {directive}",
            agent=self.name,
            task_id=mission_id
        )

        url = context.get("url", "https://google.com")
        if directive.startswith("http://") or directive.startswith("https://"):
            url = directive

        call_res = await self.executor.execute_capability(
            capability_name="browser.open",
            arguments={"url": url, "headless": False},
            requested_by="browser",
            mission_id=mission_id,
            session_id=session_id
        )

        return AgentResult(
            status=call_res.status,
            agent_name=self.name,
            summary=f"Browser navigated to {url}" if call_res.status == "SUCCESS" else f"Browser action failed: {call_res.error}",
            evidence={"tool_result": call_res.model_dump()},
            error=call_res.error
        )
