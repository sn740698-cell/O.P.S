"""
O.P.S. Tester Agent
Responsible for executing automated test suites, verifying assertion criteria, and reporting test coverage.
Uses: Qwen3 1.7B
Allowed capabilities: terminal.run_tests, terminal.execute, filesystem.read
"""

import json
import logging
from typing import Dict, Any, Optional, List
from ops_core.agents.base import BaseAgent, AgentResult
from ops_core.services.event_bus import OPSEventBus

logger = logging.getLogger("ops.agents.tester")


class TesterAgent(BaseAgent):
    name: str = "Tester"
    description: str = "Runs unit, integration, and end-to-end tests to verify functional requirements."
    assigned_model: str = "Qwen3 1.7B"
    allowed_capabilities: List[str] = [
        "terminal.run_tests",
        "terminal.execute",
        "filesystem.read"
    ]

    async def process(self, directive: str, context: Optional[Dict[str, Any]] = None) -> AgentResult:
        context = context or {}
        session_id = context.get("session_id", "default")
        mission_id = context.get("mission_id")

        await OPSEventBus.emit_thought_async(
            thought=f"Running test verification: {directive}",
            agent=self.name,
            task_id=mission_id
        )

        call_res = await self.executor.execute_capability(
            capability_name="terminal.run_tests",
            arguments={"test_command": directive if directive and "test" in directive.lower() else "pytest -v"},
            requested_by="tester",
            mission_id=mission_id,
            session_id=session_id
        )

        return AgentResult(
            status=call_res.status,
            agent_name=self.name,
            summary="All test suites passed with verified exit code 0." if call_res.status == "SUCCESS" else f"Test failures detected: {call_res.error}",
            evidence={"tool_result": call_res.model_dump()},
            error=call_res.error
        )
