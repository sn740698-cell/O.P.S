"""
O.P.S. Core Agent 2 — Understand Prompt / Router Agent
Model: Qwen3 1.7B

Role:
Understands the structured request and chooses the top-level execution domain.
Only two routes exist:
1. WEB AGENT
2. AUTOMATION AGENT

It does not select individual crawlers or automation tools.
"""

import json
import logging
from typing import Dict, Any
from ops_core.services.agents.base_agent import BaseOPSAgent, AgentTaskState

logger = logging.getLogger("ops.agents.router")


class RouterAgent(BaseOPSAgent):
    agent_id = "router_agent"
    agent_name = "Understand Prompt / Router Agent"
    level = "Core"
    assigned_model = "Qwen3 1.7B"
    allowed_tools = []
    parent_agent = "Prompt Template Agent"
    downstream_destination = "Web Superior Agent OR Automation Superior Agent"

    async def process(self, state: AgentTaskState) -> Dict[str, Any]:
        task_id = state.get("task_id", "")
        prompt = (state.get("prompt") or state.get("original_prompt") or "").strip()
        template_data = state.get("template_data", {})
        
        await self.emit_status(task_id, "PROCESSING", {"objective": template_data.get("normalized_objective")})
        await self.emit_thought(task_id, f"Evaluating top-level domain routing for: '{prompt}'")

        # 1. Check prompt domain characteristics
        domain_hint = template_data.get("domain_hint")
        
        # 2. Local Model Decision (Qwen3 1.7B)
        system_instruction = (
            "You are the O.P.S. Understand Prompt / Router Agent (Model: Qwen3 1.7B).\n"
            "Your ONLY decision is to classify the request into exactly ONE of two domains:\n"
            "- 'WEB': User is asking for information, facts, research, biographies, theories, or news from the internet.\n"
            "- 'AUTOMATION': User wants the computer to perform an action (e.g. open apps, play songs, navigate websites like Instagram/YouTube, control files, folders, or desktop UI).\n\n"
            "Examples:\n"
            "'Who is Virat Kohli?' -> WEB\n"
            "'Tell me the latest AI news.' -> WEB\n"
            "'What is the weather tomorrow?' -> WEB\n"
            "'Open Instagram and take me to Reels.' -> AUTOMATION\n"
            "'Open YouTube and search a song.' -> AUTOMATION\n"
            "'Play my Spotify playlist.' -> AUTOMATION\n"
            "'Move PDFs to Documents.' -> AUTOMATION\n"
            "'Create an O.P.S. folder on Desktop.' -> AUTOMATION\n\n"
            "Respond in JSON with: 'route_domain' ('WEB' or 'AUTOMATION'), 'reasoning', 'confidence'."
        )

        route_domain = "WEB"
        reasoning = "Information retrieval request."

        try:
            res = self.ollama.client.generate(
                model=self.ollama.reasoning_model,
                prompt=f"{system_instruction}\n\nUser Request: {prompt}\nTemplate Intent: {template_data.get('intent')}",
                format="json",
                options={"temperature": 0.0}
            )
            data = json.loads(res.get("response", "{}"))
            r = data.get("route_domain", "").strip().upper()
            if r in ["WEB", "AUTOMATION"]:
                route_domain = r
                reasoning = data.get("reasoning", "")
        except Exception as e:
            logger.warning(f"Router model decision fallback: {e}")
            # Fallback to domain hint from template agent
            if domain_hint in ["WEB", "AUTOMATION"]:
                route_domain = domain_hint
            else:
                p_lower = prompt.lower()
                if any(k in p_lower for k in ["open ", "launch ", "start ", "play ", "create ", "make ", "move ", "delete ", "type ", "navigate", "reels", "search in youtube"]):
                    route_domain = "AUTOMATION"
                else:
                    route_domain = "WEB"

        await self.emit_thought(task_id, f"Domain Decision -> [{route_domain}] (Reason: {reasoning})")
        await self.emit_status(task_id, "COMPLETED", {"route_domain": route_domain})

        return {
            "route_domain": route_domain,
            "active_agent": self.agent_name,
            "active_model": self.assigned_model
        }
