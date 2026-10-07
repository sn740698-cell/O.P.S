"""
O.P.S. Canonical Fast Router (Qwen3 0.6B)
Fast, low-latency (<50ms) intent classification and mode dispatch.
Modes: CHAT, TASK, MISSION, MEMORY, CLARIFICATION.
"""

import json
import re
import logging
from enum import Enum
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from ops_core.services.ollama_service import OPSOllamaService

logger = logging.getLogger("ops.router.fast_router")


class ExecutionMode(str, Enum):
    CHAT = "CHAT"
    TASK = "TASK"
    MISSION = "MISSION"
    MEMORY = "MEMORY"
    CLARIFICATION = "CLARIFICATION"


class RouterDecision(BaseModel):
    mode: ExecutionMode = ExecutionMode.CHAT
    intent: str = "GENERAL_CONVERSATION"
    complexity: str = "LOW"                  # "LOW", "MEDIUM", "HIGH"
    target_agent: str = "response"           # "response", "automation", "browser", "web", "research", "developer", "rag", "memory"
    suggested_agent: Optional[str] = None
    required_capabilities: List[str] = Field(default_factory=list)
    suggested_capability: Optional[str] = None
    requires_planning: bool = False
    requires_confirmation: bool = False
    clarification_question: Optional[str] = None
    parameters: Dict[str, Any] = Field(default_factory=dict)
    confidence: float = 0.95
    estimated_complexity: str = "LOW"


RoutingDecision = RouterDecision


class FastRouter:
    def __init__(self, ollama_service: Optional[OPSOllamaService] = None):
        self.ollama = ollama_service or OPSOllamaService()

    # Fast heuristic patterns for zero-latency routing (<5ms)
    FAST_PATTERNS = [
        # MEMORY
        (r"(?i)^(?:remember|store|save)\s+(?:that|this|my)\b", "MEMORY", "MEMORY_STORE", "memory", []),
        
        # TASK / AUTOMATION
        (r"(?i)^(?:open|launch|start)\s+(chrome|browser|google)\b", "TASK", "LAUNCH_BROWSER", "automation", ["browser.open", "desktop.launch_app"]),
        (r"(?i)^(?:open|launch|start)\s+(vlc|spotify|whatsapp|vscode|vs code|calculator|calc|notepad)\b", "TASK", "LAUNCH_APP", "automation", ["desktop.launch_app"]),
        (r"(?i)^(?:open|view|show)\s+(?:file|folder|downloads|documents|desktop)\s*(.*)", "TASK", "OPEN_FILE", "automation", ["desktop.open_file"]),
        (r"(?i)^(?:create|make)\s+(?:a\s+)?(?:folder|directory)\s+([a-zA-Z0-9_\-\. ]+)", "TASK", "CREATE_DIRECTORY", "automation", ["filesystem.create_directory"]),
        (r"(?i)^(?:delete|remove)\s+(?:the\s+)?(?:folder|file|directory)\s+(.*)", "TASK", "DELETE_PATH", "automation", ["filesystem.delete"]),
        
        # TASK / WEB
        (r"(?i)^(?:search|look\s+up|find)\s+(?:latest|current|recent|the)?\s*(.*)", "TASK", "WEB_SEARCH", "web", ["web.search"]),
        (r"(?i)^(?:who\s+is|what\s+is\s+the\s+weather|tell\s+me\s+about)\s+(.*)", "TASK", "WEB_RESEARCH", "web", ["web.search"]),
        
        # CHAT / EXPLANATION
        (r"(?i)^(?:what\s+is\s+(?:python|javascript|rust|html|css|docker|react|django|an?|the)|explain\s+|tell\s+me\s+about|hello|hi|hey|howdy|good\s+(?:morning|evening|afternoon)|who\s+are\s+you)\b", "CHAT", "CONVERSATION", "response", []),

        # RAG / PROJECT
        (r"(?i)^(?:where\s+is|find\s+in\s+my\s+code|where\s+did\s+i\s+put|search\s+my\s+project)\s+(.*)", "TASK", "RAG_SEARCH", "rag", ["rag.search"]),
        
        # MISSION / DEVELOPMENT
        (r"(?i)^(?:build|create|develop|refactor|generate)\s+(?:a\s+)?(?:react|django|website|app|dashboard|fullstack|api|feature)\b", "MISSION", "SOFTWARE_DEVELOPMENT", "developer", ["filesystem.write", "terminal.execute", "terminal.run_tests"]),
        (r"(?i)^(?:fix|repair|debug)\s+(?:this\s+)?(?:bug|error|test|failure|issue)\b", "MISSION", "BUG_FIX_AND_TEST", "developer", ["terminal.execute", "terminal.run_tests", "filesystem.write"]),
        (r"(?i)^(?:organize|sort|clean\s+up)\s+(?:my\s+)?(?:downloads|documents|files|desktop)\b", "MISSION", "ORGANIZE_FILES", "automation", ["filesystem.list_directory", "filesystem.move"])
    ]

    async def route(self, prompt: str, session_context: Optional[Dict[str, Any]] = None) -> RouterDecision:
        p_clean = prompt.strip()

        # 1. Zero-latency heuristic matching
        for pattern, mode, intent, target_agent, capabilities in self.FAST_PATTERNS:
            match = re.search(pattern, p_clean)
            if match:
                requires_planning = (mode == "MISSION")
                requires_conf = ("delete" in intent.lower() or "remove" in intent.lower())
                return RouterDecision(
                    mode=ExecutionMode(mode),
                    intent=intent,
                    complexity="HIGH" if mode == "MISSION" else ("MEDIUM" if len(capabilities) > 1 else "LOW"),
                    estimated_complexity="HIGH" if mode == "MISSION" else ("MEDIUM" if len(capabilities) > 1 else "LOW"),
                    target_agent=target_agent,
                    suggested_agent=target_agent,
                    required_capabilities=capabilities,
                    suggested_capability=capabilities[0] if capabilities else None,
                    requires_planning=requires_planning,
                    requires_confirmation=requires_conf,
                    parameters={"query": p_clean, "matched_pattern": pattern},
                    confidence=0.98
                )

        # 2. Fast Ollama Qwen3 0.6B routing fallback
        system_prompt = (
            "You are the O.P.S. Fast Intent Router (Qwen3 0.6B).\n"
            "Classify the user prompt into exactly one structured JSON decision.\n"
            "Modes: ['CHAT', 'TASK', 'MISSION', 'MEMORY', 'CLARIFICATION']\n"
            "Target Agents: ['response', 'automation', 'browser', 'web', 'research', 'developer', 'rag', 'memory']\n\n"
            "JSON Format:\n"
            "{\n"
            '  "mode": "CHAT" | "TASK" | "MISSION" | "MEMORY" | "CLARIFICATION",\n'
            '  "intent": "SHORT_INTENT_NAME",\n'
            '  "complexity": "LOW" | "MEDIUM" | "HIGH",\n'
            '  "target_agent": "response" | "automation" | "browser" | "web" | "developer" | "rag",\n'
            '  "required_capabilities": ["capability.name"],\n'
            '  "requires_planning": true | false,\n'
            '  "requires_confirmation": true | false\n'
            "}"
        )

        try:
            res = self.ollama.client.generate(
                model=self.ollama.fast_model,  # Qwen3 0.6B
                prompt=f"{system_prompt}\n\nUser Prompt: {p_clean}",
                format="json",
                options={"temperature": 0.0, "num_predict": 100}
            )
            raw = json.loads(res.get("response", "{}"))
            mode_val = raw.get("mode", "CHAT").upper()
            if mode_val not in ExecutionMode.__members__:
                mode_val = "CHAT"
            tgt_agent = raw.get("target_agent", "response")
            req_caps = raw.get("required_capabilities", [])
            cmplx = raw.get("complexity", "LOW")

            return RouterDecision(
                mode=ExecutionMode(mode_val),
                intent=raw.get("intent", "GENERAL_QUERY"),
                complexity=cmplx,
                estimated_complexity=cmplx,
                target_agent=tgt_agent,
                suggested_agent=tgt_agent,
                required_capabilities=req_caps,
                suggested_capability=req_caps[0] if req_caps else None,
                requires_planning=raw.get("requires_planning", False),
                requires_confirmation=raw.get("requires_confirmation", False),
                parameters={"prompt": p_clean},
                confidence=0.92
            )
        except Exception as e:
            logger.warning(f"Router LLM fallback to CHAT: {e}")
            return RouterDecision(
                mode=ExecutionMode.CHAT,
                intent="DIRECT_ANSWER",
                complexity="LOW",
                estimated_complexity="LOW",
                target_agent="response",
                suggested_agent="response",
                parameters={"prompt": p_clean},
                confidence=0.80
            )
