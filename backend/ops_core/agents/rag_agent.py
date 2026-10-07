"""
O.P.S. RAG Agent
Responsible for querying and indexing ChromaDB persistent vector knowledge.
Uses: Qwen3 1.7B
Allowed capabilities: rag.search, rag.index
"""

import logging
from typing import Dict, Any, Optional, List
from ops_core.agents.base import BaseAgent, AgentResult
from ops_core.services.event_bus import OPSEventBus

logger = logging.getLogger("ops.agents.rag")


class RAGAgent(BaseAgent):
    name: str = "RAG"
    description: str = "Retrieves semantic information from persistent memory and indexes knowledge bases."
    assigned_model: str = "Qwen3 1.7B"
    allowed_capabilities: List[str] = ["rag.search", "rag.index"]

    async def process(self, directive: str, context: Optional[Dict[str, Any]] = None) -> AgentResult:
        context = context or {}
        session_id = context.get("session_id", "default")
        mission_id = context.get("mission_id")

        await OPSEventBus.emit_thought_async(
            thought=f"Querying persistent knowledge base: {directive}",
            agent=self.name,
            task_id=mission_id
        )

        call_res = await self.executor.execute_capability(
            capability_name="rag.search",
            arguments={"query": directive, "top_k": 3},
            requested_by="rag",
            mission_id=mission_id,
            session_id=session_id
        )

        return AgentResult(
            status=call_res.status,
            agent_name=self.name,
            summary=f"Retrieved {len(call_res.data or [])} relevant knowledge chunks.",
            evidence={"tool_result": call_res.model_dump()},
            error=call_res.error
        )
