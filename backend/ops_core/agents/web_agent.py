"""
O.P.S. Web Agent
Responsible for external web search, crawling, and content extraction across untrusted boundaries.
Uses: Qwen3 1.7B
Allowed capabilities: web.search, web.crawl
"""

import json
import logging
from typing import Dict, Any, Optional, List
from ops_core.agents.base import BaseAgent, AgentResult
from ops_core.services.event_bus import OPSEventBus

logger = logging.getLogger("ops.agents.web")


class WebAgent(BaseAgent):
    name: str = "Web"
    description: str = "Performs web searches, crawling, and live web data retrieval across untrusted boundary."
    assigned_model: str = "Qwen3 1.7B"
    allowed_capabilities: List[str] = ["web.search", "web.crawl"]

    async def process(self, directive: str, context: Optional[Dict[str, Any]] = None) -> AgentResult:
        context = context or {}
        session_id = context.get("session_id", "default")
        mission_id = context.get("mission_id")

        await OPSEventBus.emit_thought_async(
            thought=f"Initiating web query: {directive}",
            agent=self.name,
            task_id=mission_id
        )

        # Determine if search or crawl
        if directive.startswith("http://") or directive.startswith("https://") or "url" in context:
            capability = "web.crawl"
            args = {"url": context.get("url", directive)}
        else:
            capability = "web.search"
            args = {"query": directive}

        call_res = await self.executor.execute_capability(
            capability_name=capability,
            arguments=args,
            requested_by="web",
            mission_id=mission_id,
            session_id=session_id
        )

        return AgentResult(
            status=call_res.status,
            agent_name=self.name,
            summary=f"Retrieved web information for: {directive}" if call_res.status == "SUCCESS" else f"Web fetch failed: {call_res.error}",
            evidence={"tool_result": call_res.model_dump()},
            error=call_res.error
        )
