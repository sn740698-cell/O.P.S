"""
O.P.S. Developer Agent
Responsible for repository inspection, code generation, refactoring, and project scaffolding.
Uses: Qwen3 1.7B (reasoning model)
Allowed capabilities: filesystem.*, terminal.execute
"""

import json
import logging
from typing import Dict, Any, Optional, List
from ops_core.agents.base import BaseAgent, AgentResult
from ops_core.services.event_bus import OPSEventBus

logger = logging.getLogger("ops.agents.developer")


class DeveloperAgent(BaseAgent):
    name: str = "Developer"
    description: str = "Handles code generation, filesystem operations, and build tasks."
    assigned_model: str = "Qwen3 1.7B"
    allowed_capabilities: List[str] = [
        "filesystem.read",
        "filesystem.write",
        "filesystem.create_directory",
        "filesystem.delete",
        "filesystem.list_directory",
        "terminal.execute"
    ]

    async def process(self, directive: str, context: Optional[Dict[str, Any]] = None) -> AgentResult:
        context = context or {}
        session_id = context.get("session_id", "default")
        mission_id = context.get("mission_id")

        await OPSEventBus.emit_thought_async(
            thought=f"Analyzing development directive: {directive}",
            agent=self.name,
            task_id=mission_id
        )

        prompt = (
            "You are the O.P.S. Developer Agent.\n"
            "Formulate the exact tool call required to carry out the directive.\n"
            "Available capabilities: filesystem.read, filesystem.write, filesystem.create_directory, "
            "filesystem.delete, filesystem.list_directory, terminal.execute.\n\n"
            "Respond in structured JSON format:\n"
            "{\n"
            '  "capability": "filesystem.write",\n'
            '  "arguments": {"path": "src/app.js", "content": "..."},\n'
            '  "explanation": "Creating main application file."\n'
            "}"
        )

        try:
            res = self.ollama.client.generate(
                model=self.ollama.reasoning_model,
                prompt=f"{prompt}\n\nDirective: {directive}\nContext: {json.dumps(context)}",
                format="json",
                options={"temperature": 0.1}
            )
            data = json.loads(res.get("response", "{}"))
            capability = data.get("capability")
            args = data.get("arguments", {})
            explanation = data.get("explanation", "Executing development task.")

            if not capability or capability not in self.allowed_capabilities:
                # Default fallback heuristic based on directive
                if "read" in directive.lower() or "inspect" in directive.lower():
                    capability = "filesystem.read"
                    args = {"path": args.get("path", ".")}
                elif "create" in directive.lower() or "write" in directive.lower():
                    capability = "filesystem.write"
                else:
                    capability = "terminal.execute"
                    args = {"command": directive}

            call_res = await self.executor.execute_capability(
                capability_name=capability,
                arguments=args,
                requested_by="developer",
                mission_id=mission_id,
                session_id=session_id
            )

            return AgentResult(
                status=call_res.status,
                agent_name=self.name,
                summary=explanation if call_res.status == "SUCCESS" else f"Development action failed: {call_res.error}",
                evidence={"tool_result": call_res.model_dump()},
                error=call_res.error
            )
        except Exception as e:
            logger.error(f"Developer agent error: {e}")
            return AgentResult(
                status="FAILED",
                agent_name=self.name,
                summary="Failed to execute developer directive.",
                error=str(e)
            )
