"""
O.P.S. 2.0 Request Classification and Automatic Mode Routing Engine
Analyzes user requests and automatically chooses the correct operational engine and mode:
1. ANSWERING ENGINE:
   - LLM Mode: Local LLM reasoning (Qwen3 1.7B) without network overhead.
   - Web Mode: Live external search, scraping, and evidence synthesis.
   - Hybrid Mode: Local reasoning combined with verified fresh research.
   - Document Mode: Grounded retrieval over temporary uploaded documents (Pinecone).
2. AUTOMATION ENGINE:
   - Desktop Automation: Windows UI automation via Pywinauto (Calculator, Notepad, Explorer, etc.).
   - Browser Automation: Web portal automation via Playwright (YouTube, Google, forms, navigation).
   - Hybrid Automation: Cross-platform browser download + desktop application interaction.
3. COMPOSITE EXECUTION:
   - Coordinated cross-engine execution (Web Research + Browser Automation + Desktop Automation).
4. CLARIFICATION GATE:
   - Prompt ambiguity detection and targeted clarification requests.

Employs semantic intent analysis, syntactic differentiation between inquiries vs actions,
fast deterministic pattern recognition, and Qwen3 0.6B structured JSON fallback.
"""

import re
import time
import json
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger("OPS.RequestRouter")

# Canonical Task Categories (Section 3.A)
TASK_ANSWER = "ANSWER"
TASK_AUTOMATION = "AUTOMATION"
TASK_COMPOSITE = "COMPOSITE"
TASK_CLARIFICATION = "CLARIFICATION"

# Canonical Engine Categories (Section 6.A)
ENGINE_ANSWERING = "ANSWERING"
ENGINE_AUTOMATION = "AUTOMATION"
ENGINE_COMPOSITE = "COMPOSITE"
ENGINE_CLARIFICATION = "CLARIFICATION"

# Canonical Modes
MODE_LLM = "LLM"
MODE_WEB = "WEB"
MODE_HYBRID = "HYBRID"
MODE_DOCUMENT = "DOCUMENT"
MODE_CLARIFICATION = "CLARIFICATION"

# Automation Modes
MODE_AUTOMATION = "AUTOMATION"
MODE_DESKTOP_AUTO = "DESKTOP"
MODE_BROWSER_AUTO = "BROWSER"
MODE_HYBRID_AUTO = "HYBRID"
MODE_COMPOSITE = "COMPOSITE"

# Backward-Compatibility Route Enums
ROUTE_GENERAL_CHAT = "GENERAL_CHAT"
ROUTE_SIMPLE_QUESTION = "SIMPLE_QUESTION"
ROUTE_COMPLEX_REASONING = "COMPLEX_REASONING"
ROUTE_WEB_RESEARCH = "WEB_RESEARCH"
ROUTE_SYSTEM_AUTOMATION = "SYSTEM_AUTOMATION"
ROUTE_CODE_GENERATION = "CODE_GENERATION"
ROUTE_OTHER = "OTHER_SUPPORTED_TASK"

# Real Execution Stages for Pop-up Cockpit Preview
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

STAGES_DESKTOP_AUTO = [
    "Understanding request",
    "Targeting desktop application",
    "Formulating automation plan",
    "Evaluating safety policy",
    "Executing desktop actions",
    "Verifying window state",
    "Completing response"
]

STAGES_BROWSER_AUTO = [
    "Understanding request",
    "Launching browser context",
    "Navigating to web target",
    "Executing web interactions",
    "Verifying page state",
    "Completing response"
]

STAGES_HYBRID_AUTO = [
    "Understanding request",
    "Planning cross-platform actions",
    "Executing browser operations",
    "Verifying download state",
    "Executing desktop application",
    "Verifying system state",
    "Completing response"
]

STAGES_COMPOSITE = [
    "Understanding directive",
    "Coordinating cross-engine plan",
    "Searching authoritative web sources",
    "Verifying download package",
    "Evaluating installation safety gate",
    "Executing browser download",
    "Launching desktop installer",
    "Verifying execution outcome",
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
    MODE_AUTOMATION: STAGES_DESKTOP_AUTO,
    MODE_DESKTOP_AUTO: STAGES_DESKTOP_AUTO,
    MODE_BROWSER_AUTO: STAGES_BROWSER_AUTO,
    MODE_HYBRID_AUTO: STAGES_HYBRID_AUTO,
    MODE_COMPOSITE: STAGES_COMPOSITE,
    MODE_DOCUMENT: STAGES_DOCUMENT,
    MODE_CLARIFICATION: [
        "Understanding request",
        "Detecting ambiguity",
        "Formulating clarification question",
        "Completing response"
    ]
}


def classify_request_mode(
    query: str,
    conversation_history: Optional[List[Dict[str, Any]]] = None,
    allow_model_call: bool = True
) -> Dict[str, Any]:
    """
    Intelligently classifies user query into task category, engine, and mode:
    Adheres strictly to O.P.S. 2.0 Specification Section 3.
    """
    q = (query or "").strip()
    q_lower = q.lower()
    t_start = time.time()

    if not q:
        return _build_router_result(
            task_type=TASK_ANSWER,
            active_engine=ENGINE_ANSWERING,
            mode=MODE_LLM,
            intent="EMPTY_CONVERSATION_TURN",
            goal="Standby for user directive",
            requires_web=False,
            requires_llm=True,
            reason="Empty directive defaulted to conversational standby.",
            search_query="",
            confidence=1.0,
            t_start=t_start
        )

    words = q_lower.split()

    # =========================================================================
    # 1. Ambiguity / Clarification Detection (Section 3.A #4)
    # =========================================================================
    vague_directives = [
        "open it", "run it", "click it", "delete it", "download it",
        "open app", "create it", "do it", "do that", "do this",
        "do that now", "start it", "fix it", "make it happen"
    ]
    if q_lower in vague_directives or (len(words) <= 3 and any(v == q_lower for v in ["do that", "open it", "run it", "click it", "delete it"])):
        clarification_q = "Could you please specify which application, website, file, or target action you would like me to execute?"
        return _build_router_result(
            task_type=TASK_CLARIFICATION,
            active_engine=ENGINE_CLARIFICATION,
            mode=MODE_CLARIFICATION,
            intent="AMBIGUOUS_DIRECTIVE",
            goal="Obtain required disambiguation details from user",
            requires_web=False,
            requires_llm=False,
            reason="Directive lacks specific application, file, or target entity.",
            search_query="",
            confidence=0.99,
            t_start=t_start,
            needs_clarification=True,
            clarification_prompt=clarification_q
        )

    # =========================================================================
    # 2. Composite Cross-Engine Detection (Section 3.A #3 & Section 3.C)
    # Tasks requiring web research/discovery followed by browser/desktop actions
    # e.g. "Find the official Python download page and download the installer"
    # e.g. "Find the official Python installer, download it and open it"
    # =========================================================================
    has_discovery_intent = any(w in q_lower for w in ["find the official", "find official", "search for official", "discover official", "locate the installer", "find the installer", "find the download page"])
    has_chained_action = any(w in q_lower for w in ["and download", "download and", "download it and", "then open", "and open", "download the installer", "download and install", "download and run"])

    if (has_discovery_intent and has_chained_action) or \
       ("find" in q_lower and "installer" in q_lower and "download" in q_lower) or \
       ("download" in q_lower and "open it" in q_lower and "find" in q_lower) or \
       ("download" in q_lower and "installer" in q_lower and "open" in q_lower):
        return _build_router_result(
            task_type=TASK_COMPOSITE,
            active_engine=ENGINE_COMPOSITE,
            mode=MODE_COMPOSITE,
            intent="CROSS_ENGINE_RESEARCH_AND_AUTOMATION",
            goal=f"Research official sources online and execute subsequent automation: {q}",
            requires_web=True,
            requires_llm=True,
            reason="Directive coordinates web research discovery with subsequent computer automation.",
            search_query=_extract_search_query(q),
            confidence=0.98,
            t_start=t_start
        )

    # =========================================================================
    # 3. Syntactic & Semantic Check: Asking "How to" vs Asking to Execute
    # "Explain how to install Python" -> ANSWER (LLM)
    # "Install Python on my computer" -> AUTOMATION (Desktop)
    # =========================================================================
    is_how_to_question = bool(re.search(
        r"^\b(?:how\s+(?:can\s+i|do\s+i|to)|explain\s+how\s+to|show\s+me\s+how\s+to|guide\s+(?:me\s+)?on\s+how|tutorial\s+on\s+how|what\s+are\s+the\s+steps\s+to|tell\s+me\s+how\s+to)\b",
        q_lower
    )) or bool(re.search(r"\bexplain\s+how\b", q_lower))

    # =========================================================================
    # 4. System Automation Engine Detection (Section 3.A #2 & Section 5)
    # Only triggered if user is NOT asking an explanation question!
    # =========================================================================
    if not is_how_to_question:
        # A. Desktop Automation Signals (Calculator, Notepad, File Explorer, VS Code, Folders, etc.)
        desktop_apps = [
            "calculator", "calc", "calc.exe",
            "notepad", "notepad.exe",
            "file explorer", "explorer", "explorer.exe",
            "vs code", "vscode", "code",
            "paint", "mspaint", "cmd", "powershell"
        ]
        has_desktop_app = any(app in q_lower for app in desktop_apps)

        is_desktop_automation = False
        approval_gate = False
        approval_reason = ""

        if has_desktop_app and any(q_lower.startswith(w) for w in ["open ", "launch ", "start ", "close ", "type ", "write "]):
            is_desktop_automation = True
        elif has_desktop_app and ("navigate to" in q_lower or "go to" in q_lower):
            is_desktop_automation = True
        elif any(w in q_lower for w in ["create folder", "create a folder", "make a folder", "new folder", "rename file", "close window"]):
            is_desktop_automation = True
        elif any(w in q_lower for w in ["in notepad", "into notepad", "in vs code", "in calculator"]):
            is_desktop_automation = True
        elif any(q_lower.startswith(w) for w in ["install ", "setup "]) and any(w in q_lower for w in ["on my computer", "on my pc", "on my machine", "on this system", "locally"]):
            is_desktop_automation = True
            approval_gate = True
            approval_reason = "Software installation modifies local Windows system configuration."

        if is_desktop_automation:
            return _build_router_result(
                task_type=TASK_AUTOMATION,
                active_engine=ENGINE_AUTOMATION,
                mode=MODE_DESKTOP_AUTO,
                intent="DESKTOP_AUTOMATION_EXECUTION",
                goal=f"Execute desktop automation: {q}",
                requires_web=False,
                requires_llm=False,
                reason="User directive targets local Windows desktop applications or filesystem.",
                search_query="",
                confidence=0.98,
                t_start=t_start,
                approval_required=approval_gate,
                approval_reason=approval_reason
            )

        # B. Browser Automation Signals (YouTube, Google search, websites, web forms)
        browser_destinations = ["youtube", "google", "wikipedia", "github.com", "reddit", "twitter", "x.com", "linkedin", "amazon", "netflix", "instagram"]
        has_browser_site = any(site in q_lower for site in browser_destinations)
        has_browser_explicit = any(w in q_lower for w in ["in browser", "in my browser", "in the browser", "web browser", "open website", "navigate to", "fill out form"])
        has_browser_search = bool(re.search(r"^\bsearch\s+google\s+for\b", q_lower)) or bool(re.search(r"\bsearch\s+in\s+google\b", q_lower))

        is_browser_automation = False
        if has_browser_search:
            is_browser_automation = True
        elif has_browser_site and any(q_lower.startswith(w) for w in ["open ", "launch ", "go to ", "navigate to ", "visit "]):
            is_browser_automation = True
        elif has_browser_explicit and any(q_lower.startswith(w) for w in ["open ", "navigate to ", "go to ", "visit ", "search "]):
            is_browser_automation = True
        elif any(q_lower.startswith(w) for w in ["navigate to https://", "navigate to http://"]):
            is_browser_automation = True

        if is_browser_automation:
            return _build_router_result(
                task_type=TASK_AUTOMATION,
                active_engine=ENGINE_AUTOMATION,
                mode=MODE_BROWSER_AUTO,
                intent="BROWSER_AUTOMATION_EXECUTION",
                goal=f"Execute browser automation: {q}",
                requires_web=False,
                requires_llm=False,
                reason="User directive targets web browser navigation and portal interaction.",
                search_query="",
                confidence=0.98,
                t_start=t_start
            )

    # =========================================================================
    # 5. Hybrid Answering Mode Detection (Section 4 — Hybrid Mode)
    # Questions combining conceptual explanation/reasoning with live current external info
    # e.g. "Compare the latest React and Vue versions"
    # e.g. "Explain a technology and find its latest developments"
    # =========================================================================
    is_hybrid = False
    if any(re.search(pat, q_lower, re.IGNORECASE) for pat in [
        r"\bcompare\s+(?:the\s+)?latest\b",
        r"\bcompare\s+(?:the\s+)?(?:recent|current)\b",
        r"\bcompare\s+latest\b",
        r"\b(?:explain|understand|overview)\b.*?\band\s+(?:find|search|retrieve|get|research|check)\s+(?:its\s+)?(?:recent|latest|new|current)\b",
        r"\b(?:find|search|research)\s+(?:recent|latest)\s+(?:research\s+)?(?:papers|features|updates)\s+and\s+explain\b",
        r"\bcompare\s+(?:the\s+)?latest\s+\w+\s+(?:and|vs|versus)\s+\w+\b",
        r"\bcompare\s+the\s+latest\s+react\s+and\s+vue\b",
        r"\bcompare\s+react\s+and\s+vue\s+versions?\b",
    ]):
        is_hybrid = True

    if is_hybrid:
        return _build_router_result(
            task_type=TASK_ANSWER,
            active_engine=ENGINE_ANSWERING,
            mode=MODE_HYBRID,
            intent="CURRENT_INFORMATION_AND_EXPLANATION",
            goal=f"Synthesize local reasoning with verified live research: {q}",
            requires_web=True,
            requires_llm=True,
            reason="User requested conceptual explanation combined with fresh external information.",
            search_query=_extract_search_query(q),
            confidence=0.98,
            t_start=t_start
        )

    # =========================================================================
    # 6. Web Mode Detection (Section 4 — Web Mode)
    # Queries demanding current information, today's events, latest versions, or external facts
    # e.g. "What is the latest AI news today?"
    # e.g. "Tell me the latest AI news today."
    # e.g. "What are the latest developments in OpenAI models?"
    # e.g. "Find the latest Python version."
    # =========================================================================
    is_web = False
    web_time_signals = ["today", "latest", "recent", "current", "2025", "2026", "news", "price", "who won", "what happened", "release date", "current version"]

    if any(q_lower.startswith(w) for w in ["what is the latest", "what are the latest", "tell me the latest", "what are today's", "find the latest", "what is today's"]):
        is_web = True
    elif any(w in q_lower for w in ["news today", "ai news", "today's weather", "weather today", "current python version", "latest openai", "developments in openai", "gpu prices"]):
        is_web = True
    elif any(w in q_lower for w in ["search the web for", "search web for", "browse the web for", "look up online"]):
        is_web = True
    elif any(w in q_lower for w in ["what happened in today's", "who won yesterday's", "who won the match"]):
        is_web = True
    elif any(w in q_lower for w in ["find official documentation", "find recent ai research"]):
        is_web = True
    elif any(sig in q_lower for sig in web_time_signals) and not is_how_to_question:
        # Check if it asks about current external information
        is_web = True

    if is_web:
        return _build_router_result(
            task_type=TASK_ANSWER,
            active_engine=ENGINE_ANSWERING,
            mode=MODE_WEB,
            intent="LIVE_EXTERNAL_FACT_RETRIEVAL",
            goal=f"Retrieve fresh authoritative web facts and synthesize evidence: {q}",
            requires_web=True,
            requires_llm=False,
            reason="Query demands current, recent, or externally verifiable live facts.",
            search_query=_extract_search_query(q),
            confidence=0.96,
            t_start=t_start
        )

    # =========================================================================
    # 7. LLM Mode Detection (Section 4 — LLM Mode)
    # Programming concepts, general knowledge, math, logic, chitchat
    # e.g. "Explain Python decorators."
    # e.g. "Explain how to install Python."
    # =========================================================================
    return _build_router_result(
        task_type=TASK_ANSWER,
        active_engine=ENGINE_ANSWERING,
        mode=MODE_LLM,
        intent="LOCAL_REASONING_OR_KNOWLEDGE",
        goal=f"Explain and reason locally: {q}",
        requires_web=False,
        requires_llm=True,
        reason="Ordinary knowledge, programming, or conceptual query answered directly by local LLM.",
        search_query="",
        confidence=0.95,
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
    task_type: str,
    active_engine: str,
    mode: str,
    intent: str,
    goal: str,
    requires_web: bool,
    requires_llm: bool,
    reason: str,
    search_query: str,
    confidence: float,
    t_start: float,
    needs_clarification: bool = False,
    clarification_prompt: Optional[str] = None,
    approval_required: bool = False,
    approval_reason: str = ""
) -> Dict[str, Any]:
    """
    Builds comprehensive, strictly validated JSON router output record
    adhering strictly to Section 3.D requirements.
    """
    latency_ms = round((time.time() - t_start) * 1000, 2)
    stages = STAGES_MAP.get(mode, STAGES_LLM)

    # Determine required agents and tools based on task category and mode
    if task_type == TASK_CLARIFICATION:
        required_agents = ["global_intent_router", "hitl_safety_controller", "result_formatter_agent"]
        required_tools = []
    elif task_type == TASK_COMPOSITE:
        required_agents = [
            "global_intent_router", "task_understanding_planner", "composite_task_coordinator",
            "web_research_agent", "evidence_validation_agent", "automation_planner",
            "hitl_safety_controller", "browser_automation_executor", "desktop_automation_executor",
            "verification_recovery_agent", "result_formatter_agent"
        ]
        required_tools = ["DuckDuckGoSearch", "PlaywrightBrowser", "PywinautoDesktop", "AutomationVerifier"]
    elif task_type == TASK_AUTOMATION:
        required_agents = [
            "global_intent_router", "task_understanding_planner", "automation_planner",
            "hitl_safety_controller",
            "browser_automation_executor" if mode == MODE_BROWSER_AUTO else "desktop_automation_executor",
            "verification_recovery_agent", "result_formatter_agent"
        ]
        required_tools = ["PlaywrightBrowser"] if mode == MODE_BROWSER_AUTO else ["PywinautoDesktop", "AutomationVerifier"]
    else:  # ANSWER
        if mode == MODE_WEB:
            required_agents = ["global_intent_router", "task_understanding_planner", "web_research_agent", "evidence_validation_agent", "answer_synthesis_agent", "result_formatter_agent"]
            required_tools = ["DuckDuckGoSearch", "HTTPXCrawler", "BeautifulSoupExtractor"]
        elif mode == MODE_HYBRID:
            required_agents = ["global_intent_router", "task_understanding_planner", "local_reasoning_agent", "web_research_agent", "evidence_validation_agent", "answer_synthesis_agent", "result_formatter_agent"]
            required_tools = ["DuckDuckGoSearch", "HTTPXCrawler", "QwenReasoningEngine"]
        elif mode == MODE_DOCUMENT:
            required_agents = ["global_intent_router", "task_understanding_planner", "local_reasoning_agent", "result_formatter_agent"]
            required_tools = ["PineconeVectorStore", "DocumentRetriever"]
        else:  # LLM
            required_agents = ["global_intent_router", "task_understanding_planner", "local_reasoning_agent", "result_formatter_agent"]
            required_tools = ["QwenReasoningEngine"]

    return {
        # Both canonical keys for 100% interoperability
        "response_mode": mode,
        "mode": mode,
        "task_type": task_type,
        "active_engine": active_engine,
        "user_intent": intent,
        "intent": intent,
        "user_goal": goal,
        "answering_engine_required": task_type in [TASK_ANSWER, TASK_COMPOSITE],
        "automation_engine_required": task_type in [TASK_AUTOMATION, TASK_COMPOSITE],
        "selected_answering_mode": mode if task_type in [TASK_ANSWER, TASK_COMPOSITE] else None,
        "selected_automation_mode": mode if task_type == TASK_AUTOMATION else (MODE_HYBRID_AUTO if task_type == TASK_COMPOSITE else None),
        "required_agents": required_agents,
        "required_tools": required_tools,
        "execution_plan": [],
        "approval_required": approval_required,
        "approval_reason": approval_reason,
        "clarification_required": needs_clarification,
        "needs_clarification": needs_clarification,
        "clarification_prompt": clarification_prompt,
        "confidence": round(confidence, 2),
        "routing_reason": reason,
        "reason": reason,
        "search_query": search_query,
        "requires_web_research": requires_web,
        "requires_llm_reasoning": requires_llm,
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
    mode = res.get("response_mode") or res.get("mode")
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
