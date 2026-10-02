"""
O.P.S. Ollama Tri-Model Service Architecture
Implementation based strictly on: OPS_Local_LLM_Model_Roles.md

The three-model setup:
1. Qwen3 0.6B              — Fast Router and Intent Detection
2. Qwen3 1.7B              — Main Reasoning, Planning, Code Gen, and Debugging Model
3. Llama 3.2 1B Instruct   — Conversation, Content Writing, and Jarvis Personality Layer
"""

import json
import logging
import re
from typing import Dict, Any, List, Optional
from django.conf import settings
import ollama

logger = logging.getLogger("ops.ollama_service")


class OPSOllamaService:
    """
    O.P.S. Local-First Tri-Model Service Provider.
    Implements intelligent routing, reasoning, coding, content generation,
    and a unified J.A.R.V.I.S. personality layer.
    """

    def __init__(self, host: Optional[str] = None):
        self.host = host or getattr(settings, 'OLLAMA_HOST', 'http://localhost:11434')
        self.client = ollama.Client(host=self.host)

        # 1. Model 1: Fast Router and Intent Detection (Qwen3 0.6B)
        self.router_model = getattr(
            settings, 'OLLAMA_ROUTER_MODEL', 'hf.co/Qwen/Qwen3-0.6B-GGUF:Q8_0'
        )
        # 2. Model 2: Main Reasoning, Planning, Code Gen, Debugging (Qwen3 1.7B)
        self.reasoning_model = getattr(
            settings, 'OLLAMA_REASONING_MODEL', 'hf.co/Qwen/Qwen3-1.7B-GGUF:Q8_0'
        )
        # 3. Model 3: Conversation, Content, and Jarvis Personality (Llama 3.2 1B Instruct)
        self.conversation_model = getattr(
            settings, 'OLLAMA_CONVERSATION_MODEL', 'hf.co/hugging-quants/Llama-3.2-1B-Instruct-Q8_0-GGUF:Q8_0'
        )

    # =========================================================================
    # MODEL 1: Qwen3 0.6B — Fast Router and Intent Detection
    # =========================================================================

    def route_request(self, prompt: str) -> Dict[str, Any]:
        """
        Model 1: Qwen3 0.6B
        Understands what the user wants in <50ms.
        Extracts intent, complexity ('simple' vs 'complex'), parameters, and target flow.
        """
        system_instruction = (
            "You are the O.P.S. Ultra-Fast Intent Router (Model 1: Qwen3 0.6B).\n"
            "Analyze the user command and output strict JSON with:\n"
            "1. 'intent': One of [OPEN_APPLICATION, WEB_SEARCH, FILE_OPERATION, SYSTEM_COMMAND, "
            "DEVELOPMENT, DEBUGGING, CONTENT_GENERATION, CONVERSATION]\n"
            "2. 'complexity': 'simple' (single tool/action) or 'complex' (multi-step, planning, coding, debugging)\n"
            "3. 'target_flow': 'DIRECT_TOOL' (for simple tool commands), 'REASONING_PLANNER' (for complex development/debugging), "
            "'CONTENT_GENERATOR' (for emails/letters/summaries), or 'CONVERSATIONAL' (for general chat)\n"
            "4. 'parameters': dictionary of extracted items (application, query, location, name, etc.)\n"
            "5. 'summary': one concise sentence describing the user goal.\n\n"
            "Example response:\n"
            "{\"intent\": \"OPEN_APPLICATION\", \"complexity\": \"simple\", \"target_flow\": \"DIRECT_TOOL\", "
            "\"parameters\": {\"application\": \"Chrome\"}, \"summary\": \"Open Chrome application\"}"
        )

        try:
            res = self.client.generate(
                model=self.router_model,
                prompt=f"{system_instruction}\n\nUser Command: {prompt}",
                format="json"
            )
            data = json.loads(res.get('response', '{}'))
            
            # Normalize target flow
            intent = data.get("intent", "CONVERSATION").upper()
            complexity = data.get("complexity", "simple").lower()
            target_flow = data.get("target_flow")

            if not target_flow:
                if complexity == "simple" and intent in ["OPEN_APPLICATION", "WEB_SEARCH", "FILE_OPERATION", "SYSTEM_COMMAND"]:
                    target_flow = "DIRECT_TOOL"
                elif intent in ["DEVELOPMENT", "DEBUGGING"] or complexity == "complex":
                    target_flow = "REASONING_PLANNER"
                elif intent == "CONTENT_GENERATION":
                    target_flow = "CONTENT_GENERATOR"
                else:
                    target_flow = "CONVERSATIONAL"

            return {
                "status": "success",
                "model": self.router_model,
                "intent": intent,
                "complexity": complexity,
                "target_flow": target_flow,
                "parameters": data.get("parameters", {}),
                "summary": data.get("summary", prompt[:60])
            }
        except Exception as e:
            logger.warning(f"Router Model fallback due to: {e}")
            # Heuristic ultra-fast deterministic fallback
            p_lower = prompt.lower()
            if any(k in p_lower for k in ["run claude", "launch claude", "terminal and run claude", "claude in terminal", "claude in the terminal"]):
                intent = "SYSTEM_COMMAND"
                flow = "DIRECT_TOOL"
                complexity = "simple"
            elif any(k in p_lower for k in ["in google", "in youtube", "in the youtube", "in instagram", "on instagram", "search", "google", "find online", "lookup"]):
                intent = "WEB_SEARCH"
                flow = "DIRECT_TOOL"
                complexity = "simple"
            elif any(k in p_lower for k in ["open ", "launch ", "start ", "vs code and open", "vscode and open", "open folder", "open file"]):
                intent = "OPEN_APPLICATION"
                flow = "DIRECT_TOOL"
                complexity = "simple"
            elif any(k in p_lower for k in ["email", "letter", "essay", "summary", "summarize", "write a draft"]):
                intent = "CONTENT_GENERATION"
                flow = "CONTENT_GENERATOR"
                complexity = "simple"
            elif any(k in p_lower for k in ["code", "function", "class", "react", "django", "test", "build", "script", "database", "postgres"]):
                intent = "DEVELOPMENT"
                flow = "REASONING_PLANNER"
                complexity = "complex"
            elif any(k in p_lower for k in ["debug", "error", "fix", "crash", "traceback"]):
                intent = "DEBUGGING"
                flow = "REASONING_PLANNER"
                complexity = "complex"
            else:
                intent = "CONVERSATION"
                flow = "CONVERSATIONAL"
                complexity = "simple"

            return {
                "status": "fallback",
                "model": self.router_model,
                "intent": intent,
                "complexity": complexity,
                "target_flow": flow,
                "parameters": {},
                "summary": prompt[:60]
            }

    # =========================================================================
    # MODEL 2: Qwen3 1.7B — Main Reasoning and Planning Model
    # =========================================================================

    def generate_reasoning_and_plan(self, prompt: str, context: Optional[str] = None) -> Dict[str, Any]:
        """
        Model 2: Qwen3 1.7B
        Main reasoning model. Handles task decomposition, planning, multi-agent coordination,
        and software engineering workflows.
        """
        system_instruction = (
            "You are the O.P.S. Main Reasoning & Planning Engine (Model 2: Qwen3 1.7B).\n"
            "Your responsibility is deep technical reasoning, task decomposition, and creating tactical plans.\n"
            "Deconstruct the user's task into clear sequential execution steps.\n"
            "Determine the agents required (e.g. Planner, Developer, Researcher, Debugger, Tester).\n"
            "Output strict JSON with:\n"
            "- 'plan_steps': list of sequential action steps\n"
            "- 'agents_required': list of agent names needed\n"
            "- 'tools_required': list of tools (terminal, file_system, browser_scrape, gui_action)\n"
            "- 'safety_level': 'SAFE' or 'REQUIRES_CONFIRMATION'"
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
                "plan": plan_data.get("plan_steps", [f"Execute task: {prompt}"]),
                "agents_required": plan_data.get("agents_required", ["DeveloperAgent"]),
                "tools_required": plan_data.get("tools_required", ["terminal", "file_system"]),
                "safety_level": plan_data.get("safety_level", "SAFE")
            }
        except Exception as e:
            logger.error(f"Reasoning Model failed: {e}")
            return {
                "status": "error",
                "model": self.reasoning_model,
                "plan": [
                    f"Analyze requirement: {prompt}",
                    "Synthesize and execute implementation",
                    "Verify execution integrity"
                ],
                "agents_required": ["DeveloperAgent"],
                "tools_required": ["terminal"],
                "safety_level": "SAFE"
            }

    def generate_code_or_debug(self, task: str, tool_name: str = "code_editor", context: Optional[str] = None) -> Dict[str, Any]:
        """
        Model 2: Qwen3 1.7B
        Software-development reasoning, code generation, code analysis, debugging, and refactoring.
        """
        system_instruction = (
            "You are the O.P.S. Developer & Code Synthesizer (Model 2: Qwen3 1.7B).\n"
            f"Target Tool: {tool_name}.\n"
            "Generate production-grade code, debugging solutions, or tool parameters.\n"
            "Output strict JSON with keys: 'code', 'language', 'explanation', 'parameters'."
        )
        ctx_str = f"\nContext:\n{context}\n" if context else ""
        try:
            res = self.client.generate(
                model=self.reasoning_model,
                prompt=f"{system_instruction}{ctx_str}\nTask: {task}",
                format="json"
            )
            result = json.loads(res.get('response', '{}'))
            return {
                "status": "success",
                "model": self.reasoning_model,
                "synthesis": result
            }
        except Exception as e:
            logger.error(f"Code/Debug generation failed: {e}")
            return {
                "status": "error",
                "model": self.reasoning_model,
                "synthesis": {
                    "code": f"# Implementation for: {task}\n",
                    "language": "python",
                    "explanation": "Generated fallback stub."
                }
            }

    # =========================================================================
    # MODEL 3: Llama 3.2 1B Instruct — Conversation, Content & Jarvis Persona
    # =========================================================================

    def generate_content(self, task: str, content_type: str = "general") -> str:
        """
        Model 3: Llama 3.2 1B Instruct
        Content generation: Emails, formal letters, documentation, summaries, explanations.
        """
        system_instruction = (
            "You are O.P.S. Content & Communication Specialist (Model 3: Llama 3.2 1B Instruct).\n"
            "Generate high-quality, professional, well-formatted content matching the user directive.\n"
            "Preserve polite, articulate language. Do not output meta-commentary, just the content itself."
        )
        try:
            res = self.client.generate(
                model=self.conversation_model,
                prompt=f"{system_instruction}\n\nTask: {task}\nType: {content_type}\nOutput:"
            )
            return res.get("response", "").strip()
        except Exception as e:
            logger.error(f"Content generation failed: {e}")
            return f"Draft content for: {task}"

    @staticmethod
    def format_as_retro_bullets(text: str) -> str:
        """
        Ensures response is formatted in authentic '90s retro style tactical bullet points.
        Tags items with [•], [>], [STATUS], or [INTEL].
        """
        lines = [l.strip() for l in text.split("\n") if l.strip()]
        if not lines:
            return "[•] Standby: Ready for instructions."

        formatted_lines = []
        has_intro = False

        for i, line in enumerate(lines):
            # Preserve existing retro brackets, code blocks, dividers
            if line.startswith(("[•]", "[>]", "[STATUS]", "[DATA]", "[INTEL]", "[ACTION]", "[SYS]", "•", "-", "*", "#", "```", "──")):
                if line.startswith(("- ", "* ", "• ")):
                    clean_line = line[2:].strip()
                    formatted_lines.append(f"[•] {clean_line}")
                else:
                    formatted_lines.append(line)
            elif not has_intro and (line.endswith(":") or (i == 0 and len(line) < 70)):
                formatted_lines.append(line)
                has_intro = True
            else:
                formatted_lines.append(f"[•] {line}")

        return "\n".join(formatted_lines)

    def generate_jarvis_response(
        self, 
        user_prompt: str, 
        context: Optional[str] = None, 
        intent: Optional[str] = None,
        history: Optional[str] = None
    ) -> str:
        """
        Model 3: Llama 3.2 1B Instruct (Shared O.P.S. Personality Layer)
        Maintains the unified J.A.R.V.I.S. voice and personality across all system tasks:
        - Polite, calm, articulate, context-aware.
        - Addresses the user with dignified respect ('sir', 'certainly', 'at your service').
        - Formatted in '90s retro tactical HUD bullet points.
        - Seamlessly references previous turns in the temporary conversation memory.
        """
        system_instruction = (
            "You are O.P.S. (Over-Engineered Programmed System), an ultra-intelligent tactical AI Operating System, "
            "modeled in tone after J.A.R.V.I.S. with a 1990s retro tactical HUD terminal aesthetic.\n\n"
            "MANDATORY FORMATTING & MEMORY INSTRUCTIONS:\n"
            "1. Address the user with dignified respect ('sir', 'certainly', 'at your service').\n"
            "2. Understand all follow-up questions and pronouns ('him', 'her', 'it', 'that', 'this', 'tell me more') "
            "by connecting to the Active Conversation Memory provided below.\n"
            "3. Begin with a concise acknowledgment header (e.g. 'At your service, sir. Additional intelligence on [Subject]:').\n"
            "4. Present all facts, updates, explanations, steps, and telemetry in distinct bullet points prefixed with '[•]' or '[>]'.\n"
            "5. For key domains, use tactical brackets, e.g.:\n"
            "   [•] STATUS: ...\n"
            "   [•] INTEL: ...\n"
            "   [•] ACTION: ...\n"
            "6. Keep bullet points crisp, articulate, and punchy. Never write unbroken walls of unstructured text."
        )

        history_str = f"\nActive Conversation Memory (Temporary Session):\n{history}\n" if history else ""
        ctx_str = f"\nTask Execution Context:\n{context}\n" if context else ""
        intent_str = f"Intent: {intent}\n" if intent else ""

        try:
            res = self.client.generate(
                model=self.conversation_model,
                prompt=f"{system_instruction}\n{history_str}{intent_str}{ctx_str}\nUser: {user_prompt}\nO.P.S.:"
            )
            text = res.get("response", "").strip()
            return self.format_as_retro_bullets(text)
        except Exception as e:
            logger.error(f"Jarvis response generation failed: {e}")
            if context:
                return (
                    f"At your service, sir. Directive processed:\n"
                    f"[•] STATUS: Operations concluded for '{user_prompt}'.\n"
                    f"[•] INTEL: {context}\n"
                    f"[•] WORKSTATION: Ready for follow-up directive."
                )
            return (
                f"At your service, sir.\n"
                f"[•] STATUS: Directive processed: '{user_prompt}'\n"
                f"[•] ACTION: Telemetry logged in workstation audit records."
            )
