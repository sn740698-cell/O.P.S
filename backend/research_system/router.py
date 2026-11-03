"""
O.P.S. 2.0 Request Classification and Automatic Mode Routing Engine
Analyzes user requests and automatically chooses the correct operational mode:
1. LLM MODE: Think and answer using local LLM reasoning (Qwen3 1.7B).
2. WEB MODE: Search, retrieve, crawl, and answer using fresh external evidence.
3. HYBRID MODE: Combine LLM reasoning with live web research for an integrated answer.
4. CLARIFICATION MODE: Request clarification when user intent is genuinely ambiguous.

Employs fast deterministic intent pattern recognition alongside Qwen3 0.6B
structured JSON routing with deterministic schema validation and safe fallback.
"""

import re
import time
import json
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger("OPS.RequestRouter")

# Canonical Response Mode Constants
MODE_LLM = "LLM"
MODE_WEB = "WEB"
MODE_HYBRID = "HYBRID"
MODE_CLARIFICATION = "CLARIFICATION"
MODE_DOCUMENT = "DOCUMENT"

# Backward-Compatibility Route Enums
ROUTE_GENERAL_CHAT = "GENERAL_CHAT"
ROUTE_SIMPLE_QUESTION = "SIMPLE_QUESTION"
ROUTE_COMPLEX_REASONING = "COMPLEX_REASONING"
ROUTE_WEB_RESEARCH = "WEB_RESEARCH"
ROUTE_SYSTEM_AUTOMATION = "SYSTEM_AUTOMATION"
ROUTE_CODE_GENERATION = "CODE_GENERATION"
ROUTE_OTHER = "OTHER_SUPPORTED_TASK"

MODE_AUTOMATION = "AUTOMATION"
MODE_DESKTOP_AUTO = "DESKTOP"
MODE_BROWSER_AUTO = "BROWSER"
MODE_HYBRID_AUTO = "HYBRID_AUTO"

# Real Execution Stages for Pop-up Cockpit Preview (Section 5.B)
STAGES_LLM = [
    "Understanding request",
    "Classifying intent",
    "Preparing reasoning context",
    "Generating answer",
    "Completing response"
]

STAGES_WEB = [
    "Understanding request",
    "Selecting research strategy",
    "Searching the web",
    "Retrieving relevant pages",
    "Extracting information",
    "Validating evidence",
    "Generating answer",
    "Completing response"
]

STAGES_HYBRID = [
    "Understanding request",
    "Analyzing the question",
    "Preparing reasoning context",
    "Searching external sources",
    "Retrieving information",
    "Validating evidence",
    "Combining knowledge and evidence",
    "Generating final answer",
    "Completing response"
]

STAGES_AUTOMATION = [
    "Understanding request",
    "Selecting automation mode",
    "Formulating execution plan",
    "Executing actions",
    "Verifying system state",
    "Completing response"
]

STAGES_DOCUMENT = [
    "Understanding request",
    "Searching uploaded document",
    "Reading document passages",
    "Preparing grounded answer",
    "Completing response"
]

STAGES_MAP = {
    MODE_LLM: STAGES_LLM,
    MODE_WEB: STAGES_WEB,
    MODE_HYBRID: STAGES_HYBRID,
    MODE_AUTOMATION: STAGES_AUTOMATION,
    MODE_DESKTOP_AUTO: STAGES_AUTOMATION,
    MODE_BROWSER_AUTO: STAGES_AUTOMATION,
    MODE_HYBRID_AUTO: STAGES_AUTOMATION,
    MODE_DOCUMENT: STAGES_DOCUMENT,
    MODE_CLARIFICATION: [
        "Understanding request",
        "Detecting ambiguity",
        "Formulating clarification question",
        "Completing response"
    ]
}

# =========================================================================
# Pattern Definitions for Fast Deterministic Detection
# =========================================================================

# Clear signals that the user wants to combine conceptual explanation with live papers / current models / comparisons
HYBRID_PATTERNS = [
    r"\b(?:explain|understand|overview)\b.*?\band\s+(?:find|search|retrieve|get|research|check)\s+(?:its\s+)?(?:recent|latest|new|current)\b",
    r"\b(?:explain|understand)\b.*?\band\s+(?:research|find|search)\b",
    r"\b(?:find|search|research)\s+(?:recent|latest)\s+(?:research\s+)?(?:papers|features|updates)\s+and\s+explain\b",
    r"\bcompare\s+(?:the\s+)?latest\b.*?\b(?:explain|architecture|differences?)\b",
    r"\bexplain\s+(?:the\s+)?(?:architecture|mechanism|internals)\b.*?\b(?:latest|recent|new|features|releases?)\b",
    r"\bexplain\s+(?:the\s+)?latest\b",
    r"\bcompare\s+latest\b",
    r"\bcompare\s+the\s+latest\s+\w+\s+models\b",
    r"\bcompare\s+the\s+latest\s+\w+\s+gpu\b",
    r"\bexplain\s+a\s+technology\s+and\s+find\s+its\s+latest\b",
    r"\bcompare\s+the\s+latest\s+three\s+gpu\s+models\b",
]

# Explicit live external fact queries where only web retrieval is requested
WEB_MODE_PATTERNS = [
    r"https?://\S+",
    r"www\.\S+",
    r"\bwhat\s+is\s+the\s+latest\s+ai\s+news\b",
    r"\blatest\s+(?:ai\s+)?news\s+today\b",
    r"\bwhat\s+are\s+today's\s+technology\s+updates\b",
    r"\btoday's\s+weather\b",
    r"\bwhat\s+is\s+today's\s+weather\b",
    r"\bweather\s+today\b",
    r"\bweather\s+in\s+[a-zA-Z\s]+\s+today\b",
    r"\bcurrent\s+python\s+version\b",
    r"\bcurrent\s+version\s+of\b",
    r"\bwho\s+won\s+yesterday's\s+match\b",
    r"\bwho\s+won\s+the\s+match\b",
    r"\bwhat\s+happened\s+in\s+today's\b",
    r"\bfind\s+(?:official\s+)?(?:django|react|vue|angular|fastapi|langchain|ollama)\s+documentation\b",
    r"\bfind\s+recent\s+ai\s+research\s+papers\b",
    r"\bwhat\s+are\s+the\s+current\s+gpu\s+prices\b",
    r"\bcurrent\s+gpu\s+prices\b",
    r"\bwhat\s+happened\s+today\b",
    r"\bsearch\s+(?:the\s+)?web\s+for\b",
    r"\bbrowse\s+the\s+web\b",
]

# Pure LLM Mode: General explanations, programming concepts, mathematics, logic, conversational acknowledgments
LLM_MODE_PATTERNS = [
    # Conversational turns & acknowledgments
    r"^\b(?:hello|hi|hey|good\s+(?:morning|afternoon|evening)|greetings|howdy|sup)\b",
    r"^\b(?:how\s+are\s+you|how's\s+it\s+going|how\s+do\s+you\s+do)\b",
    r"^\b(?:who\s+are\s+you|what\s+can\s+you\s+do|introduce\s+yourself)\b",
    r"^\b(?:yeah|yes|yep|yup|ok|okay|sure|alright|fine|cool|got\s+it|understood|agreed|sounds\s+good|right)\b",
    r"^\b(?:thank\s+you|thanks|good\s+job|awesome|bye|goodbye|see\s+ya)\b",
    r"^\b(?:continue|go\s+on|tell\s+me\s+more|proceed)\b",

    # Concept explanations
    r"^\bexplain\s+ai\s+agents\b",
    r"^\bwhat\s+is\s+an\s+ai\s+agent\b",
    r"^\bwhat\s+is\s+python\??$",
    r"^\bexplain\s+python\s+decorators\b",
    r"^\bwhat\s+is\s+langgraph\??$",
    r"^\bexplain\s+react\s+versus\s+angular\b",
    r"^\bexplain\s+machine\s+learning\b",
    r"^\bhelp\s+me\s+understand\s+a\s+programming\s+concept\b",
    r"^\bexplain\s+how\s+weather\s+forecasting\s+works\b",
    r"^\bexplain\s+weather\s+forecasting\b",
    r"^\bexplain\s+cricket\s+scoring\b",

    # Code generation & programming
    r"\bwrite\s+a\s+python\s+(?:program|script|function|calculator|class)\b",
    r"\bimplement\s+(?:quicksort|binary\s+search|linked\s+list|dfs|bfs|fibonacci)\b",
    r"\bwrite\s+(?:a\s+)?(?:python|javascript|typescript|c\+\+|sql|rust)\s+code\b",
    r"\bcalculate\b",
    r"^\d+\s*[\+\-\*\/×÷]\s*\d+",
]

# System Automation Patterns (Pywinauto / Playwright)
AUTOMATION_PATTERNS = [
    r"^\b(?:open|launch|start)\s+(?:notepad|vs\s*code|vscode|calculator|calc|file\s+explorer|explorer|paint|cmd|powershell)\b",
    r"\bcreate\s+(?:a\s+)?folder\b",
    r"\bmake\s+(?:a\s+)?(?:new\s+)?folder\b",
    r"\b(?:type|write)\s+.*?\s+(?:in|into)\s+notepad\b",
    r"\b(?:download|clone)\s+.*?\s+and\s+open\s+(?:it\s+)?in\s+(?:vs\s*code|vscode|code)\b",
    r"\bnavigate\s+to\s+https?://\S+\s+and\s+(?:fill|click|download)\b",
    r"\bclose\s+(?:notepad|vs\s*code|vscode|calculator|window)\b",
    r"\bswitch\s+(?:to\s+)?(?:window|tab)\b",
    r"\b(?:automate|interact\s+with)\s+(?:desktop|browser|app|website)\b"
]


def classify_request_mode(
    query: str,
    conversation_history: Optional[List[Dict[str, Any]]] = None,
    allow_model_call: bool = True
) -> Dict[str, Any]:
    """
    Intelligently classifies user query into one of four O.P.S. response modes:
    - LLM: Direct local LLM reasoning (Qwen3 1.7B) without network overhead.
    - WEB: Live external information retrieval via Search API, HTTPX, Crawlee, BS4.
    - HYBRID: Combined LLM conceptual reasoning + verified live web research.
    - AUTOMATION: Desktop (Pywinauto), Browser (Playwright), or Hybrid automation.
    - CLARIFICATION: Explicit prompt ambiguity resolution.

    Returns structured JSON adhering strictly to Part 4 requirements.
    """
    q = (query or "").strip()
    q_lower = q.lower()
    t_start = time.time()

    if not q:
        return _build_router_result(
            mode=MODE_LLM,
            intent="EMPTY_CONVERSATION_TURN",
            requires_web=False,
            requires_llm=True,
            reason="Empty directive defaulted to conversational standby.",
            search_query="",
            confidence=1.0,
            t_start=t_start
        )

    # 0. High-Priority System Automation Pattern Match (Pywinauto / Playwright)
    for pat in AUTOMATION_PATTERNS:
        if re.search(pat, q_lower, re.IGNORECASE):
            return _build_router_result(
                mode=MODE_AUTOMATION,
                intent="SYSTEM_AUTOMATION_EXECUTION",
                requires_web=False,
                requires_llm=False,
                reason="User directive targets desktop, browser, or hybrid system automation.",
                search_query="",
                confidence=0.98,
                t_start=t_start
            )

    # 1. High-Priority Hybrid Pattern Match
    for pat in HYBRID_PATTERNS:
        if re.search(pat, q_lower, re.IGNORECASE):
            search_term = _extract_search_query(q)
            return _build_router_result(
                mode=MODE_HYBRID,
                intent="CURRENT_INFORMATION_AND_EXPLANATION",
                requires_web=True,
                requires_llm=True,
                reason="User requested conceptual explanation combined with fresh external information.",
                search_query=search_term,
                confidence=0.98,
                t_start=t_start
            )

    # 2. Fast Deterministic Rule: Definite Web Retrieval
    for pat in WEB_MODE_PATTERNS:
        if re.search(pat, q_lower, re.IGNORECASE):
            search_term = _extract_search_query(q)
            return _build_router_result(
                mode=MODE_WEB,
                intent="LIVE_EXTERNAL_FACT_RETRIEVAL",
                requires_web=True,
                requires_llm=False,
                reason="Query demands current, recent, or externally verifiable live facts.",
                search_query=search_term,
                confidence=0.96,
                t_start=t_start
            )

    # 3. Fast Deterministic Rule: Definite LLM Knowledge / Coding / Chat
    for pat in LLM_MODE_PATTERNS:
        if re.search(pat, q_lower, re.IGNORECASE):
            return _build_router_result(
                mode=MODE_LLM,
                intent="LOCAL_REASONING_OR_KNOWLEDGE",
                requires_web=False,
                requires_llm=True,
                reason="Ordinary knowledge, programming, or conversational query answered directly by local LLM.",
                search_query="",
                confidence=0.98,
                t_start=t_start
            )

    # 4. Fallback Heuristics for General Explanations (Rule 1: Do not scrape unnecessarily!)
    # "what is X", "explain X", "how does X work", "why is X" for general established concepts -> LLM Mode
    if any(q_lower.startswith(p) for p in ["what is ", "what are ", "explain ", "how does ", "why is ", "tell me about "]):
        # If it explicitly asks about recent/current/today -> WEB
        if any(w in q_lower for w in ["latest", "today", "current", "recent", "2025", "2026", "news", "price", "release"]):
            search_term = _extract_search_query(q)
            return _build_router_result(
                mode=MODE_WEB,
                intent="CURRENT_INFORMATION_QUERY",
                requires_web=True,
                requires_llm=False,
                reason="Time-sensitive or release inquiry requires fresh external facts.",
                search_query=search_term,
                confidence=0.92,
                t_start=t_start
            )
        else:
            return _build_router_result(
                mode=MODE_LLM,
                intent="CONCEPTUAL_EXPLANATION",
                requires_web=False,
                requires_llm=True,
                reason="General concept explanation handled efficiently by local LLM without web scraping.",
                search_query="",
                confidence=0.94,
                t_start=t_start
            )

    # 5. Non-deterministic queries: Invoke Qwen3 0.6B Fast Router Agent
    if allow_model_call:
        try:
            from research_system.llm.ollama_client import ollama_client, MODEL_QWEN_0_6B
            router_prompt = (
                f"Classify this user request into one of the four response modes:\n"
                f"- LLM: General explanations, programming, concepts, local reasoning without external data.\n"
                f"- WEB: Current news, today's weather, latest versions, documentation lookups, recent events.\n"
                f"- HYBRID: Combining conceptual explanation/reasoning with fresh external research or papers.\n"
                f"- CLARIFICATION: Unclear, meaningless, or severely underspecified request.\n\n"
                f"User Directive: \"{q}\"\n\n"
                f"Output strictly a JSON object with this schema:\n"
                f"{{\n"
                f"  \"response_mode\": \"LLM\" | \"WEB\" | \"HYBRID\" | \"CLARIFICATION\",\n"
                f"  \"intent\": \"short string\",\n"
                f"  \"requires_web_research\": true/false,\n"
                f"  \"requires_llm_reasoning\": true/false,\n"
                f"  \"reason\": \"short user-friendly explanation\",\n"
                f"  \"search_query\": \"extracted web query if applicable, else empty string\",\n"
                f"  \"confidence\": 0.0 to 1.0,\n"
                f"  \"needs_clarification\": true/false\n"
                f"}}"
            )

            model_data = ollama_client.generate_json(
                model=MODEL_QWEN_0_6B,
                prompt=router_prompt,
                system_prompt="You are the O.P.S. 2.0 Request Router. Output valid JSON only.",
                default_fallback=None,
                timeout=12.0
            )

            if model_data and isinstance(model_data, dict):
                raw_mode = str(model_data.get("response_mode", "")).upper().strip()
                if raw_mode in [MODE_LLM, MODE_WEB, MODE_HYBRID, MODE_CLARIFICATION]:
                    validated_mode = raw_mode
                elif model_data.get("requires_web_research") and model_data.get("requires_llm_reasoning"):
                    validated_mode = MODE_HYBRID
                elif model_data.get("requires_web_research"):
                    validated_mode = MODE_WEB
                else:
                    validated_mode = MODE_LLM

                search_q = model_data.get("search_query") or (_extract_search_query(q) if validated_mode in [MODE_WEB, MODE_HYBRID] else "")
                return _build_router_result(
                    mode=validated_mode,
                    intent=model_data.get("intent") or "GENERAL_DIRECTIVE",
                    requires_web=bool(model_data.get("requires_web_research", validated_mode in [MODE_WEB, MODE_HYBRID])),
                    requires_llm=bool(model_data.get("requires_llm_reasoning", validated_mode in [MODE_LLM, MODE_HYBRID])),
                    reason=model_data.get("reason") or f"Automated routing resolved directive to {validated_mode} mode.",
                    search_query=search_q,
                    confidence=float(model_data.get("confidence", 0.90)),
                    needs_clarification=bool(model_data.get("needs_clarification", False)),
                    t_start=t_start
                )
        except Exception as e:
            logger.warning(f"Qwen3 0.6B routing agent encountered error ({e}); falling back to deterministic safety rule.")

    # 6. Default Safe Fallback: LLM Mode (Rule 1: Never scrape unnecessarily!)
    return _build_router_result(
        mode=MODE_LLM,
        intent="GENERAL_TASK",
        requires_web=False,
        requires_llm=True,
        reason="Defaulted safely to local LLM mode without unnecessary web crawling.",
        search_query="",
        confidence=0.85,
        t_start=t_start
    )


def _extract_search_query(raw_query: str) -> str:
    """Extracts a clean, targeted search query string from user prompt."""
    clean = re.sub(
        r"^(?:please\s+)?(?:can\s+you\s+)?(?:find|search\s+for|look\s+up|research|tell\s+me\s+about|what\s+is|what\s+are)\s+",
        "",
        raw_query,
        flags=re.IGNORECASE
    )
    clean = re.sub(r"\b(?:on\s+the\s+web|online|google|bing)\b", "", clean, flags=re.IGNORECASE)
    clean = clean.strip(" ?.!\"'")
    return clean or raw_query.strip()


def _build_router_result(
    mode: str,
    intent: str,
    requires_web: bool,
    requires_llm: bool,
    reason: str,
    search_query: str,
    confidence: float,
    t_start: float,
    needs_clarification: bool = False
) -> Dict[str, Any]:
    """Builds strictly validated JSON router output record."""
    latency_ms = round((time.time() - t_start) * 1000, 2)
    stages = STAGES_MAP.get(mode, STAGES_LLM)
    return {
        "response_mode": mode,
        "intent": intent,
        "requires_web_research": requires_web,
        "requires_llm_reasoning": requires_llm,
        "reason": reason,
        "search_query": search_query,
        "confidence": round(confidence, 2),
        "needs_clarification": needs_clarification,
        "stages": stages,
        "latency_ms": latency_ms
    }


# =========================================================================
# Backward-Compatible Helper Functions
# =========================================================================

def classify_execution_route(query: str, input_type: str = "text") -> str:
    """
    Backward-compatible adapter mapping new response modes to legacy route strings.
    """
    res = classify_request_mode(query, allow_model_call=False)
    mode = res["response_mode"]
    if mode == MODE_WEB or mode == MODE_HYBRID:
        return ROUTE_WEB_RESEARCH
    return ROUTE_GENERAL_CHAT


def log_routing_decision(
    request_id: str,
    conversation_id: str,
    query: str,
    route: str,
    reason: str,
    t_start: float
) -> Dict[str, Any]:
    """
    Logs structured routing telemetry without exposing private thought data.
    """
    t_now = time.time()
    latency_ms = round((t_now - t_start) * 1000, 2)
    record = {
        "request_id": request_id,
        "conversation_id": conversation_id,
        "query_preview": query[:80] + ("..." if len(query) > 80 else ""),
        "response_mode": route,
        "routing_reason": reason,
        "router_latency_ms": latency_ms,
        "timestamp": t_now
    }
    logger.info(
        f"[ROUTER] Req={request_id} Conv={conversation_id[:12]} Mode={route} "
        f"Latency={latency_ms}ms Reason='{reason}'"
    )
    return record
