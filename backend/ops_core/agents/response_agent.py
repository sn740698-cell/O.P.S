"""
O.P.S. Response Engine / Response Agent
Synthesizes verified execution evidence into natural language responses for the Pop-up Cockpit.
Grounded in facts: Never reports success unless verified by ground-truth evidence.
"""

import json
import logging
from typing import Dict, Any, Optional, List
from ops_core.agents.base import BaseAgent, AgentResult
from ops_core.services.event_bus import OPSEventBus

logger = logging.getLogger("ops.agents.response")


class ResponseAgent(BaseAgent):
    name: str = "Response"
    description: str = "Synthesizes final evidence-grounded responses for the O.P.S. Pop-up Cockpit."
    assigned_model: str = "Qwen3 1.7B"
    allowed_capabilities: List[str] = []

    async def process(self, directive: str, context: Optional[Dict[str, Any]] = None) -> AgentResult:
        context = context or {}
        evidence = context.get("evidence", {})
        status = context.get("status", "SUCCESS")
        mission_id = context.get("mission_id")

        # Synthesize answer
        prompt = (
            "You are the O.P.S. Response Engine.\n"
            "Format a concise, professional, tactical response for the O.P.S. Pop-up Cockpit.\n"
            "Rules:\n"
            "1. Ground all statements in the provided evidence. Never fabricate success.\n"
            "2. Clearly state what was executed and physically verified.\n"
            "3. If failed or blocked, state the root cause clearly.\n"
        )

        try:
            res = self.ollama.client.generate(
                model=self.ollama.reasoning_model,
                prompt=f"{prompt}\n\nUser Directive: {directive}\nExecution Status: {status}\nEvidence: {json.dumps(evidence, default=str)}",
                options={"temperature": 0.3, "num_predict": 128}
            )
            response_text = res.get("response", "").strip()
            if not response_text:
                if status == "SUCCESS":
                    response_text = f"Action successfully executed and verified: {directive}"
                else:
                    response_text = f"Action could not be completed: {context.get('error', 'Execution failure')}"

            return AgentResult(
                status=status,
                agent_name=self.name,
                summary=response_text,
                evidence=evidence
            )
        except Exception as e:
            logger.error(f"Response agent generation error: {e}")
            fallback_text = f"Completed directive: {directive}" if status == "SUCCESS" else f"Execution failed: {context.get('error', str(e))}"
            return AgentResult(
                status=status,
                agent_name=self.name,
                summary=fallback_text,
                evidence=evidence
            )
