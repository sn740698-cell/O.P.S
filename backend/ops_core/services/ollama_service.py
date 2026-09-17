"""
O.P.S. Ollama Tri-Model Service Architecture:
1. Router Model (Qwen 2.5 0.5B): Ultra-fast intent classification & task routing.
2. Reasoning Model (Llama 3.2 1B): Multi-step planning & contextual analysis.
3. Coding & Automation Model (Qwen 2.5 Coder 1.5B): Code generation & structured tool call parameters.
"""

import json
import logging
from typing import Dict, Any, List, Optional
from django.conf import settings
import ollama

logger = logging.getLogger("ops.ollama_service")

class OPSOllamaService:
    def __init__(self, host: Optional[str] = None):
        self.host = host or getattr(settings, 'OLLAMA_HOST', 'http://localhost:11434')
        self.client = ollama.Client(host=self.host)
        
        self.router_model = getattr(settings, 'OLLAMA_ROUTER_MODEL', 'qwen2.5:0.5b')
        self.reasoning_model = getattr(settings, 'OLLAMA_REASONING_MODEL', 'llama3.2:1b')
        self.coding_model = getattr(settings, 'OLLAMA_CODING_MODEL', 'qwen2.5-coder:1.5b')

    def route_request(self, prompt: str) -> Dict[str, Any]:
        """
        Model 1: Router (Qwen 2.5 0.5B)
        Classifies prompt into category and returns dispatch metadata.
        """
        system_instruction = (
            "You are the O.P.S Ultra-Fast Intent Router. Analyze the prompt and classify into one category:\n"
            "- CODING (Writing, debugging, or analyzing source code)\n"
            "- AUTOMATION (Browser navigation, GUI clicking, scraping, system commands)\n"
            "- REASONING (Complex planning, document synthesis, multi-step problem solving)\n"
            "- CONVERSATION (General assistance, Q&A, chat)\n"
            "Respond strictly in valid JSON format: "
            "{\"category\": \"CATEGORY\", \"confidence\": 0.95, \"summary\": \"Brief intent description\"}"
        )
        try:
            res = self.client.generate(
                model=self.router_model,
                prompt=f"{system_instruction}\n\nUser Input: {prompt}",
                format="json"
            )
            data = json.loads(res.get('response', '{}'))
            return {
                "status": "success",
                "model": self.router_model,
                "category": data.get("category", "REASONING"),
                "confidence": data.get("confidence", 0.9),
                "summary": data.get("summary", prompt[:60])
            }
        except Exception as e:
            logger.error(f"Router Model failed: {e}")
            return {
                "status": "fallback",
                "model": self.router_model,
                "category": "REASONING",
                "confidence": 0.5,
                "summary": "Fallback routing"
            }

    def generate_plan(self, prompt: str, context: Optional[str] = None) -> Dict[str, Any]:
        """
        Model 2: Reasoning (Llama 3.2 1B)
        Formulates structured step-by-step execution plans.
        """
        system_instruction = (
            "You are O.P.S. Strategic Reasoning Engine. Formulate a clean step-by-step execution plan.\n"
            "Identify necessary tools (e.g. web_scrape, dom_click, edit_file, execute_cmd).\n"
            "Output JSON with keys: \"plan_steps\" (list of strings), \"safety_level\" ('SAFE'/'REQUIRES_CONFIRMATION')."
        )
        ctx_str = f"Context: {context}\n" if context else ""
        try:
            res = self.client.generate(
                model=self.reasoning_model,
                prompt=f"{system_instruction}\n{ctx_str}User Task: {prompt}",
                format="json"
            )
            plan_data = json.loads(res.get('response', '{}'))
            return {
                "status": "success",
                "model": self.reasoning_model,
                "plan": plan_data.get("plan_steps", []),
                "safety_level": plan_data.get("safety_level", "SAFE")
            }
        except Exception as e:
            logger.error(f"Reasoning Model failed: {e}")
            return {
                "status": "error",
                "model": self.reasoning_model,
                "plan": [f"Direct execution of: {prompt}"],
                "safety_level": "SAFE"
            }

    def generate_code_or_tool_params(self, task: str, tool_name: str) -> Dict[str, Any]:
        """
        Model 3: Coding & Automation (Qwen 2.5 Coder 1.5B)
        Generates precise code snippets or structured tool arguments for Playwright/PyAutoGUI.
        """
        system_instruction = (
            f"You are O.P.S. Coding & Tool Synthesizer. Target Tool: {tool_name}.\n"
            "Extract or generate exact tool arguments or code required to execute this step.\n"
            "Output JSON format matching tool parameters."
        )
        try:
            res = self.client.generate(
                model=self.coding_model,
                prompt=f"{system_instruction}\nTask details: {task}",
                format="json"
            )
            result = json.loads(res.get('response', '{}'))
            return {
                "status": "success",
                "model": self.coding_model,
                "parameters": result
            }
        except Exception as e:
            logger.error(f"Coding Model failed: {e}")
            return {
                "status": "error",
                "model": self.coding_model,
                "parameters": {}
            }

    def orchestrate_pipeline(self, user_prompt: str) -> Dict[str, Any]:
        """
        Full 3-Model Orchestration Pipeline:
        1. Route -> 2. Plan -> 3. Synthesize Parameters
        """
        route_info = self.route_request(user_prompt)
        category = route_info.get("category")

        plan_info = self.generate_plan(user_prompt, context=f"Routed as {category}")

        tool_synth = {}
        if category in ["CODING", "AUTOMATION"]:
            tool_synth = self.generate_code_or_tool_params(
                task=user_prompt, 
                tool_name="playwright_dom_action" if category == "AUTOMATION" else "code_editor"
            )

        return {
            "prompt": user_prompt,
            "router": route_info,
            "reasoning": plan_info,
            "coding": tool_synth
        }
