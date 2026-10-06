"""
O.P.S. Core Agent 1 — Prompt Template Agent
Model: Qwen3 0.6B

Role:
First interpretation layer. Contains predefined prompt patterns that help O.P.S. recognize common user objectives.
Normalizes language variations and extracts parameters.

It must NEVER execute, browse, crawl, or control the computer.
"""

import json
import logging
import re
from typing import Dict, Any
from ops_core.services.agents.base_agent import BaseOPSAgent, AgentTaskState

logger = logging.getLogger("ops.agents.prompt_template")


class PromptTemplateAgent(BaseOPSAgent):
    agent_id = "prompt_template_agent"
    agent_name = "Prompt Template Agent"
    level = "Core"
    assigned_model = "Qwen3 0.6B"
    allowed_tools = []
    parent_agent = None
    downstream_destination = "Router Agent"

    KNOWN_PATTERNS = [
        # Automation patterns
        {"regex": r"^(?:open|launch|start)\s+(instagram|insta)\b.*?(?:reels|feed|chat|direct)?", "template": "open_application_and_perform_task", "intent": "application_automation", "app": "Instagram", "action": "navigate", "domain_hint": "AUTOMATION"},
        {"regex": r"^(?:open|launch|start|search)\s+(youtube)\b.*?(?:search|find|play)?\s*(.*)", "template": "search_application_for_query", "intent": "application_automation", "app": "YouTube", "action": "search", "domain_hint": "AUTOMATION"},
        {"regex": r"^(?:play|open)\s+(spotify)\b.*?(?:playlist|song|track)?\s*(.*)", "template": "play_playlist", "intent": "media_playback", "app": "Spotify", "action": "play", "domain_hint": "AUTOMATION"},
        {"regex": r"^(?:open|play)\s+(vlc)\b.*?(?:video|movie|file)?\s*(.*)", "template": "play_media_file", "intent": "media_playback", "app": "VLC", "action": "play", "domain_hint": "AUTOMATION"},
        {"regex": r"^(?:open|launch|start)\s+([a-zA-Z0-9_\-\. ]+?)(?:\s+and\s+(?:do|search|open|run|go to)\s+(.+))?$", "template": "open_application", "intent": "application_automation", "domain_hint": "AUTOMATION"},
        {"regex": r"^(?:open|view|show|read)\s+(.+?\.(?:pdf|txt|docx|xlsx|py|json|md|csv|png|jpg|mp4|mkv))$", "template": "open_file", "intent": "file_operation", "domain_hint": "AUTOMATION"},
        {"regex": r"^(?:open|view|show)\s+(downloads|documents|desktop|pictures|music|videos)\b", "template": "open_folder", "intent": "file_operation", "domain_hint": "AUTOMATION"},
        {"regex": r"^(?:create|make|new)\s+(?:a\s+)?(?:folder|directory)\s+(?:called|named\s+)?([a-zA-Z0-9_\-\. ]+)(?:\s+(?:on|in|inside)\s+(.+))?", "template": "create_folder", "intent": "desktop_action", "domain_hint": "AUTOMATION"},
        {"regex": r"^(?:create|make|new|write)\s+(?:a\s+)?(?:file|note|notes)\s+(?:called|named\s+)?([a-zA-Z0-9_\-\. ]+)", "template": "create_file", "intent": "desktop_action", "domain_hint": "AUTOMATION"},
        {"regex": r"^(?:move|copy|delete|rename|refresh|restart|lock)\s+(.*)", "template": "perform_desktop_action", "intent": "desktop_action", "domain_hint": "AUTOMATION"},
        
        # Web info patterns
        {"regex": r"^(?:who\s+is|tell\s+me\s+about|biography\s+of)\s+([a-zA-Z0-9_\-\. ]+)", "template": "who_is_person", "intent": "web_research", "domain_hint": "WEB"},
        {"regex": r"^(?:latest|current|recent|today'?s?|news\s+about)\s+(.+)", "template": "latest_topic_news", "intent": "web_research", "domain_hint": "WEB"},
        {"regex": r"^(?:what\s+happened\s+today|today'?s?\s+news|what\s+is\s+happening)", "template": "what_happened_today", "intent": "web_research", "domain_hint": "WEB"},
        {"regex": r"^(?:what\s+is|what\s+are|how\s+to|explain|why\s+is|compare|search\s+web\s+for)\s+(.+)", "template": "informational_query", "intent": "web_research", "domain_hint": "WEB"},
    ]

    async def process(self, state: AgentTaskState) -> Dict[str, Any]:
        task_id = state.get("task_id", "")
        prompt = (state.get("prompt") or state.get("original_prompt") or "").strip()
        
        await self.emit_status(task_id, "PROCESSING", {"prompt": prompt})
        await self.emit_thought(task_id, f"Matching natural language pattern for: '{prompt}'")

        # 1. Pattern Matching & Normalization Engine (Fast Heuristic)
        p_clean = prompt.strip()
        matched_template = None
        extracted_vars: Dict[str, Any] = {}
        domain_hint = None

        for p in self.KNOWN_PATTERNS:
            match = re.search(p["regex"], p_clean, re.IGNORECASE)
            if match:
                matched_template = p["template"]
                domain_hint = p["domain_hint"]
                extracted_vars["matched_intent"] = p["intent"]
                extracted_vars["groups"] = [g for g in match.groups() if g is not None]
                if "app" in p:
                    extracted_vars["application"] = p["app"]
                if "action" in p:
                    extracted_vars["action"] = p["action"]
                break

        # 2. Local Model Normalization (Qwen3 0.6B)
        system_instruction = (
            "You are the O.P.S. Prompt Template Agent (Model: Qwen3 0.6B).\n"
            "Your job is to normalize the user's phrasing into an objective and extract variables.\n"
            "Do NOT execute anything. Return JSON with: 'template', 'intent', 'normalized_objective', 'entities', 'domain_hint' ('WEB' or 'AUTOMATION')."
        )
        
        try:
            res = self.ollama.client.generate(
                model=self.ollama.router_model,
                prompt=f"{system_instruction}\n\nUser Prompt: {prompt}",
                format="json",
                options={"temperature": 0.0}
            )
            model_data = json.loads(res.get("response", "{}"))
        except Exception as e:
            logger.warning(f"Prompt Template model parsing fallback: {e}")
            model_data = {}

        # Merge extracted metadata
        final_template = matched_template or model_data.get("template") or "generic_request"
        final_domain_hint = domain_hint or model_data.get("domain_hint") or ("AUTOMATION" if any(k in prompt.lower() for k in ["open", "play", "create", "move", "launch", "type"]) else "WEB")
        
        entities_dict = dict(extracted_vars)
        if isinstance(model_data.get("entities"), dict):
            entities_dict.update(model_data["entities"])
        elif isinstance(model_data.get("entities"), list):
            entities_dict["items"] = model_data["entities"]

        template_payload = {
            "template": final_template,
            "intent": model_data.get("intent") or extracted_vars.get("matched_intent", "general"),
            "normalized_objective": model_data.get("normalized_objective") or prompt,
            "entities": entities_dict,
            "domain_hint": final_domain_hint,
            "confidence": 0.98 if matched_template else 0.90
        }

        await self.emit_thought(task_id, f"Normalized objective: '{template_payload['normalized_objective']}' (Template: {final_template}, Domain Candidate: {final_domain_hint})")
        await self.emit_status(task_id, "COMPLETED", {"template_data": template_payload})

        return {
            "template_data": template_payload,
            "active_agent": self.agent_name,
            "active_model": self.assigned_model
        }
