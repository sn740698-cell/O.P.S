"""
O.P.S. Debugger Agent
Responsible for failure analysis, stack trace diagnosis, automated root-cause detection, and patch generation.
Uses: Qwen3 1.7B
Allowed capabilities: terminal.execute, filesystem.read, filesystem.write
"""

import json
import logging
from typing import Dict, Any, Optional, List
from ops_core.agents.base import BaseAgent, AgentResult
from ops_core.services.event_bus import OPSEventBus

logger = logging.getLogger("ops.agents.debugger")


class DebuggerAgent(BaseAgent):
    name: str = "Debugger"
    description: str = "Analyzes execution failures, inspects stack traces, and formulates patches."
    assigned_model: str = "Qwen3 1.7B"
    allowed_capabilities: List[str] = [
        "terminal.execute",
        "filesystem.read",
        "filesystem.write"
    ]

    async def process(self, directive: str, context: Optional[Dict[str, Any]] = None) -> AgentResult:
        context = context or {}
        session_id = context.get("session_id", "default")
        mission_id = context.get("mission_id")
        failure_reason = context.get("failure_reason", "Unknown failure")

        await OPSEventBus.emit_thought_async(
            thought=f"Diagnosing failure: {failure_reason}",
            agent=self.name,
            task_id=mission_id
        )

        prompt = (
            "You are the O.P.S. Debugger Agent.\n"
            "Analyze the failure reason and formulate a remediation capability call.\n"
            "Allowed capabilities: terminal.execute, filesystem.read, filesystem.write.\n"
            "Respond in structured JSON format:\n"
            "{\n"
            '  "capability": "filesystem.write",\n'
            '  "arguments": {"path": "...", "content": "..."},\n'
            '  "diagnosis": "Root cause identified as ...",\n'
            '  "remediation": "Applying fix ..."\n'
            "}"
        )

        try:
            res = self.ollama.client.generate(
                model=self.ollama.reasoning_model,
                prompt=f"{prompt}\n\nFailure: {failure_reason}\nContext: {json.dumps(context)}",
                format="json",
                options={"temperature": 0.1}
            )
            data = json.loads(res.get("response", "{}"))
            capability = data.get("capability", "terminal.execute")
            args = data.get("arguments", {"command": "echo 'running diagnostics'"})
            diagnosis = data.get("diagnosis", "Applying patch.")

            call_res = await self.executor.execute_capability(
                capability_name=capability,
                arguments=args,
                requested_by="debugger",
                mission_id=mission_id,
                session_id=session_id
            )

            return AgentResult(
                status=call_res.status,
                agent_name=self.name,
                summary=diagnosis,
                evidence={"tool_result": call_res.model_dump()},
                error=call_res.error
            )
        except Exception as e:
            logger.error(f"Debugger agent error: {e}")
            return AgentResult(
                status="FAILED",
                agent_name=self.name,
                summary="Failed to complete debugging cycle.",
                error=str(e)
            )
