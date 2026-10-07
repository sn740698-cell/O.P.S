"""
O.P.S. Research Agent
Responsible for multi-source research synthesis, fact-checking, and combining web data with internal knowledge.
Uses: Qwen3 1.7B
Allowed capabilities: web.search, web.crawl, rag.search
"""

import json
import logging
from typing import Dict, Any, Optional, List
from ops_core.agents.base import BaseAgent, AgentResult
from ops_core.services.event_bus import OPSEventBus

logger = logging.getLogger("ops.agents.research")


class ResearchAgent(BaseAgent):
    name: str = "Research"
    description: str = "Synthesizes multi-source knowledge combining live web search and persistent memory RAG."
    assigned_model: str = "Qwen3 1.7B"
    allowed_capabilities: List[str] = ["web.search", "web.crawl", "rag.search"]

    async def process(self, directive: str, context: Optional[Dict[str, Any]] = None) -> AgentResult:
        context = context or {}
        session_id = context.get("session_id", "default")
        mission_id = context.get("mission_id")

        await OPSEventBus.emit_thought_async(
            thought=f"Synthesizing research on topic: {directive}",
            agent=self.name,
            task_id=mission_id
        )

        # 1. Search persistent RAG memory
        rag_res = await self.executor.execute_capability(
            capability_name="rag.search",
            arguments={"query": directive, "top_k": 3},
            requested_by="research",
            mission_id=mission_id,
            session_id=session_id
        )

        # 2. Search live web
        web_res = await self.executor.execute_capability(
            capability_name="web.search",
            arguments={"query": directive},
            requested_by="research",
            mission_id=mission_id,
            session_id=session_id
        )

        combined_evidence = {
            "internal_rag": rag_res.data if rag_res.status == "SUCCESS" else [],
            "web_search": web_res.data if web_res.status == "SUCCESS" else []
        }

        return AgentResult(
            status="SUCCESS" if rag_res.status == "SUCCESS" or web_res.status == "SUCCESS" else "PARTIAL",
            agent_name=self.name,
            summary=f"Compiled research findings for '{directive}'.",
            evidence=combined_evidence
        )
