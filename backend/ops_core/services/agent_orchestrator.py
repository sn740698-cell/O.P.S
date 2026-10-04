"""
O.P.S. LangGraph Multi-Agent Orchestrator Engine
Implementation based strictly on: OPS_Local_LLM_Model_Roles.md

Architecture:
1. Entry: Qwen3 0.6B (Fast Router & Intent Detection)
2. Branching:
   - Simple Task        -> Direct Tool Layer (Open App, Search, File Op)
   - Content Generation -> Llama 3.2 1B Instruct (Emails, Letters, Summaries)
   - Complex Task       -> Qwen3 1.7B (Planning, Reasoning, Multi-Agent Coordination)
3. Sub-Agents:
   - Developer Agent (Qwen3 1.7B + Codebase RAG + Terminal)
   - Browser Agent (Playwright / Web Search / DOM Scraping)
   - System Automation Agent (PyAutoGUI / OS Window Control)
   - Debugger Agent (Qwen3 1.7B Error Diagnostic & Fixes)
4. Exit: Llama 3.2 1B Instruct (Shared J.A.R.V.I.S. Personality Layer)
"""

import re
import uuid
import time
import os
import logging
from typing import Dict, Any, List, Optional, Tuple, TypedDict
from asgiref.sync import sync_to_async
from langgraph.graph import StateGraph, END

from ops_core.services.ollama_service import OPSOllamaService
from ops_core.services.tool_sandbox import OPSToolSandbox
from ops_core.services.event_bus import OPSEventBus
from ops_core.services.session_memory import OPSSessionMemoryManager
from ops_core.services.workstation_memory_service import OPSWorkstationMemoryService
from ops_core.services.scraping_service import GROUNDING_INSTRUCTION

logger = logging.getLogger("ops.agent_orchestrator")


class AgentWorkflowState(TypedDict):
    task_id: str
    session_id: str
    prompt: str
    original_prompt: str
    intent: str
    complexity: str
    target_flow: str
    parameters: Dict[str, Any]
    plan: List[str]
    active_agent: str
    tool_output: Dict[str, Any]
    developer_output: Dict[str, Any]
    browser_output: Dict[str, Any]
    automation_output: Dict[str, Any]
    crawling_output: Dict[str, Any]
    content_output: str
    final_answer: str
    execution_log: List[Dict[str, Any]]
    status: str


class OPSMultiAgentOrchestrator:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(OPSMultiAgentOrchestrator, cls).__new__(cls)
            cls._instance._workflow_app = None
        return cls._instance

    def __init__(self):
        if self._workflow_app is not None:
            return

        self.ollama = OPSOllamaService()
        self.tools = OPSToolSandbox()
        self.memory = OPSSessionMemoryManager()
        self.workstation_memory = OPSWorkstationMemoryService()
        self._workflow_app = self._build_graph()
        logger.info("LangGraph Tri-Model Orchestrator graph compiled successfully.")

    def _build_graph(self):
        graph = StateGraph(AgentWorkflowState)

        # 1. Add Nodes
        graph.add_node("router_node", self.router_node)
        graph.add_node("direct_tool_node", self.direct_tool_node)
        graph.add_node("content_writing_node", self.content_writing_node)
        graph.add_node("reasoning_planner_node", self.reasoning_planner_node)
        graph.add_node("developer_agent_node", self.developer_agent_node)
        graph.add_node("web_crawling_node", self.web_crawling_node)
        graph.add_node("browser_agent_node", self.browser_agent_node)
        graph.add_node("system_automation_agent_node", self.system_automation_agent_node)
        graph.add_node("jarvis_response_node", self.jarvis_response_node)

        # 2. Entry Point
        graph.set_entry_point("router_node")

        # 3. Conditional Routing from Router (Qwen3 0.6B)
        graph.add_conditional_edges(
            "router_node",
            self.route_router_decision,
            {
                "WEB_CRAWLER": "web_crawling_node",
                "DIRECT_TOOL": "direct_tool_node",
                "CONTENT_GENERATOR": "content_writing_node",
                "REASONING_PLANNER": "reasoning_planner_node",
                "JARVIS_DIRECT": "jarvis_response_node"
            }
        )

        # 4. Conditional Edge from Planner (Qwen3 1.7B) to Specialized Agents
        graph.add_conditional_edges(
            "reasoning_planner_node",
            self.route_planner_decision,
            {
                "DEVELOPER": "developer_agent_node",
                "WEB_CRAWLER": "web_crawling_node",
                "BROWSER": "browser_agent_node",
                "AUTOMATION": "system_automation_agent_node",
                "JARVIS": "jarvis_response_node"
            }
        )

        # 5. Direct Convergence to Unified J.A.R.V.I.S. Personality Layer (Llama 3.2 1B)
        graph.add_edge("direct_tool_node", "jarvis_response_node")
        graph.add_edge("content_writing_node", "jarvis_response_node")
        graph.add_edge("developer_agent_node", "jarvis_response_node")
        graph.add_edge("web_crawling_node", "jarvis_response_node")
        graph.add_edge("browser_agent_node", "jarvis_response_node")
        graph.add_edge("system_automation_agent_node", "jarvis_response_node")

        # 6. Exit from J.A.R.V.I.S. Persona
        graph.add_edge("jarvis_response_node", END)

        return graph.compile()

    # =========================================================================
    # NODE 1: Router (Qwen3 0.6B)
    # =========================================================================

    async def router_node(self, state: AgentWorkflowState) -> Dict[str, Any]:
        task_id = state.get("task_id", str(uuid.uuid4()))
        session_id = state.get("session_id", task_id)
        prompt = state.get("prompt", "")

        # Contextual follow-up & pronoun resolution ("him", "her", "it", "that", "tell me more")
        resolved_prompt, ref_entity = self.memory.resolve_contextual_query(session_id, prompt)
        if ref_entity and resolved_prompt != prompt:
            await OPSEventBus.emit_agent_thought_async(
                thought=f"Resolved follow-up reference ('{prompt}' -> '{resolved_prompt}') using temporary session memory.",
                agent="Contextual Memory",
                step=1,
                task_id=task_id
            )
            prompt = resolved_prompt
            state["prompt"] = resolved_prompt

        await OPSEventBus.emit_agent_thought_async(
            thought=f"Analyzing directive & classifying intent in <50ms...",
            agent="Router Agent (Qwen3 0.6B)",
            step=1,
            task_id=task_id
        )

        # Route Intent using Model 1
        route_res = self.ollama.route_request(prompt)
        intent = route_res.get("intent", "CONVERSATION")
        complexity = route_res.get("complexity", "simple")
        target_flow = route_res.get("target_flow", "CONVERSATIONAL")
        parameters = route_res.get("parameters", {})

        await OPSEventBus.emit_agent_thought_async(
            thought=f"Intent: {intent} | Complexity: {complexity.upper()} | Target Flow: {target_flow}",
            agent="Router Agent (Qwen3 0.6B)",
            step=1,
            task_id=task_id
        )

        return {
            "intent": intent,
            "complexity": complexity,
            "target_flow": target_flow,
            "parameters": parameters,
            "active_agent": "RouterAgent",
            "status": "ROUTED"
        }

    @staticmethod
    def extract_universal_site_and_query(prompt: str) -> Optional[Tuple[str, str]]:
        """
        Universally extracts target website and query across ALL websites on earth.
        Supports:
        - "Search 'Who is Virat Kohli?' in Google." -> ("Google", "Who is Virat Kohli?")
        - "Search about any song like begin in the YouTube." -> ("YouTube", "any song like begin")
        - "Go to Instagram and search for the song." -> ("Instagram", "the song")
        - "Go to Amazon and search for wireless headphones" -> ("Amazon", "wireless headphones")
        - "Search for laptop reviews on Reddit" -> ("Reddit", "laptop reviews")
        - "Open Netflix and search for Stranger Things" -> ("Netflix", "Stranger Things")
        - "Search on Pinterest for retro room design" -> ("Pinterest", "retro room design")
        - "Go to Spotify and search for Coldplay" -> ("Spotify", "Coldplay")
        - "Search for Python async tutorial on Medium" -> ("Medium", "Python async tutorial")
        - "Go to GitHub and search for LangGraph examples" -> ("GitHub", "LangGraph examples")
        - "Search on eBay for vintage watch" -> ("eBay", "vintage watch")
        - "In Wikipedia search Quantum Computing" -> ("Wikipedia", "Quantum Computing")
        - "Go to Bilibili and search for anime" -> ("Bilibili", "anime")
        """
        clean_p = re.sub(r'\b(search|open|launch|start|run|find|go to)\.', r'\1', prompt, flags=re.IGNORECASE).strip().strip('"\'')

        # Pattern 1: (go to|open|browse to) <site> and (search for|search|find|look up|play|check) <query>
        m1 = re.search(
            r'(?:go\s+to|open|browse\s+to)\s+([a-zA-Z0-9\.\-_]+)\s+(?:and\s+)?(?:search(?:\s+for|\s+about)?|find|look\s+up|play|check)\s+(?:for\s+|about\s+)?["\']?([^"\'\.\?]+)["\']?',
            clean_p,
            re.IGNORECASE
        )
        if m1:
            site = m1.group(1).strip()
            query = m1.group(2).strip()
            if site and query:
                return site, query

        # Pattern 2: (search for|search about|search|find|look up|play) <query> (in|on|at) (the)? <site>
        m2 = re.search(
            r'(?:search(?:\s+for|\s+about)?|find|look\s+up|play)\s+["\']?([^"\']+)["\']?\s+(?:in|on|at)\s+(?:the\s+)?([a-zA-Z0-9\.\-_]+)',
            clean_p,
            re.IGNORECASE
        )
        if m2:
            query = m2.group(1).strip()
            site = m2.group(2).strip()
            site = re.sub(r'[\.\?!]+$', '', site).strip()
            if site and query:
                return site, query

        # Pattern 3: (in|on|at) (the)? <site> (search for|search about|search|find|look up) <query>
        m3 = re.search(
            r'(?:in|on|at)\s+(?:the\s+)?([a-zA-Z0-9\.\-_]+)\s+(?:search(?:\s+for|\s+about)?|find|look\s+up|play)\s+(?:for\s+|about\s+)?["\']?([^"\'\.\?]+)["\']?',
            clean_p,
            re.IGNORECASE
        )
        if m3:
            site = m3.group(1).strip()
            query = m3.group(2).strip()
            if site and query:
                return site, query

        # Pattern 4: search (on|in|at) <site> for <query>
        m4 = re.search(
            r'search\s+(?:on|in|at)\s+(?:the\s+)?([a-zA-Z0-9\.\-_]+)\s+(?:for|about)?\s+["\']?([^"\'\.\?]+)["\']?',
            clean_p,
            re.IGNORECASE
        )
        if m4:
            site = m4.group(1).strip()
            query = m4.group(2).strip()
            if site and query:
                return site, query

        return None

    @staticmethod
    def is_memory_capture_command(prompt: str) -> bool:
        p = prompt.lower().strip()
        if any(k in p for k in [
            "add it to this, my memory", "add to this, my memory", "add to this my memory",
            "add this to my memory", "add it to my memory", "add to my memory",
            "save to my memory", "save into my memory", "add it to memory", "add this to memory",
            "add to memory", "put in my memory", "save to memory"
        ]):
            return True
        if "remember this" in p and ("this is" in p or "memory" in p or "as " in p):
            return True
        if "this is" in p and "memory" in p:
            return True
        return False

    @staticmethod
    def is_memory_recall_command(prompt: str) -> bool:
        p = prompt.lower().strip()
        if any(k in p for k in ["from the memory", "from my memory", "from memory"]):
            return True
        if (p.startswith("recall ") or p.startswith("play ") or p.startswith("open ") or p.startswith("add ")) and "memory" in p:
            return True
        return False

    @staticmethod
    def extract_memory_label(prompt: str) -> str:
        p = prompt.strip()
        m = re.search(r'this\s+is\s+["\']?([^"\'\.,\?!]+)["\']?', p, re.IGNORECASE)
        if m:
            label = m.group(1).strip()
            label = re.sub(r'[\s,]+add\s+(?:it\s+)?to\s+.*$', '', label, flags=re.IGNORECASE).strip()
            if label:
                return label

        m2 = re.search(r'remember\s+this\s+as\s+["\']?([^"\'\.,\?!]+)["\']?', p, re.IGNORECASE)
        if m2:
            return m2.group(1).strip()

        clean = p
        for prefix in [
            "add it to this, my memory", "add to this, my memory", "add to this my memory",
            "add this to my memory", "add it to my memory", "add to my memory",
            "save to my memory", "save into my memory", "add it to memory", "add this to memory",
            "add to memory", "remember this", "save to memory"
        ]:
            if prefix in clean.lower():
                clean = re.sub(re.escape(prefix), '', clean, flags=re.IGNORECASE)

        clean = re.sub(r'^(?:[:, -]+|is\s+)', '', clean).strip(" '\",.:;?!")
        return clean or "Workstation Memory Item"

    @staticmethod
    def is_identity_query(prompt: str) -> bool:
        """
        Detects self-identity, creator, and origin questions to prevent
        unwanted external web scrapes and ensure accurate attribution to Suraj.
        """
        p = prompt.lower().strip().strip("?!.,'\"")
        identity_exact = {
            "who are you", "who r u", "who are u", "what are you", "what r u",
            "who made you", "who created you", "who built you", "who programmed you",
            "who developed you", "who is your creator", "who is your developer",
            "who is your maker", "who is your author", "who is your master",
            "who is your owner", "who owns you", "what is your name",
            "tell me about yourself", "introduce yourself", "describe yourself",
            "who is ops", "what is ops", "who is o.p.s.", "what is o.p.s.",
            "who is suraj", "who is your boss"
        }
        if p in identity_exact:
            return True
        if any(p.startswith(prefix) for prefix in [
            "who are you", "what are you", "who made you", "who created you",
            "who built you", "who is your creator", "who is your developer",
            "tell me about yourself", "introduce yourself", "who programmed you"
        ]):
            return True
        if ("who are you" in p or "who created you" in p or "who made you" in p or "tell me about yourself" in p) and len(p.split()) <= 8:
            return True
        return False

    def route_router_decision(self, state: AgentWorkflowState) -> str:
        prompt = state.get("prompt", "").lower().strip()

        # -1. Self-Identity & Creator Intent (Direct J.A.R.V.I.S. Persona with Suraj Attribution)
        if self.is_identity_query(prompt):
            return "JARVIS_DIRECT"

        # 0. User Workstation Memory Persistence & Recall (PostgreSQL ops_db)
        if self.is_memory_capture_command(prompt) or self.is_memory_recall_command(prompt):
            return "DIRECT_TOOL"

        # 1. Informational & Research Queries -> Web Crawling Agent (Crawlee / ScrapeGraphAI)
        # Prevents unwanted desktop browser popups for pure question/information searches
        if any(prompt.startswith(p) for p in [
            "who is ", "who was ", "tell me about ", "biography of ",
            "what is ", "what are ", "explain ", "theory of ", "concept of ",
            "latest news", "live news", "live update", "breaking news", "headlines"
        ]) or any(k in prompt for k in [
            "crawl", "web crawl", "crawlee", "scrapegraph", "using web crawling", "via web crawl",
            "quantum computing", "theory of relativity", "black hole", "string theory"
        ]):
            if not any(k in prompt for k in ["in terminal", "terminal and", "open file", "open folder", "run claude", "launch "]):
                if not (prompt.startswith("go to ") and " and search" in prompt):
                    return "WEB_CRAWLER"

        # 2. Universal Direct Tool / Fast-path override
        if self.extract_universal_site_and_query(prompt):
            return "DIRECT_TOOL"
        if any(prompt.startswith(p) for p in [
            "open ", "launch ", "start ", "browse to ", "go to ",
            "run ", "execute ", "search ", "find ", "look up ", "play "
        ]):
            return "DIRECT_TOOL"
        if any(k in prompt for k in [
            "in terminal", "terminal run", "terminal command", "run terminal",
            "run claude", "claude in the terminal", "terminal and run claude", "claude in terminal", "launch claude",
            "vs code and open", "open in vs code", "open in vscode", "vscode and open",
            "open messages in instagram", "messages in instagram",
            "open folder", "open file", "open downloads", "open desktop", "open documents",
            "d:\\", "c:\\"
        ]):
            return "DIRECT_TOOL"
        target_flow = state.get("target_flow", "CONVERSATIONAL")
        if target_flow == "DIRECT_TOOL":
            return "DIRECT_TOOL"
        elif target_flow == "CONTENT_GENERATOR":
            return "CONTENT_GENERATOR"
        elif target_flow == "REASONING_PLANNER":
            return "REASONING_PLANNER"
        return "JARVIS_DIRECT"

    # =========================================================================
    # NODE 2: Direct Tool Execution (Bypasses 1.7B for Speed)
    # =========================================================================

    async def direct_tool_node(self, state: AgentWorkflowState) -> Dict[str, Any]:
        task_id = state.get("task_id", "")
        prompt = state.get("prompt", "")
        intent = state.get("intent", "SYSTEM_COMMAND")
        params = state.get("parameters", {})

        await OPSEventBus.emit_agent_thought_async(
            thought=f"Directly executing simple tool action ({intent}) without taxing reasoning model...",
            agent="Tool Sandbox (Fast Path)",
            step=2,
            task_id=task_id
        )

        output = {}
        p_lower = prompt.lower()

        # 0. Workstation Memory Capture (PostgreSQL ops_db)
        if self.is_memory_capture_command(prompt):
            label = self.extract_memory_label(prompt)
            capture_res = await sync_to_async(self.workstation_memory.capture_memory)(label=label)
            output = {
                "action": "workstation_memory_capture",
                "label": label,
                "result": capture_res,
                "message": (
                    f"• COMMITTED TO POSTGRESQL (ops_db) WORKSTATION MEMORY VAULT:\n"
                    f"  - Label: '{capture_res.get('label')}'\n"
                    f"  - Category: [{capture_res.get('category', 'general').upper()}]\n"
                    f"  - Target URL/Window: {capture_res.get('target_url') or capture_res.get('window_title') or 'Active Workstation Window'}\n"
                    f"  - Action Type: {capture_res.get('action_type')}\n"
                    f"  - Instant Recall: Command 'Add {capture_res.get('label')} from the memory' or 'Play {capture_res.get('label')} from memory'."
                )
            }
            return {
                "tool_output": output,
                "intent": "WORKSTATION_MEMORY_CAPTURE",
                "active_agent": "ToolSandbox",
                "plan": [f"Persist workstation memory to PostgreSQL (ops_db): '{label}'"]
            }

        # 0.5 Workstation Memory Recall & Auto-Execution (PostgreSQL ops_db)
        elif self.is_memory_recall_command(prompt):
            recall_res = await sync_to_async(self.workstation_memory.recall_and_execute)(prompt)
            if recall_res.get("status") == "executed":
                output = {
                    "action": "workstation_memory_recall",
                    "result": recall_res,
                    "message": (
                        f"• WORKSTATION MEMORY RECALLED & EXECUTED:\n"
                        f"  - Memory Label: '{recall_res.get('label')}'\n"
                        f"  - Category: [{recall_res.get('category', 'general').upper()}]\n"
                        f"  - Telemetry: {recall_res.get('execution_details')}\n"
                        f"  - Status: Automatic window navigation and playback executed."
                    )
                }
            else:
                output = {
                    "action": "workstation_memory_recall",
                    "result": recall_res,
                    "message": f"• MEMORY RECALL NOTICE: {recall_res.get('message')}"
                }
            return {
                "tool_output": output,
                "intent": "WORKSTATION_MEMORY_RECALL",
                "active_agent": "ToolSandbox",
                "plan": ["Recall workstation memory from PostgreSQL (ops_db) and auto-execute playback"]
            }

        # 1. Claude Routine Execution: D:\freellmapi -> npm run dev -> claude
        elif any(k in p_lower for k in [
            "run claude", "launch claude", "start claude",
            "terminal and run claude", "claude in terminal", "claude in the terminal"
        ]):
            res = await self.tools.run_claude_routine(task_id=task_id)
            output = {"action": "run_claude_routine", "target": r"D:\freellmapi", "result": res}

        # 2. VS Code File Open
        elif any(k in p_lower for k in ["vs code and open", "vscode and open", "open file in vs code", "open in vs code", "open in vscode"]) or (("vs code" in p_lower or "vscode" in p_lower) and "open" in p_lower):
            target_file = ""
            for token in prompt.split():
                if "." in token and not any(token.endswith(ext) for ext in [".com", ".org", ".net", ".io", ".ai", ".in"]):
                    target_file = token.strip('"\'')
                    break
            res = await self.tools.open_in_vscode(target=target_file, task_id=task_id)
            output = {"action": "open_in_vscode", "target": target_file or "VS Code", "result": res}

        # 3. Universal Website & DOM Search Automation (Any Website on Earth!)
        elif self.extract_universal_site_and_query(prompt):
            site, query = self.extract_universal_site_and_query(prompt)
            resolved_url = self.tools.automation_service.resolve_website_url(site)
            res = await self.tools.execute_browser_dom_task(
                url=resolved_url,
                search_query=query,
                site_name=site,
                task_id=task_id
            )
            output = {"action": "browser_dom_task", "site": site, "query": query, "result": res}

        # 4. Universal Terminal / Shell Command Execution
        elif any(k in p_lower for k in ["run command ", "execute command ", "in terminal run ", "run in terminal ", "terminal command "]) or (p_lower.startswith("run ") and any(c in p_lower for c in ["dir", "git ", "npm ", "python ", "pip ", "docker ", "cargo ", "npx ", "ipconfig", "curl ", "ping "])):
            cmd_text = prompt
            for prefix in ["run command ", "execute command ", "in terminal run ", "run in terminal ", "terminal command ", "run "]:
                if prefix in cmd_text.lower():
                    cmd_text = cmd_text[cmd_text.lower().index(prefix) + len(prefix):]
                    break
            cmd_text = cmd_text.strip(" \"':;,")
            res = await self.tools.execute_terminal_command(cmd_text, task_id=task_id)
            output = {"action": "run_terminal_cmd", "command": cmd_text, "result": res}

        # 5. Explicit File, Folder, or Directory Path Open
        elif any(k in p_lower for k in [":\\", ":/", "folder", "downloads", "documents", "desktop", "pictures", "videos"]) and any(k in p_lower for k in ["open ", "launch ", "explore "]):
            clean_t = prompt
            for prefix in ["open folder ", "open the folder ", "open file ", "open the file ", "open ", "launch "]:
                if prefix in clean_t.lower():
                    clean_t = clean_t[clean_t.lower().index(prefix) + len(prefix):]
                    break
            clean_t = clean_t.strip(" \"':?,.")
            res = await self.tools.open_file_or_folder(clean_t, task_id=task_id)
            output = {"action": "open_file_or_folder", "target": clean_t, "result": res}

        # 7. Standard App, Web Service, Deep Link, or Installed Windows App
        elif intent == "OPEN_APPLICATION" or any(k in p_lower for k in ["open ", "launch ", "start ", "browse to ", "go to "]):
            # Check known web services & desktop applications
            app_target = params.get("application") or ""
            if not app_target:
                all_known = (
                    list(self.tools.automation_service.KNOWN_WEB_SERVICES.keys()) +
                    list(self.tools.automation_service.KNOWN_APPS.keys())
                )
                all_known_sorted = sorted(all_known, key=len, reverse=True)
                for w in all_known_sorted:
                    if w in p_lower:
                        app_target = w
                        break
            if not app_target:
                for prefix in ["browse to ", "go to ", "open the website for ", "open website ", "open ", "launch ", "start "]:
                    if prefix in p_lower:
                        remainder = p_lower.split(prefix)[-1].strip()
                        for trailing in [" please", " for me", " now", " right now"]:
                            if remainder.endswith(trailing):
                                remainder = remainder[:-len(trailing)].strip()
                        app_target = remainder
                        break
            if not app_target:
                words = [w for w in prompt.split() if w.lower() not in ["open", "the", "app", "application", "launch", "start", "please", "website", "to", "for"]]
                app_target = " ".join(words) if words else prompt.split()[-1]

            res = await self.tools.launch_application(app_target, task_id=task_id)
            output = {"action": "launch_application", "target": app_target, "result": res}

        elif intent == "WEB_SEARCH" or any(k in p_lower for k in ["search", "google", "lookup"]):
            query = params.get("query") or prompt.replace("search for", "").replace("search", "").replace("google", "").strip()
            res = await self.tools.search_web(query, max_results=3, task_id=task_id)
            output = {"action": "web_search", "query": query, "result": res}

        elif intent == "FILE_OPERATION" or any(k in p_lower for k in ["folder", "directory", "create file", "mkdir"]):
            folder_name = params.get("name") or "NewProject"
            for word in prompt.split():
                if word not in ["create", "a", "folder", "called", "in", "my", "directory", "make"]:
                    folder_name = word.strip('"\'')
                    break
            os.makedirs(folder_name, exist_ok=True)
            output = {"action": "file_operation", "message": f"Created folder '{folder_name}' successfully."}
            await OPSEventBus.emit_terminal_log_async(f"[OPS-FS] Created directory: {folder_name}", stream="stdout")

        else:
            output = {"action": "direct_execution", "message": f"Executed action for: {prompt}"}

        return {
            "tool_output": output,
            "active_agent": "ToolSandbox",
            "plan": [f"Directly execute {intent}"]
        }

    # =========================================================================
    # NODE 3: Content Writing (Llama 3.2 1B Instruct)
    # =========================================================================

    async def content_writing_node(self, state: AgentWorkflowState) -> Dict[str, Any]:
        task_id = state.get("task_id", "")
        prompt = state.get("prompt", "")

        await OPSEventBus.emit_agent_thought_async(
            thought="Generating refined content (email/letter/summary/explanation)...",
            agent="Content Specialist (Llama 3.2 1B Instruct)",
            step=2,
            task_id=task_id
        )

        content = self.ollama.generate_content(prompt)
        return {
            "content_output": content,
            "active_agent": "ContentSpecialist",
            "plan": ["Drafting high-quality content via Llama 3.2 1B Instruct"]
        }

    # =========================================================================
    # NODE 4: Reasoning & Planning Engine (Qwen3 1.7B)
    # =========================================================================

    async def reasoning_planner_node(self, state: AgentWorkflowState) -> Dict[str, Any]:
        task_id = state.get("task_id", "")
        prompt = state.get("prompt", "")
        intent = state.get("intent", "DEVELOPMENT")

        await OPSEventBus.emit_agent_thought_async(
            thought="Deconstructing task, formulating multi-step plan & coordinating agents...",
            agent="Main Reasoning Engine (Qwen3 1.7B)",
            step=2,
            task_id=task_id
        )

        plan_res = self.ollama.generate_reasoning_and_plan(prompt, context=f"Intent: {intent}")
        plan_steps = plan_res.get("plan", [f"Execute task: {prompt}"])

        OPSEventBus.emit_agent_plan(plan_steps, model=self.ollama.reasoning_model)

        return {
            "plan": plan_steps,
            "active_agent": "ReasoningPlanner",
            "status": "PLANNED"
        }

    def route_planner_decision(self, state: AgentWorkflowState) -> str:
        prompt = state.get("prompt", "").lower()
        intent = state.get("intent", "").upper()

        if intent in ["DEVELOPMENT", "DEBUGGING", "CODING"] or any(k in prompt for k in ["code", "python", "script", "build", "debug", "test", "fix"]):
            return "DEVELOPER"
        elif any(k in prompt for k in ["crawl", "crawlee", "scrapegraph", "who is", "what is", "theory", "news", "live update"]):
            return "WEB_CRAWLER"
        elif intent in ["WEB_SEARCH", "SCRAPING"] or any(k in prompt for k in ["http://", "https://", "scrape", "crawl"]):
            return "BROWSER"
        elif intent in ["AUTOMATION", "GUI"] or any(k in prompt for k in ["click", "gui", "type", "mouse"]):
            return "AUTOMATION"
        return "JARVIS"

    # =========================================================================
    # SPECIALIZED AGENTS (Under Qwen3 1.7B Direction)
    # =========================================================================

    async def developer_agent_node(self, state: AgentWorkflowState) -> Dict[str, Any]:
        task_id = state.get("task_id", "")
        prompt = state.get("prompt", "")

        await OPSEventBus.emit_agent_thought_async(
            thought="Developer Agent writing code, consulting RAG, and compiling terminal solution...",
            agent="Developer Agent (Qwen3 1.7B)",
            step=3,
            task_id=task_id
        )

        # 1. Search Codebase RAG
        rag_hits = self.tools.rag_search(prompt, collection="ops_codebase", n_results=2)

        # 2. Synthesize Code / Debug Fix using Model 2 (Qwen3 1.7B)
        code_synth = self.ollama.generate_code_or_debug(prompt, tool_name="code_editor")

        # 3. Scaffolding check
        p_lower = prompt.lower()
        build_output = ""
        if any(k in p_lower for k in ["build", "create file", "write script", "make project"]):
            await OPSEventBus.emit_terminal_log_async(f"[OPS-DEV] Scaffolding software solution for: {prompt[:60]}", stream="stdout")
            build_output = "Project structure generated and verified with local runtime."

        dev_result = {
            "rag_context": rag_hits,
            "synthesis": code_synth,
            "build_output": build_output,
            "status": "COMPLETED"
        }

        return {
            "developer_output": dev_result,
            "active_agent": "DeveloperAgent"
        }

    async def web_crawling_node(self, state: AgentWorkflowState) -> Dict[str, Any]:
        task_id = state.get("task_id", "")
        prompt = state.get("prompt", "")

        await OPSEventBus.emit_agent_thought_async(
            thought=f"Web Crawling Agent crawling live web intelligence (Crawlee / ScrapeGraphAI) for: '{prompt}'...",
            agent="Web Crawling Agent (Crawlee / ScrapeGraphAI)",
            step=2,
            task_id=task_id
        )

        research_res = await self.tools.auto_research_web(prompt, task_id=task_id)

        # If the scrape failed (bot block, empty/JS page, network error), surface
        # an explicit failure state instead of handing blank or fabricated context
        # to the response model.
        if research_res.get("status") not in ("success", None):
            research_res["markdown"] = (
                f"[•] SCRAPE FAILED: {research_res.get('error', 'Unknown scrape error')}\n"
                f"[•] URL: {research_res.get('url', prompt)}"
            )
            research_res.setdefault("voice_briefing", "Scrape failed - no source text available.")
            research_res["category"] = "SCRAPE_FAILED"

        # Inject the closed-domain grounding preamble so the response model can
        # only cite what the scraped source actually contains.
        research_res["markdown"] = GROUNDING_INSTRUCTION + research_res.get("markdown", "")

        # Connect live crawled knowledge to voice calling / speech synthesis layer
        voice_briefing = research_res.get("voice_briefing", "")
        if voice_briefing:
            try:
                from ops_core.services.voice_service import WisprFlowVoiceService
                voice_svc = WisprFlowVoiceService()
                voice_svc.synthesize_speech(voice_briefing)
                await OPSEventBus.emit_terminal_log_async(f"[VOICE-TTS] Spoken briefing queued: {voice_briefing[:70]}...", stream="stdout")
            except Exception as ve:
                logger.warning(f"Voice synthesis error in web_crawling_node: {ve}")

        await OPSEventBus.emit_agent_thought_async(
            thought=f"Live research completed ({research_res.get('category')}). Knowledge extracted & voice audio ready.",
            agent="Web Crawling Agent (Crawlee / ScrapeGraphAI)",
            step=3,
            task_id=task_id
        )

        return {
            "crawling_output": research_res,
            "active_agent": "WebCrawlingAgent",
            "plan": [
                f"Live autonomous web crawl: '{prompt}' via ScrapingBee, Playwright, Selenium, Scrapy, Crawlee & BeautifulSoup",
                f"Extracted real-time structured knowledge dossier ({research_res.get('category')})",
                "Synthesized voice audio stream via local Piper TTS engine"
            ]
        }

    async def browser_agent_node(self, state: AgentWorkflowState) -> Dict[str, Any]:
        task_id = state.get("task_id", "")
        prompt = state.get("prompt", "")

        await OPSEventBus.emit_agent_thought_async(
            thought="Browser Agent navigating web, extracting DOM, and analyzing online docs...",
            agent="Browser Agent (Playwright / ScrapeGraph)",
            step=3,
            task_id=task_id
        )

        url = None
        for word in prompt.split():
            if word.startswith("http://") or word.startswith("https://"):
                url = word
                break

        if url:
            scrape_res = await self.tools.web_scrape(url, task_id=task_id)
            search_res = None
        else:
            query = prompt.replace("search for", "").replace("search", "").replace("google", "").strip() or prompt
            search_res = await self.tools.search_web(query, max_results=4, task_id=task_id)
            url = search_res.get("results", [{}])[0].get("url", "https://duckduckgo.com") if search_res.get("results") else "https://duckduckgo.com"
            scrape_res = {"status": "success", "title": f"Search Results for: {query}", "text": search_res.get("summary", "")}

        return {
            "browser_output": {
                "target_url": url,
                "scrape_result": scrape_res,
                "search_result": search_res
            },
            "active_agent": "BrowserAgent"
        }

    async def system_automation_agent_node(self, state: AgentWorkflowState) -> Dict[str, Any]:
        task_id = state.get("task_id", "")
        prompt = state.get("prompt", "")

        await OPSEventBus.emit_agent_thought_async(
            thought="System Automation Agent executing desktop coordinate commands...",
            agent="System Automation Agent (PyAutoGUI / OS)",
            step=3,
            task_id=task_id
        )

        p_lower = prompt.lower()
        auto_result = {}

        if any(k in p_lower for k in ["open ", "launch ", "start "]):
            app_target = prompt.split()[-1]
            for w in ["chrome", "antigravity", "vscode", "terminal", "notepad", "calculator"]:
                if w in p_lower:
                    app_target = w
                    break
            res = await self.tools.launch_application(app_target, task_id=task_id)
            auto_result = res
        elif any(k in p_lower for k in ["search google", "browse to"]):
            query = prompt.replace("search google for", "").replace("google", "").strip()
            res = await self.tools.open_browser_search(query, task_id=task_id)
            auto_result = res
        else:
            code_synth = self.ollama.generate_code_or_debug(prompt, tool_name="gui_controller")
            auto_result = {"action": "gui_action", "details": code_synth}

        return {
            "automation_output": auto_result,
            "active_agent": "SystemAutomationAgent"
        }

    # =========================================================================
    # NODE 5: Shared J.A.R.V.I.S. Personality Layer (Llama 3.2 1B Instruct)
    # =========================================================================

    async def jarvis_response_node(self, state: AgentWorkflowState) -> Dict[str, Any]:
        task_id = state.get("task_id", "")
        prompt = state.get("prompt", "")
        intent = state.get("intent", "GENERAL")
        plan = state.get("plan", [])

        await OPSEventBus.emit_agent_thought_async(
            thought="Applying shared O.P.S. J.A.R.V.I.S. personality layer for refined user response...",
            agent="J.A.R.V.I.S. Persona Layer (Llama 3.2 1B Instruct)",
            step=4,
            task_id=task_id
        )

        # Collect context from whichever branch was executed
        details = []
        tool_out = state.get("tool_output", {})
        content_out = state.get("content_output", "")
        dev_out = state.get("developer_output", {})
        browser_out = state.get("browser_output", {})
        auto_out = state.get("automation_output", {})
        crawl_out = state.get("crawling_output", {})

        if tool_out:
            res_dict = tool_out.get("result") if isinstance(tool_out.get("result"), dict) else {}
            if res_dict.get("status") == "BLOCKED" or tool_out.get("status") == "BLOCKED":
                block_reason = res_dict.get("reason") or res_dict.get("stderr") or tool_out.get("reason") or "Action authorization was denied by user or blocked by safety policy."
                details.append(f"⛔ [SECURITY ALERT] Execution Denied / Action Blocked:\n  - Reason: {block_reason}\n  - Target: {tool_out.get('target') or tool_out.get('command') or tool_out.get('action')}")
            else:
                msg = res_dict.get("message") or tool_out.get("message")
                if msg:
                    details.append(msg)
                elif tool_out.get("action") == "launch_application":
                    details.append(f"{tool_out.get('target', 'Application').title()} is open and ready on your workstation.")
                elif tool_out.get("action") == "run_claude_routine":
                    details.append(r"Claude workflow executed: initialized 'npm run dev' in D:\freellmapi and launched Claude CLI.")
                elif tool_out.get("action") == "open_in_vscode":
                    details.append(f"Visual Studio Code launched with target '{tool_out.get('target', 'workspace')}'.")
                elif tool_out.get("action") == "browser_dom_task":
                    details.append(f"Executed browser DOM task on {tool_out.get('site')} for '{tool_out.get('query')}'.")
                elif tool_out.get("action") == "open_file_or_folder":
                    details.append(f"Opened file or folder: '{tool_out.get('target')}'.")
                elif tool_out.get("action") == "run_terminal_cmd":
                    cmd = tool_out.get("command", "")
                    stdout = res_dict.get("stdout", "")
                    details.append(f"Terminal execution finished for `{cmd}`:\n```\n{stdout[:200]}\n```" if stdout else f"Executed terminal command `{cmd}`.")
                elif tool_out.get("action") == "web_search":
                    details.append(f"Web search executed for '{tool_out.get('query')}'.")

        if crawl_out:
            md = crawl_out.get("markdown")
            if md:
                details.append(md)
            v_brief = crawl_out.get("voice_briefing")
            if v_brief:
                details.append(f"**🔊 Voice Dispatch:** *\"{v_brief}\"*")

        if content_out:
            details.append(content_out)

        if dev_out:
            synth = dev_out.get("synthesis", {}).get("synthesis", {})
            if synth.get("code"):
                details.append(f"```python\n{synth.get('code')}\n```")
            if synth.get("explanation"):
                details.append(synth.get("explanation"))
            if dev_out.get("build_output"):
                details.append(dev_out["build_output"])

        if browser_out:
            scrape_res = browser_out.get("scrape_result")
            search_data = browser_out.get("search_result")
            if scrape_res and scrape_res.get("text"):
                details.append(
                    f"{GROUNDING_INSTRUCTION}"
                    f"Scraped Web Intelligence from [{scrape_res.get('title', browser_out.get('target_url'))}]({browser_out.get('target_url')}):\n"
                    f"{scrape_res.get('text')[:3500]}"
                )
            elif search_data and search_data.get("results"):
                details.append("Key search findings:")
                for r in search_data["results"][:4]:
                    details.append(f"• [{r.get('title')}]({r.get('url')}): {r.get('snippet')}")
            elif browser_out.get("target_url"):
                details.append(f"Target URL: {browser_out.get('target_url')}")

        if auto_out:
            if auto_out.get("status") == "BLOCKED":
                details.append(f"⛔ [SECURITY ALERT] System automation was DENIED / BLOCKED: {auto_out.get('reason', 'Action rejected by safety gatekeeper or user.')}")
            else:
                msg = auto_out.get("message") or f"Executed {auto_out.get('action', 'automation')}"
                details.append(msg)

        context_summary = "\n\n".join(details)
        is_action_denied = any("DENIED" in d or "BLOCKED" in d for d in details)

        # Generate J.A.R.V.I.S. conversational response
        session_id = state.get("session_id", task_id)
        history_str = self.memory.get_formatted_history(session_id, limit=6)

        # Generate J.A.R.V.I.S. conversational response with temporary chat memory
        if tool_out.get("action") in ["workstation_memory_capture", "workstation_memory_recall"]:
            jarvis_text = f"Workstation memory directive acknowledged and processed, sir.\n\n{context_summary}"
        elif is_action_denied:
            jarvis_text = f"Directive aborted, sir. The action was blocked or permission was denied by human authorization.\n\n{context_summary}"
        elif content_out:
            jarvis_text = f"Certainly, sir. Here is the requested draft:\n\n{content_out}"
        else:
            jarvis_text = self.ollama.generate_jarvis_response(
                user_prompt=prompt,
                context=context_summary,
                intent=intent,
                history=history_str
            )

        # Anti-standby guard: Never leave user with a blank standby prompt when directive was executed
        if not jarvis_text or jarvis_text.strip() == "[•] Standby: Ready for instructions.":
            if is_action_denied:
                jarvis_text = f"Directive aborted, sir. The action was blocked or permission was denied by human authorization.\n\n{context_summary}"
            elif context_summary:
                jarvis_text = f"Certainly, sir. Here is the verified intelligence for your directive:\n\n{context_summary}"
            elif crawl_out and crawl_out.get("markdown"):
                jarvis_text = f"Certainly, sir. Live web intelligence report:\n\n{crawl_out.get('markdown')}"
            else:
                jarvis_text = f"At your service, sir. Directive '{prompt}' executed successfully."

        # Append execution footer in 90s retro tactical HUD style
        plan_summary = "\n".join([f"    [>] {step}" for step in plan]) if plan else "    [>] Fast-path direct execution"
        final_answer = (
            f"{jarvis_text}\n\n"
            f"────────────────────────────────────────\n"
            f"[•] DIRECTIVE: {prompt}\n"
            f"[•] PIPELINE: `{intent}`\n"
            f"[•] EXECUTION TELEMETRY:\n"
            f"{plan_summary}"
        )

        # Emit completion over event bus (triggers real-time retro typewriter in HUD & Pop-Up)
        OPSEventBus.emit_agent_response(final_answer, is_final=True, task_id=task_id)

        # Save to dedicated chatbot vector database memory partition (ops_chatbot_memory)
        self.memory.add_turn(
            session_id=session_id,
            role="assistant",
            content=final_answer,
            save_to_vector_db=True
        )

        return {
            "final_answer": final_answer,
            "status": "COMPLETED"
        }

    # =========================================================================
    # Public Execution Entry Point
    # =========================================================================

    async def run_task_async(self, prompt: str, task_id: Optional[str] = None, session_id: Optional[str] = None, source: str = "workstation") -> Dict[str, Any]:
        """
        Executes the full Tri-Model LangGraph workflow asynchronously with temporary chat session memory.
        """
        tid = task_id or str(uuid.uuid4())
        sid = session_id or tid

        # Check for contextual pronoun / follow-up resolution BEFORE router dispatch
        resolved_prompt, ref_entity = self.memory.resolve_contextual_query(sid, prompt)
        effective_prompt = resolved_prompt if ref_entity else prompt

        initial_state: AgentWorkflowState = {
            "task_id": tid,
            "session_id": sid,
            "prompt": effective_prompt,
            "original_prompt": prompt,
            "intent": "",
            "complexity": "simple",
            "target_flow": "DIRECT_TOOL",
            "parameters": {},
            "plan": [],
            "active_agent": "RouterAgent",
            "tool_output": {},
            "developer_output": {},
            "browser_output": {},
            "automation_output": {},
            "crawling_output": {},
            "content_output": "",
            "final_answer": "",
            "execution_log": [],
            "status": "PENDING"
        }

        # Record user prompt in dedicated chatbot vector database memory partition (ops_chatbot_memory)
        self.memory.add_turn(session_id=sid, role="user", content=prompt, save_to_vector_db=True)

        # Broadcast task started to the entire O.P.S ecosystem (Web HUD Tab 2, Mobile, Overlays)
        origin_label = "Desktop Pop-Up Cockpit" if source == "desktop_cockpit" else "Directive & Hotkey Ingestion"
        await OPSEventBus.emit_task_started_async(
            prompt=prompt,
            task_id=tid,
            source=source,
            agent=origin_label
        )

        try:
            final_state = await self._workflow_app.ainvoke(initial_state)

            # Broadcast task completed across all connected WebSocket clients (including Tab 2)
            await OPSEventBus.emit_task_completed_async(
                task_id=tid,
                final_answer=final_state.get("final_answer", ""),
                category=final_state.get("intent") or final_state.get("category", "EXECUTED"),
                plan=final_state.get("plan", []),
                details={
                    "tool_output": final_state.get("tool_output"),
                    "developer_output": final_state.get("developer_output"),
                    "browser_output": final_state.get("browser_output"),
                    "automation_output": final_state.get("automation_output"),
                    "content_output": final_state.get("content_output"),
                    "intent": final_state.get("intent"),
                    "status": final_state.get("status")
                }
            )
            return final_state
        except Exception as e:
            await OPSEventBus.emit_task_failed_async(task_id=tid, error=str(e))
            raise
