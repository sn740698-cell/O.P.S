"""
O.P.S. Automation Agent
Responsible for desktop OS automation, application launching, and local workflow orchestration.
Uses: Qwen3 1.7B
Allowed capabilities: desktop.launch_app, desktop.open_file
"""

import logging
from typing import Dict, Any, Optional, List
from ops_core.agents.base import BaseAgent, AgentResult
from ops_core.services.event_bus import OPSEventBus

logger = logging.getLogger("ops.agents.automation")


class AutomationAgent(BaseAgent):
    name: str = "Automation"
    description: str = "Automates desktop applications, OS workflows, and GUI actions."
    assigned_model: str = "Qwen3 1.7B"
    allowed_capabilities: List[str] = [
        "desktop.launch_app",
        "desktop.open_file"
    ]

    async def process(self, directive: str, context: Optional[Dict[str, Any]] = None) -> AgentResult:
        context = context or {}
        session_id = context.get("session_id", "default")
        mission_id = context.get("mission_id")

        await OPSEventBus.emit_thought_async(
            thought=f"Triggering desktop automation: {directive}",
            agent=self.name,
            task_id=mission_id
        )

        app_name = context.get("app_name", directive.replace("open", "").replace("launch", "").strip())
        call_res = await self.executor.execute_capability(
            capability_name="desktop.launch_app",
            arguments={"app_name": app_name},
            requested_by="automation",
            mission_id=mission_id,
            session_id=session_id
        )

        return AgentResult(
            status=call_res.status,
            agent_name=self.name,
            summary=f"Successfully launched {app_name}" if call_res.status == "SUCCESS" else f"Failed to launch {app_name}: {call_res.error}",
            evidence={"tool_result": call_res.model_dump()},
            error=call_res.error
        )
