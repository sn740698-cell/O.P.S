"""
O.P.S. Model Router & Django Orchestration Gatekeeper Module
Manages model routing across Ollama models:
- Router: Qwen 0.6B (Fast intent detection & model dispatch)
- Reasoning: Llama 3.2 1B (Planning & contextual analysis)
- Coding & Automation: Qwen 1.7B (Code generation & tool argument extraction)

Enforces safety: Models ONLY generate tool intents (JSON), Django executes actions.
"""

import json
import logging
from typing import Dict, Any, Optional
import ollama

logger = logging.getLogger("ops.router")

MODEL_ROUTER = "qwen2.5:0.5b"
MODEL_REASONING = "llama3.2:1b"
MODEL_CODING = "qwen2.5-coder:1.5b"


class OPSModelRouter:
    def __init__(self, ollama_client: Optional[ollama.Client] = None):
        self.client = ollama_client or ollama.Client()

    def route_intent(self, user_prompt: str) -> Dict[str, Any]:
        """
        Routes incoming prompt to the appropriate category using Qwen 0.6B
        Categories: 'CODING', 'AUTOMATION', 'REASONING', 'CONVERSATION'
        """
        system_prompt = (
            "You are the O.P.S Intent Router. Classify the user prompt into exactly one category:\n"
            "- CODING (writing, refactoring, or fixing code)\n"
            "- AUTOMATION (web crawling, PyAutoGUI clicks, Playwright DOM actions, terminal commands)\n"
            "- REASONING (planning, analysis, summarizing)\n"
            "- CONVERSATION (general chat, greetings)\n"
            "Return JSON format: {\"category\": \"CATEGORY_NAME\", \"confidence\": 0.9}"
        )

        try:
            response = self.client.generate(
                model=MODEL_ROUTER,
                prompt=f"{system_prompt}\nUser Prompt: {user_prompt}",
                format="json"
            )
            result = json.loads(response['response'])
            return result
        except Exception as e:
            logger.warning(f"Router fallback due to error: {e}")
            return {"category": "REASONING", "confidence": 0.5}

    def dispatch_and_plan(self, user_prompt: str) -> Dict[str, Any]:
        """
        Dispatches request to specialized model based on routed category.
        """
        intent = self.route_intent(user_prompt)
        category = intent.get("category", "REASONING")

        if category in ["CODING", "AUTOMATION"]:
            target_model = MODEL_CODING
        else:
            target_model = MODEL_REASONING

        logger.info(f"Routed '{user_prompt[:30]}...' -> {category} using {target_model}")

        response = self.client.generate(
            model=target_model,
            prompt=f"System: You are O.P.S Assistant. Analyze request and formulate plan.\nPrompt: {user_prompt}"
        )

        return {
            "routed_category": category,
            "used_model": target_model,
            "response": response['response']
        }
