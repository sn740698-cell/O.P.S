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
        self.fast_model = self.router_model
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
                format="json",
                options={"num_predict": 768}
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
                format="json",
                options={"num_predict": 768}
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
                prompt=f"{system_instruction}\n\nTask: {task}\nType: {content_type}\nOutput:",
                options={"num_predict": 768}
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
        Strips leading role headers and trailing continuation prompts without discarding valid content.
        """
        if not text or not text.strip():
            return "[•] Standby: Ready for instructions."

        raw_lines = [l.strip() for l in text.split("\n") if l.strip()]
        
        # Strip leading assistant prefixes
        cleaned_lines = []
        for l in raw_lines:
            low = l.lower()
            if low.startswith(("o.p.s.:", "ops:", "assistant:", "synthesized knowledge dossier:")):
                remainder = re.sub(r'^(o\.p\.s\.:|ops:|assistant:|synthesized knowledge dossier:)\s*', '', l, flags=re.IGNORECASE).strip()
                if remainder:
                    cleaned_lines.append(remainder)
                continue
            cleaned_lines.append(l)

        # Truncate if subsequent conversational hallucination triggers occur
        lines = []
        for i, l in enumerate(cleaned_lines):
            low = l.lower()
            if i > 0 and any(low.startswith(p) for p in [
                "user:", "human:", "active conversation memory", "task execution context"
            ]):
                break
            lines.append(l)

        if not lines:
            lines = raw_lines if raw_lines else [text.strip()]

        formatted_lines = []
        for line in lines:
            # If already bulleted with [•], [>], etc.
            if line.startswith(("[•]", "[>]", "[STATUS]", "[DATA]", "[INTEL]", "[ACTION]", "[SYS]", "#", "```", "──", "**")):
                formatted_lines.append(line)
            elif line.startswith(("- ", "* ", "• ")):
                formatted_lines.append(f"[•] {line[2:].strip()}")
            elif re.match(r'^\d+[\.\)]\s*', line):
                clean_num = re.sub(r'^\d+[\.\)]\s*', '', line).strip()
                formatted_lines.append(f"[•] {clean_num}")
            else:
                formatted_lines.append(f"[•] {line}")

        return "\n".join(formatted_lines)

    def _synthesize_from_context(self, query: str, context: str) -> str:
        """
        Robust deterministic knowledge extractor from verified web context when LLM is offline or busy.
        """
        if not context or not context.strip():
            return f"[•] STATUS: Web intelligence completed for '{query}'.\n[•] INTEL: Verified public knowledge indexed."

        bullets = []
        raw_lines = [l.strip() for l in context.split("\n") if l.strip()]
        for l in raw_lines:
            if any(l.startswith(prefix) for prefix in ["Person / Subject:", "Description:", "Summary / Extract:", "Wire Update:", "Principle:", "Overview:", "Source:"]):
                cleaned = re.sub(r'^(Person / Subject:|Description:|Summary / Extract:|Wire Update:|Principle:|Overview:|Source:)\s*', '', l).strip()
                if cleaned and len(cleaned) > 20 and not cleaned.startswith("http"):
                    bullets.append(f"[•] {cleaned}")
            elif len(l) > 35 and not l.startswith("===") and not l.startswith("http"):
                bullets.append(f"[•] {l}")
            if len(bullets) >= 6:
                break

        if bullets:
            return "\n".join(bullets)

        # Fallback to sentence split
        sentences = [s.strip() for s in re.split(r'\.\s+', context) if len(s.strip()) > 20]
        if sentences:
            return "\n".join([f"[•] {s}." for s in sentences[:5]])

        return f"[•] INTEL: {context[:500]}"

    def synthesize_crawled_knowledge(self, query: str, context: str) -> str:
        """
        Uses Model 2 (Qwen3 1.7B Reasoning Engine) to synthesize rich live web crawling
        data into authoritative, structured, and factual dotted points with zero hallucination.
        """
        if not context or not context.strip():
            return f"[•] STATUS: Web crawling concluded for '{query}'.\n[•] INTEL: No verified records found in active indexes."

        sys_msg = (
            "You are O.P.S. Knowledge Synthesizer (Model 2: Qwen3 1.7B) created and developed by Suraj.\n"
            "Analyze the verified real-time web intelligence and synthesize a thorough, highly accurate, "
            "and informative explanation for the user directive.\n\n"
            "MANDATORY INSTRUCTIONS:\n"
            "1. Answer strictly using the facts in the context. Do NOT speculate or invent facts.\n"
            "2. Present 4-6 distinct, detailed, and informative bullet points.\n"
            "3. Prefix each bullet point with '[•] '.\n"
            "4. Do NOT repeat phrases or loop sentences."
        )

        user_msg = (
            f"=== VERIFIED WEB CONTEXT ===\n{context[:3200]}\n===========================\n\n"
            f"Directive: {query}\n"
            "Synthesize a clear, detailed bullet-point dossier based strictly on the verified context."
        )

        try:
            res = self.client.chat(
                model=self.reasoning_model,
                messages=[
                    {"role": "system", "content": sys_msg},
                    {"role": "user", "content": user_msg}
                ],
                options={
                    "temperature": 0.2,
                    "top_p": 0.8,
                    "repeat_penalty": 1.25,
                    "repeat_last_n": 128,
                    "num_predict": 768
                }
            )
            msg = res.get("message", {})
            text = (msg.get("content") or "").strip()
            if not text:
                thinking = (msg.get("thinking") or "").strip()
                if thinking and len(thinking) > 50:
                    lines = [l.strip() for l in thinking.split("\n") if l.strip().startswith(("-", "*", "•", "[•]"))]
                    if lines:
                        text = "\n".join(lines)
            if not text:
                return self._synthesize_from_context(query, context)
            return self.format_as_retro_bullets(text)
        except Exception as e:
            logger.error(f"Knowledge synthesis error: {e}")
            return self._synthesize_from_context(query, context)

    def generate_jarvis_response(
        self, 
        user_prompt: str, 
        context: Optional[str] = None, 
        intent: Optional[str] = None,
        history: Optional[str] = None
    ) -> str:
        """
        Model 3: Llama 3.2 1B / Qwen3 1.7B (Shared O.P.S. Personality Layer)
        Maintains the unified J.A.R.V.I.S. voice and personality across all system tasks:
        - Polite, calm, articulate, context-aware.
        - Addresses the user with dignified respect ('sir', 'certainly', 'at your service').
        - Formatted in '90s retro tactical HUD bullet points.
        - Created, developed, and engineered by Suraj.
        - Seamlessly references previous turns in the temporary conversation memory.
        """
        p_lower = user_prompt.lower().strip().strip("?!.,'\"")
        
        # Direct identity response
        if any(p_lower == q for q in [
            "who are you", "what are you", "who made you", "who created you",
            "who is your creator", "who is your developer", "tell me about yourself",
            "who built you", "introduce yourself"
        ]) and not context:
            return (
                "At your service, sir.\n"
                "[•] DESIGNATION: O.P.S. (Over-Engineered Programmed System)\n"
                "[•] CREATOR: Suraj\n"
                "[•] CLASSIFICATION: Ultra-Intelligent Local-First Tactical AI Operating System\n"
                "[•] ARCHITECTURE: Tri-Model LangGraph Multi-Agent Engine (Qwen3 0.6B Intent Router, Qwen3 1.7B Reasoning & Dev Core, Llama 3.2 1B J.A.R.V.I.S. Persona)\n"
                "[•] CAPABILITIES: Real-time autonomous web crawling, PostgreSQL workstation memory vault, safe terminal execution sandbox, and OS desktop automation."
            )

        # For rich factual web research, use Qwen3 1.7B reasoning model for synthesis
        chosen_model = self.reasoning_model if (context and len(context) > 100) else self.conversation_model

        system_instruction = (
            "You are O.P.S. (Over-Engineered Programmed System), an ultra-intelligent, local-first tactical AI Operating System "
            "and autonomous workstation assistant created, developed, and engineered by Suraj.\n\n"
            "MANDATORY IDENTITY & ATTRIBUTION RULES:\n"
            "- You were created and engineered by Suraj.\n"
            "- Address the user with dignified respect ('sir', 'certainly', 'at your service').\n"
            "- Formulate all answers in structured tactical bullet points prefixed with '[•]'.\n"
            "- If the user asks for more details, elaboration, or follow-ups, synthesize thorough expanded information from the conversation history.\n"
            "- Do NOT repeat sentences or loop text. Keep output articulate, crisp, and factual.\n"
            "- If Task Execution Context is provided, ground your entire response strictly in that context."
        )

        messages = [{"role": "system", "content": system_instruction}]

        if history:
            messages.append({"role": "system", "content": f"=== ACTIVE CONVERSATION HISTORY ===\n{history}\n================================="})

        if context:
            messages.append({"role": "system", "content": f"=== TASK EXECUTION CONTEXT ===\n{context}\n============================="})

        messages.append({"role": "user", "content": user_prompt})

        try:
            res = self.client.chat(
                model=chosen_model,
                messages=messages,
                options={
                    "temperature": 0.25,
                    "top_p": 0.8,
                    "repeat_penalty": 1.25,
                    "repeat_last_n": 128,
                    "num_predict": 768
                }
            )
            msg = res.get("message", {})
            text = (msg.get("content") or "").strip()
            if not text:
                thinking = (msg.get("thinking") or "").strip()
                if thinking and len(thinking) > 50:
                    lines = [l.strip() for l in thinking.split("\n") if l.strip().startswith(("-", "*", "•", "[•]"))]
                    if lines:
                        text = "\n".join(lines)
            if not text:
                if context:
                    return f"Certainly, sir. Operations concluded for '{user_prompt}':\n\n{context[:600]}"
                return f"At your service, sir. Directive '{user_prompt}' processed successfully."
            return self.format_as_retro_bullets(text)
        except Exception as e:
            logger.error(f"Jarvis response generation failed: {e}")
            if any(k in p_lower for k in ["who are you", "who created you", "who made you", "creator", "suraj"]):
                return (
                    "At your service, sir.\n"
                    "[•] SYSTEM: O.P.S. (Over-Engineered Programmed System)\n"
                    "[•] CREATOR: Suraj\n"
                    "[•] STATUS: Operational in offline tactical mode."
                )
            if context:
                return (
                    f"At your service, sir. Directive processed:\n"
                    f"[•] STATUS: Operations concluded for '{user_prompt}'.\n"
                    f"[•] INTEL: {context[:500]}\n"
                    f"[•] WORKSTATION: Ready for follow-up directive."
                )
            return (
                f"At your service, sir.\n"
                f"[•] STATUS: Directive processed: '{user_prompt}'\n"
                f"[•] ACTION: Telemetry logged in workstation audit records."
            )


ollama_service = OPSOllamaService()

