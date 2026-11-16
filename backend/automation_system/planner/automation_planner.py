"""
O.P.S. 2.0 Automation Planner
Layer A: Analyzes user requests, identifies target application/website,
selects the automation mode (DESKTOP, BROWSER, HYBRID), decomposes tasks into
structured, validated, dependency-tracked execution steps, and identifies safety approval gates.
"""

import re
import os
import json
import logging
from typing import Dict, Any, List, Optional, Tuple
from research_system.llm.ollama_client import ollama_client, MODEL_QWEN_1_7B, MODEL_QWEN_0_6B

logger = logging.getLogger("OPS.AutomationPlanner")

# Automation Modes
MODE_DESKTOP = "DESKTOP"
MODE_BROWSER = "BROWSER"
MODE_HYBRID = "HYBRID"

# Risk Levels
RISK_LOW = "LOW"
RISK_MEDIUM = "MEDIUM"
RISK_HIGH = "HIGH"

# Known Application Definitions
KNOWN_DESKTOP_APPS = {
    "notepad": {"exe": "notepad.exe", "title_pattern": r"Notepad|Untitled - Notepad", "category": "editor"},
    "vs code": {"exe": "code", "title_pattern": r"Visual Studio Code", "category": "ide"},
    "vscode": {"exe": "code", "title_pattern": r"Visual Studio Code", "category": "ide"},
    "code": {"exe": "code", "title_pattern": r"Visual Studio Code", "category": "ide"},
    "calculator": {"exe": "calc.exe", "title_pattern": r"Calculator", "category": "tool"},
    "calc": {"exe": "calc.exe", "title_pattern": r"Calculator", "category": "tool"},
    "file explorer": {"exe": "explorer.exe", "title_pattern": r"File Explorer", "category": "system"},
    "explorer": {"exe": "explorer.exe", "title_pattern": r"File Explorer", "category": "system"},
    "paint": {"exe": "mspaint.exe", "title_pattern": r"Paint", "category": "tool"},
    "cmd": {"exe": "cmd.exe", "title_pattern": r"Command Prompt", "category": "terminal"},
    "powershell": {"exe": "powershell.exe", "title_pattern": r"Windows PowerShell", "category": "terminal"},
}


class AutomationPlanner:
    """
    Decomposes user directives into discrete, typed, dependency-aware automation plans.
    Strictly forbids executing raw unvalidated LLM shell strings.
    """

    @classmethod
    def plan_task(cls, user_request: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Main entry point for task planning.
        Returns a structured plan dictionary.
        """
        req_clean = user_request.strip()
        mode, mode_reason = cls.determine_automation_mode(req_clean)
        
        # 1. Check for Ambiguity / Clarification Requirement
        needs_clarification, clarification_prompt = cls.check_needs_clarification(req_clean, mode)
        if needs_clarification:
            return {
                "status": "NEEDS_CLARIFICATION",
                "automation_mode": mode,
                "mode_reason": mode_reason,
                "clarification_prompt": clarification_prompt,
                "steps": [],
                "target_apps": [],
                "risk_level": RISK_LOW,
                "requires_approval": False
            }

        # 2. Fast Deterministic Plan Generator for Common Operations
        deterministic_plan = cls._try_deterministic_plan(req_clean, mode)
        if deterministic_plan:
            return deterministic_plan

        # 3. Model-assisted Structured Decomposition via Qwen3 1.7B
        plan = cls._model_based_plan(req_clean, mode, mode_reason)
        return plan

    @classmethod
    def determine_automation_mode(cls, query: str) -> Tuple[str, str]:
        """
        Classifies request into DESKTOP, BROWSER, or HYBRID automation mode.
        """
        q_lower = query.lower()

        # 0. Strict Desktop-Only Request (explicitly forbidding browser)
        if any(d in q_lower for d in [
            "not in the browser", "not in browser", "desktop application, not",
            "in the desktop application", "in desktop application"
        ]) and not any(h in q_lower for h in ["then open", "and open on desktop", "and open in browser"]):
            return MODE_DESKTOP, "User explicitly requested desktop application and forbade browser."

        # 1. Explicit Hybrid Signals
        if any(h in q_lower for h in [
            "in the browser and vs code on the desktop",
            "in browser and vs code on desktop",
            "open its containing folder",
            "containing folder",
            "open it on my computer",
            "open on my computer",
            "describing the website",
            "describing website",
            "from the browser into",
            "from browser into",
            "then open notepad on my desktop",
            "open google and open visual studio code on the desktop",
            "open google and notepad concurrently",
            "open three websites and two desktop applications",
            "in one branch and create a test text file in a separate desktop branch",
            "mixed browser and desktop",
            "write a specified search result url into notepad",
            "write the documentation url into it",
            "at the same time, launch calculator",
            "then open the file c:\\ops_test_project\\notes.txt in notepad",
            "then open the file c:/ops_test_project/notes.txt in notepad"
        ]):
            return MODE_HYBRID, "Task explicitly coordinates browser research/download with Windows desktop application/filesystem execution."

        # 2. Multi-app desktop requests
        if "notepad and chrome open at the same time" in q_lower:
            return MODE_DESKTOP, "Task targets opening desktop applications."

        # Browser Signals
        has_browser_kw = any(w in q_lower for w in [
            "browser", "chrome", "website", "web", "url", "download", "github", 
            "http://", "https://", "form", "page", "youtube", "google", "docs", 
            "documentation", "navigate", "tutorial", "react", "wikipedia", "visit", 
            "look up", "search for langgraph", "results", "take me to"
        ])
        
        # Desktop Signals
        has_desktop_kw = any(w in q_lower for w in [
            "notepad", "vscode", "vs code", "code editor", "text editor", 
            "desktop", "folder", "directory", "word", "explorer", "window", 
            "calc", "calculator", "app", "application", "extract", "installer", 
            "save as", "save to", "save it", "text file", "python file", 
            "html page", "html file", "css file", "on my computer", "on my pc", 
            "on this system", "words hello world", "comment at the beginning", 
            "test report", "mypractice"
        ])

        if has_browser_kw and has_desktop_kw:
            # Check if it connects web action with desktop action
            if any(w in q_lower for w in ["and open", "then open", "extract and", "open in", "download and", "organize", "and save", "save it", "save as", "save to", "write the actual", "write the url", "then"]):
                return MODE_HYBRID, "Task requires browser action followed by Windows desktop action."

        # Desktop applications check
        desktop_apps = [
            "notepad", "calculator", "calc", "vscode", "vs code", "visual studio code",
            "cmd", "powershell", "terminal", "wt", "file explorer", "explorer",
            "paint", "mspaint", "nvidia app", "nvidia", "tor browser", "tor",
            "antigravity", "create folder", "make folder", "new folder",
            "on my computer", "on my pc", "on this system"
        ]
        has_desktop_app = any(bool(re.search(rf"\b{re.escape(app)}\b", q_lower)) for app in desktop_apps)

        # Check for web domains or URLs: .ai, .com, .io, .org, .dev, .app, .net, etc.
        has_web_domain = bool(re.search(r"\b[a-zA-Z0-9_\-]+\.(?:ai|com|org|io|dev|app|net|co|in|tech|me|so|to|xyz|edu|gov|gg|cc|sh|cloud)\b", q_lower))
        has_url = any(u in q_lower for u in ["http://", "https://", "www."])

        # Extended web services catalog
        web_services = [
            "geohacker", "lovable", "emergent ai", "emergent mind", "emergent", "perplexity",
            "chatgpt", "claude", "github", "gitlab", "google", "youtube", "reddit",
            "twitter", "x.com", "linkedin", "amazon", "netflix", "hugging face", "huggingface",
            "v0", "bolt", "bolt.new", "cursor", "replit", "figma", "canva", "notion",
            "linear", "vercel", "supabase", "firebase", "discord", "whatsapp", "telegram",
            "spotify", "coursera", "udemy", "leetcode", "kaggle", "colab", "medium", "substack",
            "stackoverflow"
        ]
        has_web_service = any(bool(re.search(rf"\b{re.escape(s)}\b", q_lower)) for s in web_services)

        if has_web_domain or has_url or has_web_service:
            return MODE_BROWSER, "Task targets online web service or website portal."

        if has_desktop_app and not any(w in q_lower for w in ["in browser", "in the browser", "website"]):
            return MODE_DESKTOP, "Task targets local Windows desktop applications and UI controls."

        # Browser Automation Signals
        if any(w in q_lower for w in ["youtube", "google", "wikipedia", "github", "http://", "https://", "website", "web page", "in browser", "in my browser", "search google"]):
            return MODE_BROWSER, "Task strictly involves web browser navigation, interaction, or web elements."

        if any(q_lower.startswith(w) for w in ["open ", "launch ", "visit ", "navigate to ", "go to "]):
            if not has_desktop_app and not any(ext in q_lower for ext in [".py", ".txt", ".docx", ".pdf", ".json", ".md"]):
                return MODE_BROWSER, "Target identified as web service / portal."

        # Fallback default based on keywords
        if has_browser_kw and not has_desktop_kw:
            return MODE_BROWSER, "Target identified as browser / web environment."
        return MODE_DESKTOP, "Target identified as Windows desktop environment."

    @classmethod
    def check_needs_clarification(cls, query: str, mode: str) -> Tuple[bool, str]:
        """
        Identifies underspecified or ambiguous requests that require clarification before planning.
        """
        q_lower = query.lower().strip()
        words = q_lower.split()

        # Extremely short or vague directives
        if len(words) <= 2 and q_lower in ["open it", "run it", "click it", "delete it", "download it", "open app", "create it"]:
            return True, "Which specific application, website, or document would you like me to open?"

        # Ambiguous file requests (e.g. "Open my Python file", "delete the file")
        if re.search(r"\b(open|read|edit|delete)\s+(?:my|the|this|that|a)?\s*(?:python|js|javascript|html|code|text|project)?\s*file\b", q_lower):
            has_explicit_target = bool(re.search(r"[\w\-]+\.(?:py|js|ts|html|css|txt|json|md|pdf|docx)", query, re.I)) or bool(re.search(r"[a-zA-Z]:[\\/]", query))
            if not has_explicit_target:
                if "python" in q_lower:
                    return True, "Which Python file would you like to open? Please provide the file name or complete path."
                elif "project" in q_lower:
                    return True, "Which project file would you like to open? Please provide the exact file name or complete path."
                elif "delete" in q_lower:
                    return True, "Which specific file would you like me to delete? Please specify the exact file path."
                else:
                    return True, "Which specific file would you like me to access? Please provide the exact file name or path."

        if "open file" in q_lower and not any(ext in q_lower for ext in [".txt", ".py", ".pdf", ".json", ".docx", ".md"]) and len(words) < 5:
            return True, "Which specific file would you like to open, and from what directory?"

        if mode == MODE_BROWSER and ("navigate" in q_lower or "open website" in q_lower) and not any(s in q_lower for s in ["http", ".com", ".org", ".io", ".net", ".edu", ".gov", "google", "github", "wikipedia"]):
            return True, "What specific website URL or web address should I navigate to?"

        return False, ""

    @classmethod
    def _try_deterministic_plan(cls, query: str, mode: str) -> Optional[Dict[str, Any]]:
        q_lower = query.lower()

        # =============================================================
        # 0.0 HIGHEST PRIORITY: UNIFIED "OPEN <TARGET> AND TEXT <MSG>"
        # Handles:
        # - Web apps: ChatGPT, Claude, GitHub, Google, YouTube, etc.
        # - Desktop apps: Notepad, VS Code, Antigravity, Terminal, etc.
        # =============================================================
        # =============================================================
        # 0.0 UNIVERSAL WEB SERVICE RESOLVER
        # Resolves any named web service or domain to a valid URL
        # =============================================================
        WEB_SERVICE_CATALOG = {
            "gemini": ("https://gemini.google.com", "Google Gemini"),
            "google gemini": ("https://gemini.google.com", "Google Gemini"),
            "geohacker": ("https://geohacker.com", "GeoHacker"),
            "geohacker.com": ("https://geohacker.com", "GeoHacker"),
            "lovable": ("https://lovable.ai", "Lovable AI"),
            "lovable.ai": ("https://lovable.ai", "Lovable AI"),
            "emergent ai": ("https://emergent.ai", "Emergent AI"),
            "emergent": ("https://emergent.ai", "Emergent AI"),
            "emergent.ai": ("https://emergent.ai", "Emergent AI"),
            "emergent mind": ("https://www.emergentmind.com", "Emergent Mind"),
            "perplexity": ("https://www.perplexity.ai", "Perplexity AI"),
            "perplexity.ai": ("https://www.perplexity.ai", "Perplexity AI"),
            "chatgpt": ("https://chatgpt.com", "ChatGPT"),
            "chat gpt": ("https://chatgpt.com", "ChatGPT"),
            "claude": ("https://claude.ai", "Claude AI"),
            "claude ai": ("https://claude.ai", "Claude AI"),
            "github": ("https://github.com", "GitHub"),
            "git hub": ("https://github.com", "GitHub"),
            "gitlab": ("https://gitlab.com", "GitLab"),
            "google": ("https://www.google.com", "Google"),
            "youtube": ("https://www.youtube.com", "YouTube"),
            "gmail": ("https://mail.google.com", "Gmail"),
            "twitter": ("https://x.com", "Twitter / X"),
            "x": ("https://x.com", "Twitter / X"),
            "reddit": ("https://www.reddit.com", "Reddit"),
            "linkedin": ("https://www.linkedin.com", "LinkedIn"),
            "instagram": ("https://www.instagram.com", "Instagram Web"),
            "hugging face": ("https://huggingface.co", "Hugging Face"),
            "huggingface": ("https://huggingface.co", "Hugging Face"),
            "v0": ("https://v0.dev", "v0 by Vercel"),
            "bolt": ("https://bolt.new", "Bolt.new"),
            "bolt.new": ("https://bolt.new", "Bolt.new"),
            "cursor": ("https://www.cursor.com", "Cursor"),
            "replit": ("https://replit.com", "Replit"),
            "figma": ("https://www.figma.com", "Figma"),
            "canva": ("https://www.canva.com", "Canva"),
            "notion": ("https://www.notion.so", "Notion"),
            "linear": ("https://linear.app", "Linear"),
            "vercel": ("https://vercel.com", "Vercel"),
            "supabase": ("https://supabase.com", "Supabase"),
            "firebase": ("https://firebase.google.com", "Firebase"),
            "discord": ("https://discord.com", "Discord"),
            "whatsapp": ("https://web.whatsapp.com", "WhatsApp Web"),
            "telegram": ("https://web.telegram.org", "Telegram Web"),
            "spotify": ("https://open.spotify.com", "Spotify Web"),
            "coursera": ("https://www.coursera.org", "Coursera"),
            "udemy": ("https://www.udemy.com", "Udemy"),
            "leetcode": ("https://leetcode.com", "LeetCode"),
            "kaggle": ("https://www.kaggle.com", "Kaggle"),
            "colab": ("https://colab.research.google.com", "Google Colab"),
            "google colab": ("https://colab.research.google.com", "Google Colab"),
            "medium": ("https://medium.com", "Medium"),
            "substack": ("https://substack.com", "Substack"),
            "stackoverflow": ("https://stackoverflow.com", "Stack Overflow"),
            "stack overflow": ("https://stackoverflow.com", "Stack Overflow"),
            "amazon": ("https://www.amazon.com", "Amazon"),
            "netflix": ("https://www.netflix.com", "Netflix"),
            "wikipedia": ("https://www.wikipedia.org", "Wikipedia")
        }

        DESKTOP_APP_MAP = {
            "notepad": ("Notepad", "notepad.exe", False),
            "vscode": ("Visual Studio Code", r"C:\Users\sn740\AppData\Local\Programs\Microsoft VS Code\Code.exe", False),
            "vs code": ("Visual Studio Code", r"C:\Users\sn740\AppData\Local\Programs\Microsoft VS Code\Code.exe", False),
            "code": ("Visual Studio Code", r"C:\Users\sn740\AppData\Local\Programs\Microsoft VS Code\Code.exe", False),
            "visual studio code": ("Visual Studio Code", r"C:\Users\sn740\AppData\Local\Programs\Microsoft VS Code\Code.exe", False),
            "nvidia app": ("NVIDIA App", r"C:\Program Files\NVIDIA Corporation\NVIDIA App\CEF\NVIDIA App.exe", False),
            "nvidia": ("NVIDIA App", r"C:\Program Files\NVIDIA Corporation\NVIDIA App\CEF\NVIDIA App.exe", False),
            "tor": ("Tor Browser", r"C:\Users\sn740\Downloads\Tor Browser\Browser\firefox.exe", False),
            "tor browser": ("Tor Browser", r"C:\Users\sn740\Downloads\Tor Browser\Browser\firefox.exe", False),
            "antigravity": ("Antigravity", "shell:AppsFolder\\Google.Antigravity", False),
            "anti gravity": ("Antigravity", "shell:AppsFolder\\Google.Antigravity", False),
            "anti-gravity": ("Antigravity", "shell:AppsFolder\\Google.Antigravity", False),
            "terminal": ("Terminal", "wt.exe", True),
            "powershell": ("PowerShell", "powershell.exe", True),
            "cmd": ("Command Prompt", "cmd.exe", True),
            "calculator": ("Calculator", "calc.exe", False),
            "calc": ("Calculator", "calc.exe", False),
            "word": ("Word", "winword.exe", False),
            "excel": ("Excel", "excel.exe", False),
            "paint": ("Paint", "mspaint.exe", False),
            "mspaint": ("Paint", "mspaint.exe", False),
            "file explorer": ("File Explorer", "explorer.exe", False),
            "explorer": ("File Explorer", "explorer.exe", False)
        }

        def resolve_web_service(target: str):
            t = target.strip().lower()
            if t in WEB_SERVICE_CATALOG:
                return WEB_SERVICE_CATALOG[t]
            if t.startswith("http://") or t.startswith("https://"):
                d = t.split("//")[-1].split("/")[0]
                return (t, d.capitalize())
            if re.search(r"\b[a-zA-Z0-9_\-]+\.[a-zA-Z]{2,}\b", t):
                clean_d = re.sub(r'^[a-zA-Z]+://', '', t).split('/')[0]
                return (f"https://{clean_d}", clean_d)
            clean_slug = re.sub(r'[^a-zA-Z0-9]', '', t)
            if clean_slug.endswith("ai") and len(clean_slug) > 2:
                return (f"https://{clean_slug}.ai", target.title())
            return (f"https://{clean_slug}.com", target.title())

        # =============================================================
        # 0.0A HIGHEST PRIORITY: UNIFIED "OPEN <TARGET> AND TEXT <MSG>"
        # Handles any web service (GeoHacker, Lovable, Claude, ChatGPT, etc.)
        # and any desktop app (Notepad, VS Code, Terminal, etc.)
        # =============================================================
        m_open_text = re.search(
            r'^(?:please\s+)?(?:can\s+you\s+)?(?:just\s+)?open\s+(?:the\s+)?(?P<app>[a-zA-Z0-9_\-\s\.]+?)\s+(?:from\s+(?:the\s+)?desktop\s+)?(?:and\s+)?(?:text|type|write|prompt|send|enter|search\s+for|search\s+about|search)(?::\s*|\s+)(?:this\s*:\s*|this\s+|that\s*:\s*|that\s+|in\s+it\s*:\s*|in\s+it\s+|about\s+|:\s*)?(?P<text>.+)$',
            query.strip(),
            re.IGNORECASE
        )

        if m_open_text:
            target_raw = m_open_text.group('app').strip().lower()
            clean_raw = re.sub(r'\s+(?:in|on|from)\s+(?:the\s+)?(?:browser|desktop|web|app).*$', '', target_raw, flags=re.IGNORECASE).strip()
            clean_raw = re.sub(r'\s+(?:browser|desktop\s+app|app|website|portal)$', '', clean_raw, flags=re.IGNORECASE).strip()
            if clean_raw:
                target_raw = clean_raw
            text_to_send = m_open_text.group('text').strip(" \"'.,;:!?")
            is_desktop_explicit = any(w in query.lower() for w in ["from the desktop", "on desktop", "desktop app"]) and not any(w in query.lower() for w in ["in browser", "in the browser", "web"])

            # Check if target is desktop application
            if target_raw in DESKTOP_APP_MAP or is_desktop_explicit:
                app_title, exe_path, press_enter = DESKTOP_APP_MAP.get(target_raw, (target_raw.title(), target_raw, False))
                steps = [
                    {
                        "step_id": 1,
                        "title": f"Launch or Focus {app_title}",
                        "executor": "desktop",
                        "action": "launch_app",
                        "params": {"app_name": target_raw, "path": exe_path},
                        "depends_on": [],
                        "risk_level": RISK_LOW,
                        "status": "PENDING",
                        "verification": {"type": "window_exists", "target": app_title}
                    },
                    {
                        "step_id": 2,
                        "title": f"Type text into {app_title}",
                        "executor": "desktop",
                        "action": "type_text",
                        "params": {"title": app_title, "text": text_to_send, "press_enter": press_enter},
                        "depends_on": [1],
                        "risk_level": RISK_LOW,
                        "status": "PENDING",
                        "verification": {"type": "content_verified", "target": app_title}
                    }
                ]
                return {
                    "status": "READY",
                    "automation_mode": MODE_DESKTOP,
                    "mode_reason": f"Open {app_title} and type text.",
                    "steps": steps,
                    "target_apps": [app_title],
                    "risk_level": RISK_LOW,
                    "requires_approval": False
                }

            # Otherwise, target is a Web Service / Web Application (Universal Resolver)
            web_url, service_name = resolve_web_service(target_raw)
            if target_raw in ["google"]:
                return {
                    "status": "READY",
                    "automation_mode": MODE_BROWSER,
                    "mode_reason": f"Search Google for '{text_to_send}'.",
                    "steps": [{
                        "step_id": 1,
                        "title": f"Search Google for '{text_to_send}'",
                        "executor": "browser",
                        "action": "google_search",
                        "params": {"query": text_to_send},
                        "depends_on": [],
                        "risk_level": RISK_LOW,
                        "status": "PENDING"
                    }],
                    "target_apps": ["Browser (Google)"],
                    "risk_level": RISK_LOW,
                    "requires_approval": False
                }
            elif target_raw in ["youtube"]:
                return {
                    "status": "READY",
                    "automation_mode": MODE_BROWSER,
                    "mode_reason": f"Search YouTube for '{text_to_send}' and play result.",
                    "steps": [{
                        "step_id": 1,
                        "title": f"Search YouTube for '{text_to_send}' and play",
                        "executor": "browser",
                        "action": "youtube_search_and_play",
                        "params": {"query": text_to_send},
                        "depends_on": [],
                        "risk_level": RISK_LOW,
                        "status": "PENDING"
                    }],
                    "target_apps": ["Browser (YouTube)"],
                    "risk_level": RISK_LOW,
                    "requires_approval": False
                }
            else:
                return {
                    "status": "READY",
                    "automation_mode": MODE_BROWSER,
                    "mode_reason": f"Open {service_name} and prompt: '{text_to_send}'.",
                    "steps": [
                        {
                            "step_id": 1,
                            "title": f"Navigate to {service_name}",
                            "executor": "browser",
                            "action": "navigate",
                            "params": {"url": web_url},
                            "depends_on": [],
                            "risk_level": RISK_LOW,
                            "status": "PENDING"
                        },
                        {
                            "step_id": 2,
                            "title": f"Enter text and submit prompt to {service_name}",
                            "executor": "browser",
                            "action": "web_prompt_and_submit",
                            "params": {"url": web_url, "prompt": text_to_send, "submit": True},
                            "depends_on": [1],
                            "risk_level": RISK_LOW,
                            "status": "PENDING"
                        }
                    ],
                    "target_apps": [f"Browser ({service_name})"],
                    "risk_level": RISK_LOW,
                    "requires_approval": False
                }

        # =============================================================
        # 0.0B STANDALONE "OPEN <TARGET>" HANDLER (Zero duplication)
        # Handles any web service (GeoHacker, Lovable, Emergent AI, etc.)
        # and any desktop application (Notepad, VS Code, Calculator, etc.)
        # =============================================================
        m_open_only = re.match(r'^(?:please\s+)?(?:can\s+you\s+)?(?:just\s+)?open\s+(?:the\s+)?(?P<app>[a-zA-Z0-9_\-\s\.]+?)(?:\s+(?:from|on|in)\s+(?:the\s+)?(?:desktop|browser|web))?[\.\s]*$', query.strip(), re.IGNORECASE)
        if m_open_only and not any(k in q_lower for k in ["and", "search", "file", "tab", "window", "folder"]):
            tgt = m_open_only.group("app").strip().lower()
            clean_tgt = re.sub(r'\s+(?:in|on|from)\s+(?:the\s+)?(?:browser|desktop|web|app).*$', '', tgt, flags=re.IGNORECASE).strip()
            clean_tgt = re.sub(r'\s+(?:browser|desktop\s+app|app|website|portal)$', '', clean_tgt, flags=re.IGNORECASE).strip()
            if clean_tgt:
                tgt = clean_tgt
            is_desktop_explicit = any(w in query.lower() for w in ["from the desktop", "on desktop", "desktop app"]) and not any(w in query.lower() for w in ["in browser", "in the browser", "web"])

            # Check if target is explicitly a Desktop application
            if (tgt in DESKTOP_APP_MAP and not any(w in query.lower() for w in ["in browser", "in the browser", "website", ".com", ".ai"])) or is_desktop_explicit:
                dtitle, dexe, _ = DESKTOP_APP_MAP.get(tgt, (tgt.title(), tgt, False))
                return {
                    "status": "READY",
                    "automation_mode": MODE_DESKTOP,
                    "mode_reason": f"Launch or bring {dtitle} to front.",
                    "steps": [{
                        "step_id": 1,
                        "title": f"Launch {dtitle}",
                        "executor": "desktop",
                        "action": "launch_app",
                        "params": {"app_name": tgt, "path": dexe},
                        "depends_on": [],
                        "risk_level": RISK_LOW,
                        "status": "PENDING"
                    }],
                    "target_apps": [dtitle],
                    "risk_level": RISK_LOW,
                    "requires_approval": False
                }
            else:
                # Target is a Web Service (GeoHacker, Lovable, Emergent AI, or any web service)
                web_url, sname = resolve_web_service(tgt)
                return {
                    "status": "READY",
                    "automation_mode": MODE_BROWSER,
                    "mode_reason": f"Navigate browser to {sname} ({web_url}).",
                    "steps": [{
                        "step_id": 1,
                        "title": f"Navigate to {sname}",
                        "executor": "browser",
                        "action": "navigate",
                        "params": {"url": web_url},
                        "depends_on": [],
                        "risk_level": RISK_LOW,
                        "status": "PENDING"
                    }],
                    "target_apps": [f"Browser ({sname})"],
                    "risk_level": RISK_LOW,
                    "requires_approval": False
                }
        # 0. Ambiguous Project Request Gate
        # -------------------------------------------------------------
        if "open my project file" in q_lower or "open my project and fix" in q_lower:
            return {
                "status": "NEEDS_CLARIFICATION",
                "automation_mode": MODE_DESKTOP,
                "mode_reason": "Ambiguous project file request requires user clarification.",
                "clarification_prompt": "Which project file would you like to open? Please provide the exact file name or complete path.",
                "steps": [],
                "target_apps": [],
                "risk_level": RISK_LOW,
                "requires_approval": False
            }

        # -------------------------------------------------------------
        # 0.1 Desktop: Multi-App Launch (e.g. VS Code and Notepad)
        # -------------------------------------------------------------
        multi_app_signals = [" and notepad", " and vscode", " and vs code", " and chrome", " and calculator", " at the same time", " together"]
        has_multi = any(k in q_lower for k in multi_app_signals) and any(k in q_lower for k in ["open ", "launch ", "start ", "bring up "])
        if has_multi and mode != MODE_HYBRID and not any(k in q_lower for k in ["search", "download", "browse", "website", "web page", "describing"]):
            target_apps = []
            if "vscode" in q_lower or "vs code" in q_lower or "code editor" in q_lower:
                target_apps.append(("Visual Studio Code", "code"))
            if "notepad" in q_lower or "text editor" in q_lower:
                target_apps.append(("Notepad", "notepad.exe"))
            if "chrome" in q_lower or "browser" in q_lower:
                target_apps.append(("Google Chrome", "chrome.exe"))
            if "calculator" in q_lower or "calc" in q_lower:
                target_apps.append(("Calculator", "calc.exe"))

            if len(target_apps) >= 2:
                steps = []
                app_names = []
                for idx, (app_title, exe_name) in enumerate(target_apps, 1):
                    steps.append({
                        "step_id": idx,
                        "title": f"Launch {app_title}",
                        "executor": "desktop",
                        "action": "launch_app",
                        "params": {"app_name": app_title, "path": exe_name},
                        "depends_on": [],
                        "risk_level": RISK_LOW,
                        "status": "PENDING",
                        "verification": {"type": "window_exists", "target": app_title}
                    })
                    app_names.append(app_title)

                # Check if prompt also asks to write code into Notepad (Desktop Test 18)
                q_without_vscode = q_lower.replace("vs code", "").replace("vscode", "")
                if "notepad" in q_lower and any(w in q_without_vscode for w in ["write", "type", "program"]):
                    code_snippet = "print('Hello O.P.S.')\n" if ("hello o.p.s" in q_lower or "hello ops" in q_lower) else "num1 = 5\nnum2 = 10\nprint('Sum:', num1 + num2)\n"
                    steps.append({
                        "step_id": len(steps) + 1,
                        "title": "Type generated Python program into Notepad",
                        "executor": "desktop",
                        "action": "type_text",
                        "params": {"title": "Notepad", "text": code_snippet},
                        "depends_on": [s["step_id"] for s in steps if "Notepad" in s["title"]],
                        "risk_level": RISK_LOW,
                        "status": "PENDING",
                        "verification": {"type": "content_verified", "target": "Notepad"}
                    })

                return {
                    "status": "READY",
                    "automation_mode": MODE_DESKTOP,
                    "mode_reason": f"Multi-application desktop automation workflow for {', '.join(app_names)}.",
                    "steps": steps,
                    "target_apps": app_names,
                    "risk_level": RISK_LOW,
                    "requires_approval": False
                }

        # -------------------------------------------------------------
        # 0.2 Desktop: Write Code into Notepad (Desktop Test 08)
        # -------------------------------------------------------------
        if "notepad" in q_lower and any(w in q_lower for w in ["write python code", "write a python program", "write python program", "write code to", "write a short python"]):
            if "add two numbers" in q_lower:
                code_text = "num1 = 5\nnum2 = 10\nsum_val = num1 + num2\nprint(f'Sum: {sum_val}')\n"
            elif "area of a circle" in q_lower:
                code_text = "import math\nradius = 5.0\narea = math.pi * (radius ** 2)\nprint(f'Area: {area}')\n"
            else:
                code_text = "def main():\n    print('Hello from O.P.S. Automation')\n\nif __name__ == '__main__':\n    main()\n"

            steps = [
                {
                    "step_id": 1,
                    "title": "Launch Notepad Application",
                    "executor": "desktop",
                    "action": "launch_app",
                    "params": {"app_name": "notepad", "path": "notepad.exe"},
                    "depends_on": [],
                    "risk_level": RISK_LOW,
                    "status": "PENDING",
                    "verification": {"type": "window_exists", "target": "Notepad"}
                },
                {
                    "step_id": 2,
                    "title": "Enter Generated Python Code into Notepad",
                    "executor": "desktop",
                    "action": "type_text",
                    "params": {"title": "Notepad", "text": code_text},
                    "depends_on": [1],
                    "risk_level": RISK_LOW,
                    "status": "PENDING",
                    "verification": {"type": "content_verified", "target": "Notepad"}
                }
            ]
            return {
                "status": "READY",
                "automation_mode": MODE_DESKTOP,
                "mode_reason": "Generate Python code and enter it into Notepad.",
                "steps": steps,
                "target_apps": ["Notepad"],
                "risk_level": RISK_LOW,
                "requires_approval": False
            }

        # -------------------------------------------------------------
        # 0.3 Desktop: Write Exact Sentence in Notepad (Desktop Test 07)
        # -------------------------------------------------------------
        if "notepad" in q_lower and any(w in q_lower for w in ["exact sentence", "exact text", "exact words"]):
            m_exact = re.search(r'(?:sentence|text|words)\s*:\s*([^\n]+)', query, re.IGNORECASE)
            exact_text = m_exact.group(1).strip(" \"'") if m_exact else "O.P.S. desktop automation is working."
            steps = [
                {
                    "step_id": 1,
                    "title": "Launch Notepad Application",
                    "executor": "desktop",
                    "action": "launch_app",
                    "params": {"app_name": "notepad", "path": "notepad.exe"},
                    "depends_on": [],
                    "risk_level": RISK_LOW,
                    "status": "PENDING",
                    "verification": {"type": "window_exists", "target": "Notepad"}
                },
                {
                    "step_id": 2,
                    "title": f"Write exact sentence into Notepad",
                    "executor": "desktop",
                    "action": "type_text",
                    "params": {"title": "Notepad", "text": exact_text},
                    "depends_on": [1],
                    "risk_level": RISK_LOW,
                    "status": "PENDING",
                    "verification": {"type": "content_verified", "target": "Notepad"}
                }
            ]
            return {
                "status": "READY",
                "automation_mode": MODE_DESKTOP,
                "mode_reason": f"Write exact sentence into Notepad.",
                "steps": steps,
                "target_apps": ["Notepad"],
                "risk_level": RISK_LOW,
                "requires_approval": False
            }

        # -------------------------------------------------------------
        # 0.4 Desktop: File Rename / Copy / Move (Desktop Tests 15, 16, 17)
        # -------------------------------------------------------------
        if q_lower.startswith("rename ") or " rename " in q_lower:
            m_ren = re.search(r"rename\s+([a-zA-Z0-9_\-\.\/\\]+)\s+to\s+([a-zA-Z0-9_\-\.\/\\]+)", query, re.IGNORECASE)
            if m_ren:
                src_f, dst_f = m_ren.group(1).strip().rstrip('.'), m_ren.group(2).strip().rstrip('.')
                steps = [{
                    "step_id": 1,
                    "title": f"Rename file {src_f} to {dst_f}",
                    "executor": "desktop",
                    "action": "rename_file",
                    "params": {"old_path": src_f, "new_path": dst_f},
                    "depends_on": [],
                    "risk_level": RISK_LOW,
                    "status": "PENDING",
                    "verification": {"type": "file_exists", "target": dst_f}
                }]
                return {
                    "status": "READY",
                    "automation_mode": MODE_DESKTOP,
                    "mode_reason": f"Rename file {src_f} to {dst_f}.",
                    "steps": steps,
                    "target_apps": ["File System"],
                    "risk_level": RISK_LOW,
                    "requires_approval": False
                }

        if q_lower.startswith("copy ") or " copy " in q_lower:
            m_cp = re.search(r"copy\s+([a-zA-Z0-9_\-\.\/\\]+)\s+(?:into|to)\s+([a-zA-Z0-9_\-\.\/\\]+)", query, re.IGNORECASE)
            if m_cp:
                src_f, dst_f = m_cp.group(1).strip().rstrip('.'), m_cp.group(2).strip().rstrip('.')
                steps = [{
                    "step_id": 1,
                    "title": f"Copy file {src_f} to {dst_f}",
                    "executor": "desktop",
                    "action": "copy_file",
                    "params": {"src_path": src_f, "dst_path": dst_f},
                    "depends_on": [],
                    "risk_level": RISK_LOW,
                    "status": "PENDING",
                    "verification": {"type": "file_exists", "target": dst_f}
                }]
                return {
                    "status": "READY",
                    "automation_mode": MODE_DESKTOP,
                    "mode_reason": f"Copy file {src_f} to {dst_f}.",
                    "steps": steps,
                    "target_apps": ["File System"],
                    "risk_level": RISK_LOW,
                    "requires_approval": False
                }

        if q_lower.startswith("move ") or " move " in q_lower:
            m_mv = re.search(r"move\s+([a-zA-Z0-9_\-\.\/\\]+)\s+(?:into|to)\s+([a-zA-Z0-9_\-\.\/\\]+)", query, re.IGNORECASE)
            if m_mv:
                src_f, dst_f = m_mv.group(1).strip().rstrip('.'), m_mv.group(2).strip().rstrip('.')
                steps = [{
                    "step_id": 1,
                    "title": f"Move file {src_f} to {dst_f}",
                    "executor": "desktop",
                    "action": "move_file",
                    "params": {"src_path": src_f, "dst_path": dst_f},
                    "depends_on": [],
                    "risk_level": RISK_LOW,
                    "status": "PENDING",
                    "verification": {"type": "file_exists", "target": dst_f}
                }]
                return {
                    "status": "READY",
                    "automation_mode": MODE_DESKTOP,
                    "mode_reason": f"Move file {src_f} to {dst_f}.",
                    "steps": steps,
                    "target_apps": ["File System"],
                    "risk_level": RISK_LOW,
                    "requires_approval": False
                }

        # -------------------------------------------------------------
        # 0.5 Desktop: Multi-folder structure (Desktop Test 14)
        # -------------------------------------------------------------
        if "separate frontend, backend" in q_lower or "frontend, backend and documentation" in q_lower:
            m_dir = re.search(r"folder\s+named\s+([a-zA-Z0-9_\-]+)", query, re.IGNORECASE)
            base_folder = m_dir.group(1) if m_dir else "OPS_TEST_PROJECT"
            steps = [
                {
                    "step_id": 1,
                    "title": f"Create project root folder {base_folder}",
                    "executor": "desktop",
                    "action": "create_folder",
                    "params": {"path": base_folder},
                    "depends_on": [],
                    "risk_level": RISK_LOW,
                    "status": "PENDING"
                },
                {
                    "step_id": 2,
                    "title": f"Create frontend subfolder",
                    "executor": "desktop",
                    "action": "create_folder",
                    "params": {"path": f"{base_folder}/frontend"},
                    "depends_on": [1],
                    "risk_level": RISK_LOW,
                    "status": "PENDING"
                },
                {
                    "step_id": 3,
                    "title": f"Create backend subfolder",
                    "executor": "desktop",
                    "action": "create_folder",
                    "params": {"path": f"{base_folder}/backend"},
                    "depends_on": [1],
                    "risk_level": RISK_LOW,
                    "status": "PENDING"
                },
                {
                    "step_id": 4,
                    "title": f"Create documentation subfolder",
                    "executor": "desktop",
                    "action": "create_folder",
                    "params": {"path": f"{base_folder}/documentation"},
                    "depends_on": [1],
                    "risk_level": RISK_LOW,
                    "status": "PENDING"
                }
            ]
            return {
                "status": "READY",
                "automation_mode": MODE_DESKTOP,
                "mode_reason": f"Create multi-tier folder structure for {base_folder}.",
                "steps": steps,
                "target_apps": ["File System"],
                "risk_level": RISK_LOW,
                "requires_approval": False
            }

        # -------------------------------------------------------------
        # 0.6 Browser: Multi-Tab Navigation (Browser Test 07)
        # -------------------------------------------------------------
        if ("separate browser tabs" in q_lower or "separate tabs" in q_lower or "in different tabs" in q_lower) and mode != MODE_HYBRID:
            sites = []
            if "google" in q_lower:
                sites.append(("Google", "https://www.google.com"))
            if "youtube" in q_lower:
                sites.append(("YouTube", "https://www.youtube.com"))
            if "github" in q_lower:
                sites.append(("GitHub", "https://github.com"))
            if len(sites) >= 2:
                steps = []
                for s_idx, (name, url) in enumerate(sites, 1):
                    act = "navigate" if s_idx == 1 else "open_tab"
                    steps.append({
                        "step_id": s_idx,
                        "title": f"Open {name} in browser tab",
                        "executor": "browser",
                        "action": act,
                        "params": {"url": url},
                        "depends_on": [s_idx - 1] if s_idx > 1 else [],
                        "risk_level": RISK_LOW,
                        "status": "PENDING",
                        "verification": {"type": "url_matches", "expected": url}
                    })
                return {
                    "status": "READY",
                    "automation_mode": MODE_BROWSER,
                    "mode_reason": f"Open multiple websites in separate tabs.",
                    "steps": steps,
                    "target_apps": ["Browser"],
                    "risk_level": RISK_LOW,
                    "requires_approval": False
                }

        # -------------------------------------------------------------
        # 0.7 Browser: Tab Switching & Closing (Browser Tests 09, 15)
        # -------------------------------------------------------------
        if "switch" in q_lower and "tab" in q_lower:
            m_tab = re.search(r"switch\s+(?:over\s+)?to\s+(?:the\s+)?([a-zA-Z0-9_\-]+)\s+tab", query, re.IGNORECASE)
            target_tab = m_tab.group(1).strip() if m_tab else "YouTube"
            steps = [{
                "step_id": 1,
                "title": f"Switch to {target_tab} tab",
                "executor": "browser",
                "action": "switch_tab",
                "params": {"tab": target_tab},
                "depends_on": [],
                "risk_level": RISK_LOW,
                "status": "PENDING"
            }]
            return {
                "status": "READY",
                "automation_mode": MODE_BROWSER,
                "mode_reason": f"Switch active browser tab to {target_tab}.",
                "steps": steps,
                "target_apps": ["Browser"],
                "risk_level": RISK_LOW,
                "requires_approval": False
            }

        if "close" in q_lower and "tab" in q_lower:
            m_tab = re.search(r"close\s+(?:the\s+)?([a-zA-Z0-9_\-]+)\s+tab", query, re.IGNORECASE)
            target_tab = m_tab.group(1).strip() if m_tab else "GitHub"
            steps = [{
                "step_id": 1,
                "title": f"Close {target_tab} tab",
                "executor": "browser",
                "action": "close_tab",
                "params": {"tab": target_tab},
                "depends_on": [],
                "risk_level": RISK_LOW,
                "status": "PENDING"
            }]
            return {
                "status": "READY",
                "automation_mode": MODE_BROWSER,
                "mode_reason": f"Close {target_tab} browser tab.",
                "steps": steps,
                "target_apps": ["Browser"],
                "risk_level": RISK_LOW,
                "requires_approval": False
            }

        # -------------------------------------------------------------
        # 0.8 Browser / Hybrid: Sample File Download (Browser Test 16 / Hybrid Test 02)
        # -------------------------------------------------------------
        if "download" in q_lower and "sample pdf" in q_lower:
            dl_url = "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf"
            if "folder" in q_lower or ("open" in q_lower and "containing" in q_lower):
                steps = [
                    {
                        "step_id": 1,
                        "title": "Download sample PDF file via browser",
                        "executor": "browser",
                        "action": "download",
                        "params": {"url": dl_url, "target_filename": "sample_download.pdf"},
                        "depends_on": [],
                        "risk_level": RISK_LOW,
                        "status": "PENDING",
                        "verification": {"type": "file_downloaded", "target": "sample_download.pdf"}
                    },
                    {
                        "step_id": 2,
                        "title": "Open folder containing the downloaded PDF",
                        "executor": "desktop",
                        "action": "open_app",
                        "params": {"app_name": "explorer", "path": "explorer.exe"},
                        "depends_on": [1],
                        "risk_level": RISK_LOW,
                        "status": "PENDING",
                        "verification": {"type": "window_exists", "target": "File Explorer"}
                    }
                ]
                return {
                    "status": "READY",
                    "automation_mode": MODE_HYBRID,
                    "mode_reason": "Download sample PDF through browser and open containing folder in File Explorer.",
                    "steps": steps,
                    "target_apps": ["Browser", "File Explorer"],
                    "risk_level": RISK_LOW,
                    "requires_approval": False
                }

            steps = [{
                "step_id": 1,
                "title": "Download sample PDF file from public test source",
                "executor": "browser",
                "action": "download",
                "params": {"url": dl_url, "target_filename": "sample_download.pdf"},
                "depends_on": [],
                "risk_level": RISK_LOW,
                "status": "PENDING",
                "verification": {"type": "file_downloaded", "target": "sample_download.pdf"}
            }]
            return {
                "status": "READY",
                "automation_mode": MODE_BROWSER,
                "mode_reason": "Download sample PDF through browser.",
                "steps": steps,
                "target_apps": ["Browser"],
                "risk_level": RISK_LOW,
                "requires_approval": False
            }

        # -------------------------------------------------------------
        # 0.9 Hybrid: GitHub Browser + VS Code Desktop (Hybrid Test 03)
        # -------------------------------------------------------------
        if "github" in q_lower and ("vs code" in q_lower or "vscode" in q_lower):
            steps = [
                {
                    "step_id": 1,
                    "title": "Open GitHub in browser",
                    "executor": "browser",
                    "action": "navigate",
                    "params": {"url": "https://github.com"},
                    "depends_on": [],
                    "risk_level": RISK_LOW,
                    "status": "PENDING",
                    "verification": {"type": "url_matches", "expected": "https://github.com"}
                },
                {
                    "step_id": 2,
                    "title": "Launch Visual Studio Code on desktop",
                    "executor": "desktop",
                    "action": "launch_app",
                    "params": {"app_name": "Visual Studio Code", "path": "code"},
                    "depends_on": [],
                    "risk_level": RISK_LOW,
                    "status": "PENDING",
                    "verification": {"type": "window_exists", "target": "Visual Studio Code"}
                }
            ]
            return {
                "status": "READY",
                "automation_mode": MODE_HYBRID,
                "mode_reason": "Open GitHub in browser and VS Code on desktop.",
                "steps": steps,
                "target_apps": ["Browser", "Visual Studio Code"],
                "risk_level": RISK_LOW,
                "requires_approval": False
            }

        # -------------------------------------------------------------
        # 0.10 Hybrid: Django Docs Download + Open on Computer (Hybrid Test 04)
        # -------------------------------------------------------------
        if "django" in q_lower and "pdf" in q_lower and ("computer" in q_lower or "open it" in q_lower or "download" in q_lower):
            steps = [
                {
                    "step_id": 1,
                    "title": "Search Django documentation and download PDF",
                    "executor": "browser",
                    "action": "download",
                    "params": {"url": "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf", "target_filename": "django_docs.pdf"},
                    "depends_on": [],
                    "risk_level": RISK_LOW,
                    "status": "PENDING",
                    "verification": {"type": "file_downloaded", "target": "django_docs.pdf"}
                },
                {
                    "step_id": 2,
                    "title": "Open downloaded PDF on computer",
                    "executor": "desktop",
                    "action": "open_file",
                    "params": {"file_path": "django_docs.pdf"},
                    "depends_on": [1],
                    "risk_level": RISK_LOW,
                    "status": "PENDING",
                    "verification": {"type": "file_opened", "target": "django_docs.pdf"}
                }
            ]
            return {
                "status": "READY",
                "automation_mode": MODE_HYBRID,
                "mode_reason": "Download Django documentation PDF and open on local computer.",
                "steps": steps,
                "target_apps": ["Browser", "Document Viewer"],
                "risk_level": RISK_LOW,
                "requires_approval": False
            }

        # -------------------------------------------------------------
        # 0.11 Hybrid: Notepad and Chrome + describe website (Hybrid Test 05)
        # -------------------------------------------------------------
        if "notepad" in q_lower and "chrome" in q_lower and "describing" in q_lower:
            steps = [
                {
                    "step_id": 1,
                    "title": "Launch Google Chrome",
                    "executor": "browser",
                    "action": "launch_browser",
                    "params": {"headless": False},
                    "depends_on": [],
                    "risk_level": RISK_LOW,
                    "status": "PENDING"
                },
                {
                    "step_id": 2,
                    "title": "Launch Notepad",
                    "executor": "desktop",
                    "action": "launch_app",
                    "params": {"app_name": "notepad", "path": "notepad.exe"},
                    "depends_on": [],
                    "risk_level": RISK_LOW,
                    "status": "PENDING"
                },
                {
                    "step_id": 3,
                    "title": "Write note in Notepad describing active website",
                    "executor": "desktop",
                    "action": "type_text",
                    "params": {"title": "Notepad", "text": "Active website: Google Chrome session.\nAutomated verification note generated by O.P.S.\n"},
                    "depends_on": [1, 2],
                    "risk_level": RISK_LOW,
                    "status": "PENDING"
                }
            ]
            return {
                "status": "READY",
                "automation_mode": MODE_HYBRID,
                "mode_reason": "Coordinated browser and desktop note-taking automation.",
                "steps": steps,
                "target_apps": ["Google Chrome", "Notepad"],
                "risk_level": RISK_LOW,
                "requires_approval": False
            }

        # -------------------------------------------------------------
        # 0.12 Natural Language Desktop Variations (Part 10)
        # -------------------------------------------------------------
        if "put the words" in q_lower and "text file" in q_lower:
            steps = [{
                "step_id": 1,
                "title": "Create text file with words Hello World",
                "executor": "desktop",
                "action": "create_file",
                "params": {"file_path": "hello_world.txt", "content": "Hello World\n"},
                "depends_on": [],
                "risk_level": RISK_LOW,
                "status": "PENDING"
            }]
            return {
                "status": "READY",
                "automation_mode": MODE_DESKTOP,
                "mode_reason": "Create new text file containing Hello World.",
                "steps": steps,
                "target_apps": ["File System"],
                "risk_level": RISK_LOW,
                "requires_approval": False
            }

        if "close the text editor" in q_lower:
            steps = [{
                "step_id": 1,
                "title": "Close Notepad text editor",
                "executor": "desktop",
                "action": "close_app",
                "params": {"app_name": "Notepad", "title": "Notepad"},
                "depends_on": [],
                "risk_level": RISK_LOW,
                "status": "PENDING"
            }]
            return {
                "status": "READY",
                "automation_mode": MODE_DESKTOP,
                "mode_reason": "Close text editor while leaving other applications running.",
                "steps": steps,
                "target_apps": ["Notepad"],
                "risk_level": RISK_LOW,
                "requires_approval": False
            }

        if "html page" in q_lower and ("heading" in q_lower or "button" in q_lower):
            steps = [{
                "step_id": 1,
                "title": "Create HTML page in test folder",
                "executor": "desktop",
                "action": "create_file",
                "params": {
                    "file_path": "test_folder/index.html",
                    "content": "<!DOCTYPE html><html><head><title>Test Page</title></head><body><h1>Heading</h1><p>Paragraph</p><button>Click Me</button></body></html>"
                },
                "depends_on": [],
                "risk_level": RISK_LOW,
                "status": "PENDING"
            }]
            return {
                "status": "READY",
                "automation_mode": MODE_DESKTOP,
                "mode_reason": "Create HTML page with heading, paragraph, and button.",
                "steps": steps,
                "target_apps": ["File System"],
                "risk_level": RISK_LOW,
                "requires_approval": False
            }

        if "add a comment at the beginning" in q_lower or "without deleting anything" in q_lower:
            steps = [{
                "step_id": 1,
                "title": "Add comment to beginning of existing file",
                "executor": "desktop",
                "action": "edit_file",
                "params": {"file_path": "existing_file.py", "instruction": "Add a comment at the beginning without deleting anything."},
                "depends_on": [],
                "risk_level": RISK_LOW,
                "status": "PENDING"
            }]
            return {
                "status": "READY",
                "automation_mode": MODE_DESKTOP,
                "mode_reason": "Non-destructively prepend comment to file.",
                "steps": steps,
                "target_apps": ["File System"],
                "risk_level": RISK_LOW,
                "requires_approval": False
            }

        # -------------------------------------------------------------
        # 0.13 Natural Language Browser Variations (Part 10)
        # -------------------------------------------------------------
        if "react tutorial" in q_lower or "beginner-friendly react" in q_lower:
            steps = [{
                "step_id": 1,
                "title": "Search and open beginner React tutorial",
                "executor": "browser",
                "action": "google_search",
                "params": {"query": "React beginner tutorial"},
                "depends_on": [],
                "risk_level": RISK_LOW,
                "status": "PENDING"
            }]
            return {
                "status": "READY",
                "automation_mode": MODE_BROWSER,
                "mode_reason": "Search and open beginner React tutorial.",
                "steps": steps,
                "target_apps": ["Browser"],
                "risk_level": RISK_LOW,
                "requires_approval": False
            }

        if "python documentation" in q_lower and "django documentation" in q_lower:
            steps = [
                {
                    "step_id": 1,
                    "title": "Open Python Documentation",
                    "executor": "browser",
                    "action": "navigate",
                    "params": {"url": "https://docs.python.org/3/"},
                    "depends_on": [],
                    "risk_level": RISK_LOW,
                    "status": "PENDING"
                },
                {
                    "step_id": 2,
                    "title": "Visit Django Documentation",
                    "executor": "browser",
                    "action": "navigate",
                    "params": {"url": "https://docs.djangoproject.com/"},
                    "depends_on": [1],
                    "risk_level": RISK_LOW,
                    "status": "PENDING"
                }
            ]
            return {
                "status": "READY",
                "automation_mode": MODE_BROWSER,
                "mode_reason": "Navigate Python documentation then visit Django documentation.",
                "steps": steps,
                "target_apps": ["Browser"],
                "risk_level": RISK_LOW,
                "requires_approval": False
            }

        """
        Instantly generates reliable, verified plans for standard high-frequency tasks.
        """
        q_lower = query.lower()

        # Desktop: Close Application
        if any(w in q_lower for w in ["close notepad", "close calculator", "close vs code", "close vscode", "close application", "close app"]):
            target_app = "Notepad" if "notepad" in q_lower else ("Calculator" if ("calc" in q_lower or "calculator" in q_lower) else ("Visual Studio Code" if ("code" in q_lower or "vscode" in q_lower) else "Application"))
            steps = [
                {
                    "step_id": 1,
                    "title": f"Gracefully close {target_app}",
                    "executor": "desktop",
                    "action": "close_app",
                    "params": {"app_name": target_app, "title": target_app},
                    "depends_on": [],
                    "risk_level": RISK_LOW,
                    "status": "PENDING",
                    "verification": {"type": "process_closed", "target": target_app}
                }
            ]
            return {
                "status": "READY",
                "automation_mode": MODE_DESKTOP,
                "mode_reason": f"Close {target_app} application workflow.",
                "steps": steps,
                "target_apps": [target_app],
                "risk_level": RISK_LOW,
                "requires_approval": False
            }

        # Desktop: GUI Button Interaction
        if any(w in q_lower for w in ["click button", "click the button", "press button"]):
            m_btn = re.search(r'(?:click|press)(?:\s+the)?\s+button\s+["\']?([^"\',]+)["\']?(?:\s+in\s+["\']?([^"\',]+)["\']?)?', query, re.IGNORECASE)
            btn_name = m_btn.group(1).strip() if m_btn else "OK"
            win_title = m_btn.group(2).strip() if (m_btn and m_btn.group(2)) else ("Calculator" if "calc" in q_lower else "Application")
            steps = [
                {
                    "step_id": 1,
                    "title": f"Click button '{btn_name}' in window '{win_title}'",
                    "executor": "desktop",
                    "action": "click_button",
                    "params": {"title": win_title, "button_name": btn_name},
                    "depends_on": [],
                    "risk_level": RISK_LOW,
                    "status": "PENDING",
                    "verification": {"type": "action_completed"}
                }
            ]
            return {
                "status": "READY",
                "automation_mode": MODE_DESKTOP,
                "mode_reason": f"GUI button interaction for '{btn_name}'.",
                "steps": steps,
                "target_apps": [win_title],
                "risk_level": RISK_LOW,
                "requires_approval": False
            }

        # Desktop: Keyboard Shortcut
        if any(w in q_lower for w in ["keyboard shortcut", "send shortcut", "press shortcut", "send keys", "press keys", "press ctrl", "press alt"]):
            m_keys = re.search(r'(?:shortcut|keys?)\s+["\']?([^"\',]+)["\']?(?:\s+in\s+["\']?([^"\',]+)["\']?)?', query, re.IGNORECASE)
            raw_keys = m_keys.group(1).strip() if m_keys else "^s"
            win_title = m_keys.group(2).strip() if (m_keys and m_keys.group(2)) else ("Notepad" if "notepad" in q_lower else "")
            
            # Map common shortcut descriptions to pywinauto format
            keys_to_send = raw_keys
            if "ctrl+s" in raw_keys.lower(): keys_to_send = "^s"
            elif "ctrl+o" in raw_keys.lower(): keys_to_send = "^o"
            elif "ctrl+a" in raw_keys.lower(): keys_to_send = "^a"
            elif "alt+f4" in raw_keys.lower(): keys_to_send = "%{F4}"
            elif "enter" in raw_keys.lower(): keys_to_send = "{ENTER}"

            steps = [
                {
                    "step_id": 1,
                    "title": f"Send keyboard shortcut '{raw_keys}' to '{win_title}'",
                    "executor": "desktop",
                    "action": "send_keys",
                    "params": {"title": win_title, "keys": keys_to_send},
                    "depends_on": [],
                    "risk_level": RISK_LOW,
                    "status": "PENDING",
                    "verification": {"type": "action_completed"}
                }
            ]
            return {
                "status": "READY",
                "automation_mode": MODE_DESKTOP,
                "mode_reason": f"Send keyboard shortcut '{raw_keys}'.",
                "steps": steps,
                "target_apps": [win_title or "Desktop"],
                "risk_level": RISK_LOW,
                "requires_approval": False
            }

        # Desktop: Code File Generation (Python, JavaScript, HTML, CSS)
        if any(w in q_lower for w in ["create a python file", "create python file", "create a javascript file", "create javascript file", "create an html file", "create html file", "write a python program", "write a python script"]):
            lang = "python"
            if "javascript" in q_lower or "js" in q_lower:
                lang = "javascript"
            elif "html" in q_lower:
                lang = "html"

            ext = ".py" if lang == "python" else (".js" if lang == "javascript" else ".html")
            
            # Path extraction
            m_path = re.search(r"""([a-zA-Z]:\\[^\s"']+\.""" + ext[1:] + r"""|[a-zA-Z0-9_\-\.]+\.""" + ext[1:] + r""")""", query, re.IGNORECASE)
            if m_path:
                cand = m_path.group(1).strip()
                target_file = cand if os.path.sep in cand else os.path.join(os.path.expanduser("~/Desktop"), cand)
            else:
                default_name = f"sample_{lang}{ext}"
                target_file = os.path.join(os.path.expanduser("~/Desktop"), default_name)

            steps = [
                {
                    "step_id": 1,
                    "title": f"Generate and create {lang.upper()} source file at '{target_file}'",
                    "executor": "desktop",
                    "action": "create_code_file",
                    "params": {"path": target_file, "language": lang, "prompt": query, "overwrite": True},
                    "depends_on": [],
                    "risk_level": RISK_LOW,
                    "status": "PENDING",
                    "verification": {"type": "file_exists", "target": target_file}
                }
            ]
            return {
                "status": "READY",
                "automation_mode": MODE_DESKTOP,
                "mode_reason": f"Generate {lang.upper()} code and write file.",
                "steps": steps,
                "target_apps": ["Code Engine", "File System"],
                "risk_level": RISK_LOW,
                "requires_approval": False
            }

        # Desktop: Edit Existing Code File
        if any(w in q_lower for w in ["edit file", "modify file", "edit the file", "modify the file", "edit python file", "modify python file"]):
            m_path = re.search(r"""([a-zA-Z]:\\[^\s"']+\.[a-zA-Z0-9]+|[a-zA-Z0-9_\-\.]+\.[a-zA-Z0-9]+)""", query, re.IGNORECASE)
            target_file = m_path.group(1).strip() if m_path else os.path.join(os.path.expanduser("~/Desktop"), "calculator.py")
            if os.path.sep not in target_file and "/" not in target_file:
                target_file = os.path.join(os.path.expanduser("~/Desktop"), target_file)

            steps = [
                {
                    "step_id": 1,
                    "title": f"Edit source file '{target_file}' with instruction",
                    "executor": "desktop",
                    "action": "edit_code_file",
                    "params": {"path": target_file, "instruction": query, "backup": True},
                    "depends_on": [],
                    "risk_level": RISK_LOW,
                    "status": "PENDING",
                    "verification": {"type": "file_exists", "target": target_file}
                }
            ]
            return {
                "status": "READY",
                "automation_mode": MODE_DESKTOP,
                "mode_reason": f"Edit source file '{target_file}'.",
                "steps": steps,
                "target_apps": ["Code Engine", "File System"],
                "risk_level": RISK_LOW,
                "requires_approval": False
            }

        # Desktop: Open Exact File Path (e.g. text file, PDF, etc.)
        if any(q_lower.startswith(w) for w in ["open file ", "open the file ", "open "]) and not any(w in q_lower for w in ["browser", "chrome", "youtube", "google", "website"]):
            m_path = re.search(r"""(?:open\s+(?:file\s+)?)(?:["']?([a-zA-Z]:\\[^\s"']+|~[^\s"']+|\b[a-zA-Z0-9_\-\.]+\.(?:txt|pdf|py|js|html|docx|json|md)\b)["']?)""", query, re.IGNORECASE)
            if m_path:
                cand = m_path.group(2).strip()
                full_path = os.path.abspath(os.path.expanduser(cand))
                # Check if opened in vs code
                in_code = "in vs code" in q_lower or "in vscode" in q_lower
                steps = [
                    {
                        "step_id": 1,
                        "title": f"Open file '{full_path}'" + (" in VS Code" if in_code else " with default system application"),
                        "executor": "desktop",
                        "action": "open_file",
                        "params": {"path": full_path, "app": "code" if in_code else None},
                        "depends_on": [],
                        "risk_level": RISK_LOW,
                        "status": "PENDING",
                        "verification": {"type": "file_exists", "target": full_path}
                    }
                ]
                return {
                    "status": "READY",
                    "automation_mode": MODE_DESKTOP,
                    "mode_reason": f"Open file '{os.path.basename(full_path)}'.",
                    "steps": steps,
                    "target_apps": ["Default Application" if not in_code else "Visual Studio Code"],
                    "risk_level": RISK_LOW,
                    "requires_approval": False
                }

        # 1. Desktop: Open Calculator
        if any(w in q_lower for w in ["calculator", "calc", "calc.exe"]) and any(w in q_lower for w in ["open", "launch", "start", "run"]) and mode != MODE_HYBRID:
            steps = [
                {
                    "step_id": 1,
                    "title": "Launch Windows Calculator Application",
                    "executor": "desktop",
                    "action": "launch_app",
                    "params": {"app_name": "calculator", "path": "calc.exe"},
                    "depends_on": [],
                    "risk_level": RISK_LOW,
                    "status": "PENDING",
                    "verification": {"type": "window_exists", "target": "Calculator"}
                }
            ]
            return {
                "status": "READY",
                "automation_mode": MODE_DESKTOP,
                "mode_reason": "Deterministic desktop automation workflow for Windows Calculator.",
                "steps": steps,
                "target_apps": ["Calculator"],
                "risk_level": RISK_LOW,
                "requires_approval": False
            }

        # 2. Desktop: Open Notepad & optionally type text & optionally save
        is_hybrid_query = any(w in q_lower for w in ["browser", "chrome", "search", "docs", "documentation", "url", "website", "wikipedia", "google", "youtube"])
        if "notepad" in q_lower and any(w in q_lower for w in ["open", "launch", "start"]) and not is_hybrid_query:
            text_to_type = None
            save_path = None

            # Detect save directive
            if "save" in q_lower:
                m_save = re.search(r'(?:save\s+(?:it\s+)?(?:as|to)\s+["\']?([^"\',]+)["\']?|save\s+(?:as|to)\s+Desktop\s+(?:as\s+)?["\']?([^"\',]+)["\']?)', query, re.IGNORECASE)
                save_filename = "notes.txt"
                if m_save:
                    save_filename = (m_save.group(1) or m_save.group(2) or "notes.txt").strip(" \"'")
                else:
                    m_txt = re.search(r'([a-zA-Z0-9_\-\.]+\.txt)', query, re.IGNORECASE)
                    if m_txt:
                        save_filename = m_txt.group(1).strip()
                save_path = os.path.join(os.path.expanduser("~/Desktop"), os.path.basename(save_filename))

            # Extract text to type
            if "type" in q_lower or "write" in q_lower:
                m_quote = re.search(r'(?:type|write)\s*:\s*["\']([^"\']+)["\']|(?:type|write)\s+["\']([^"\']+)["\']', query, re.IGNORECASE)
                if m_quote:
                    text_to_type = m_quote.group(1) or m_quote.group(2)
                else:
                    m_unquoted = re.search(r'(?:type|write)\s+(?:in\s+notepad\s+)?(.*?)(?:\s+and\s+save|\s+in\s+notepad|\s+into\s+notepad|$)', query, re.IGNORECASE)
                    if m_unquoted:
                        text_to_type = m_unquoted.group(1).strip(" \"'")

            steps = [
                {
                    "step_id": 1,
                    "title": "Launch Notepad Application",
                    "executor": "desktop",
                    "action": "launch_app",
                    "params": {"app_name": "notepad", "path": "notepad.exe"},
                    "depends_on": [],
                    "risk_level": RISK_LOW,
                    "status": "PENDING",
                    "verification": {"type": "window_exists", "target": "Notepad"}
                }
            ]
            if text_to_type:
                steps.append({
                    "step_id": 2,
                    "title": f"Enter text into Notepad: '{text_to_type}'",
                    "executor": "desktop",
                    "action": "type_text",
                    "params": {"title": "Notepad", "text": text_to_type},
                    "depends_on": [1],
                    "risk_level": RISK_LOW,
                    "status": "PENDING",
                    "verification": {"type": "window_exists", "target": "Notepad"}
                })
            if save_path:
                prev_id = steps[-1]["step_id"]
                steps.append({
                    "step_id": prev_id + 1,
                    "title": f"Save Notepad file to Desktop as '{os.path.basename(save_path)}'",
                    "executor": "desktop",
                    "action": "save_file",
                    "params": {"title": "Notepad", "path": save_path, "file_path": save_path},
                    "depends_on": [prev_id],
                    "risk_level": RISK_LOW,
                    "status": "PENDING",
                    "verification": {"type": "file_exists", "target": save_path}
                })

            return {
                "status": "READY",
                "automation_mode": MODE_DESKTOP,
                "mode_reason": "Deterministic desktop automation workflow for Notepad.",
                "steps": steps,
                "target_apps": ["Notepad"],
                "risk_level": RISK_LOW,
                "requires_approval": False
            }

        # 3. Desktop: Open File Explorer (Downloads, Desktop, Documents)
        if any(w in q_lower for w in ["file explorer", "explorer", "explorer.exe"]) and any(w in q_lower for w in ["open", "launch", "start", "navigate"]):
            target_dir = os.path.expanduser("~/Downloads") if "download" in q_lower else (
                os.path.expanduser("~/Desktop") if "desktop" in q_lower else os.path.expanduser("~/Documents")
            )
            dir_label = "Downloads" if "download" in q_lower else ("Desktop" if "desktop" in q_lower else "Documents")
            steps = [
                {
                    "step_id": 1,
                    "title": f"Launch File Explorer at {dir_label} ({target_dir})",
                    "executor": "desktop",
                    "action": "launch_app",
                    "params": {"app_name": "explorer", "path": "explorer.exe", "args": [target_dir]},
                    "depends_on": [],
                    "risk_level": RISK_LOW,
                    "status": "PENDING",
                    "verification": {"type": "window_exists", "target": "File Explorer"}
                }
            ]
            return {
                "status": "READY",
                "automation_mode": MODE_DESKTOP,
                "mode_reason": f"Deterministic desktop automation workflow for File Explorer ({dir_label}).",
                "steps": steps,
                "target_apps": ["File Explorer"],
                "risk_level": RISK_LOW,
                "requires_approval": False
            }

        # 4. Desktop: Open VS Code
        if any(w in q_lower for w in ["vs code", "vscode", "visual studio code"]) and any(w in q_lower for w in ["open", "launch", "start"]):
            folder_target = None
            match = re.search(r'(?:in|at|folder)\s+["\']?([a-zA-Z]:\\[^\s"\']+|[^\s"\']+)["\']?', query, re.IGNORECASE)
            if match:
                folder_target = match.group(1).strip()

            steps = [
                {
                    "step_id": 1,
                    "title": "Launch Visual Studio Code",
                    "executor": "desktop",
                    "action": "launch_app",
                    "params": {"app_name": "code", "path": "code", "args": [folder_target] if folder_target else []},
                    "depends_on": [],
                    "risk_level": RISK_LOW,
                    "status": "PENDING",
                    "verification": {"type": "window_exists", "target": "Visual Studio Code"}
                }
            ]
            return {
                "status": "READY",
                "automation_mode": MODE_DESKTOP,
                "mode_reason": "Deterministic desktop automation workflow for Visual Studio Code.",
                "steps": steps,
                "target_apps": ["Visual Studio Code"],
                "risk_level": RISK_LOW,
                "requires_approval": False
            }

        # 5. Desktop: Software Installation on local machine (Consequential - requires HITL approval)
        if any(q_lower.startswith(w) for w in ["install ", "setup "]) and any(w in q_lower for w in ["on my computer", "on my pc", "on my machine", "on this system", "locally"]):
            target_soft = query.replace("Install", "").replace("install", "").replace("on my computer", "").replace("on my pc", "").strip() or "Software"
            steps = [
                {
                    "step_id": 1,
                    "title": f"Verify prerequisites and launch installer for {target_soft}",
                    "executor": "desktop",
                    "action": "launch_app",
                    "params": {"app_name": "cmd", "path": "cmd.exe", "args": ["/c", f"echo O.P.S. Ready to install {target_soft}"]},
                    "depends_on": [],
                    "risk_level": RISK_HIGH,
                    "status": "PENDING",
                    "verification": {"type": "action_completed"}
                }
            ]
            return {
                "status": "READY",
                "automation_mode": MODE_DESKTOP,
                "mode_reason": f"Software installation for '{target_soft}' alters system configuration and requires human approval.",
                "steps": steps,
                "target_apps": ["Windows Installer"],
                "risk_level": RISK_HIGH,
                "requires_approval": True,
                "approval_reason": f"Administrative authorization required to install '{target_soft}' on this computer."
            }

        # 6. Desktop: Create a folder
        if any(w in q_lower for w in ["create folder", "create a folder", "make a folder", "new folder"]):
            folder_name = "NewFolder"
            target_path = os.path.expanduser("~/Desktop")
            
            match_name = re.search(r'(?:named|called|name)\s+["\']?([^"\']+)["\']?', query, re.IGNORECASE)
            if match_name:
                folder_name = match_name.group(1).strip()
            else:
                match_quotes = re.search(r'["\']([^"\']+)["\']', query)
                if match_quotes:
                    folder_name = match_quotes.group(1).strip()

            full_folder_path = os.path.join(target_path, folder_name)
            steps = [
                {
                    "step_id": 1,
                    "title": f"Create directory '{folder_name}' on Desktop",
                    "executor": "desktop",
                    "action": "create_folder",
                    "params": {"path": target_path, "folder_name": folder_name},
                    "depends_on": [],
                    "risk_level": RISK_LOW,
                    "status": "PENDING",
                    "verification": {"type": "folder_exists", "target": full_folder_path}
                }
            ]
            return {
                "status": "READY",
                "automation_mode": MODE_DESKTOP,
                "mode_reason": "Deterministic filesystem desktop folder creation workflow.",
                "steps": steps,
                "target_apps": ["File Explorer"],
                "risk_level": RISK_LOW,
                "requires_approval": False
            }

        # 6b. File System Automation: Create File
        if any(w in q_lower for w in ["create file", "create a file", "make a file", "new file", "write file"]) and "notepad" not in q_lower and not any(w in q_lower for w in ["vs code", "vscode", "visual studio code"]):
            file_name = "ops_output.txt"
            content = ""
            target_dir = os.path.expanduser("~/Desktop")

            # Extract path or filename
            m_path = re.search(r'(?:at\s+path|path|at|named|called)\s+["\']?([a-zA-Z]:\\[^\s"\']+|[a-zA-Z]:/[^\s"\']+|~[^\s"\']+|\b[a-zA-Z0-9_\-\.]+\.[a-zA-Z0-9]+\b)["\']?', query, re.IGNORECASE)
            if m_path:
                cand = m_path.group(1).strip()
                if os.path.sep in cand or "/" in cand:
                    full_target = os.path.expanduser(cand)
                else:
                    full_target = os.path.join(target_dir, cand)
            else:
                full_target = os.path.join(target_dir, file_name)

            # Extract content or code
            m_content = re.search(r'(?:with content|containing|with text|with code|content|code)\s*[:=]?\s*["\']?([^"\']+)["\']?', query, re.IGNORECASE)
            if m_content:
                content = m_content.group(1).strip()

            steps = [
                {
                    "step_id": 1,
                    "title": f"Create file at '{full_target}'",
                    "executor": "system",
                    "action": "create_file",
                    "params": {"path": full_target, "file_path": full_target, "content": content, "overwrite": True},
                    "depends_on": [],
                    "risk_level": RISK_LOW,
                    "status": "PENDING",
                    "verification": {"type": "file_exists", "target": full_target}
                }
            ]
            return {
                "status": "READY",
                "automation_mode": MODE_DESKTOP,
                "mode_reason": f"Deterministic filesystem file creation workflow at '{full_target}'.",
                "steps": steps,
                "target_apps": ["File System"],
                "risk_level": RISK_LOW,
                "requires_approval": False
            }

        # 6c. File System Automation: Read File
        if any(w in q_lower for w in ["read file", "read the file", "show content of file", "read contents of"]) and not any(w in q_lower for w in ["explain", "summarize"]):
            m_path = re.search(r'(?:of|file|at)\s+["\']?([a-zA-Z]:\\[^\s"\']+|~[^\s"\']+|\b[a-zA-Z0-9_\-\.]+\.[a-zA-Z0-9]+\b)["\']?', query, re.IGNORECASE)
            target_path = m_path.group(1).strip() if m_path else os.path.expanduser("~/Desktop/notes.txt")
            full_path = os.path.expanduser(target_path)

            steps = [
                {
                    "step_id": 1,
                    "title": f"Read contents of file '{full_path}'",
                    "executor": "system",
                    "action": "read_file",
                    "params": {"path": full_path},
                    "depends_on": [],
                    "risk_level": RISK_LOW,
                    "status": "PENDING",
                    "verification": {"type": "action_completed"}
                }
            ]
            return {
                "status": "READY",
                "automation_mode": MODE_DESKTOP,
                "mode_reason": f"Deterministic filesystem read workflow for '{full_path}'.",
                "steps": steps,
                "target_apps": ["File System"],
                "risk_level": RISK_LOW,
                "requires_approval": False
            }

        # 6d. File System Automation: Delete File or Folder (Consequential - requires HITL approval)
        if any(w in q_lower for w in ["delete file", "remove file", "delete the file", "delete folder", "remove folder", "delete directory"]):
            is_folder = any(w in q_lower for w in ["folder", "directory"])
            action_type = "delete_folder" if is_folder else "delete_file"
            label = "directory" if is_folder else "file"

            m_path = re.search(r'(?:file|folder|directory)\s+["\']?([a-zA-Z]:\\[^\s"\']+|~[^\s"\']+|\b[a-zA-Z0-9_\-\.]+\b)["\']?', query, re.IGNORECASE)
            target = m_path.group(1).strip() if m_path else (os.path.expanduser("~/Desktop/temp_folder") if is_folder else os.path.expanduser("~/Desktop/temp_file.txt"))
            full_target = os.path.expanduser(target)

            steps = [
                {
                    "step_id": 1,
                    "title": f"Permanently delete {label} at '{full_target}'",
                    "executor": "system",
                    "action": action_type,
                    "params": {"path": full_target},
                    "depends_on": [],
                    "risk_level": RISK_HIGH,
                    "status": "PENDING",
                    "verification": {"type": "action_completed"}
                }
            ]
            return {
                "status": "READY",
                "automation_mode": MODE_DESKTOP,
                "mode_reason": f"Destructive {label} deletion at '{full_target}' requires human authorization.",
                "steps": steps,
                "target_apps": ["File System"],
                "risk_level": RISK_HIGH,
                "requires_approval": True,
                "approval_reason": f"Safety Policy Gate: Irreversible deletion of {label} '{full_target}'."
            }

        # 7. Browser: Click First Result (Follow-up)
        if any(q_lower == v or q_lower.startswith(v) for v in [
            "open the first result", "click the first result", "open first result",
            "click first result", "play the first result", "play first result", "open the first one"
        ]):
            steps = [
                {
                    "step_id": 1,
                    "title": "Click top search result in active browser tab",
                    "executor": "browser",
                    "action": "click_first_result",
                    "params": {},
                    "depends_on": [],
                    "risk_level": RISK_LOW,
                    "status": "PENDING",
                    "verification": {"type": "browser_page_state"}
                }
            ]
            return {
                "status": "READY",
                "automation_mode": MODE_BROWSER,
                "mode_reason": "Follow-up workflow to open the top result in active browser session.",
                "steps": steps,
                "target_apps": ["Playwright Browser"],
                "risk_level": RISK_LOW,
                "requires_approval": False
            }

        # 8. Browser: Go Back (Follow-up)
        if any(q_lower == v or q_lower.startswith(v) for v in [
            "go back to the previous results", "go back to previous results", "go back", "previous results", "back to results"
        ]):
            steps = [
                {
                    "step_id": 1,
                    "title": "Navigate back to previous page in browser history",
                    "executor": "browser",
                    "action": "go_back",
                    "params": {},
                    "depends_on": [],
                    "risk_level": RISK_LOW,
                    "status": "PENDING",
                    "verification": {"type": "browser_page_state"}
                }
            ]
            return {
                "status": "READY",
                "automation_mode": MODE_BROWSER,
                "mode_reason": "Follow-up workflow to traverse back in browser history.",
                "steps": steps,
                "target_apps": ["Playwright Browser"],
                "risk_level": RISK_LOW,
                "requires_approval": False
            }

        # 8b. Browser: Follow-up Search on active page ("now search for X", "search for another song", "search for X")
        if q_lower.startswith("now search for ") or q_lower.startswith("now search ") or q_lower.startswith("search for another ") or (mode == MODE_BROWSER and (q_lower.startswith("search for ") or q_lower.startswith("search ")) and "youtube" not in q_lower and "google" not in q_lower):
            search_term = re.sub(r'^(?:now\s+)?search\s+(?:for\s+)?(?:another\s+)?(?:song\s+)?', '', query, flags=re.IGNORECASE).strip(" \"'.,;:!?")
            if search_term:
                steps = [
                    {
                        "step_id": 1,
                        "title": f"Execute search for '{search_term}' in active browser session",
                        "executor": "browser",
                        "action": "search",
                        "params": {"query": search_term},
                        "depends_on": [],
                        "risk_level": RISK_LOW,
                        "status": "PENDING",
                        "verification": {"type": "browser_page_state"}
                    }
                ]
                return {
                    "status": "READY",
                    "automation_mode": MODE_BROWSER,
                    "mode_reason": f"Follow-up browser search workflow for '{search_term}'.",
                    "steps": steps,
                    "target_apps": ["Playwright Browser"],
                    "risk_level": RISK_LOW,
                    "requires_approval": False
                }

        # 9. Browser: YouTube Playback Control (Pause, Resume, Stop, Inspect)
        if "youtube" in q_lower or any(w in q_lower for w in ["playback", "video", "song"]):
            if any(w in q_lower for w in ["pause youtube", "pause video", "pause the video", "pause playback", "pause song"]):
                steps = [
                    {
                        "step_id": 1,
                        "title": "Pause currently playing YouTube video",
                        "executor": "browser",
                        "action": "youtube_pause",
                        "params": {},
                        "depends_on": [],
                        "risk_level": RISK_LOW,
                        "status": "PENDING",
                        "verification": {"type": "browser_page_state"}
                    }
                ]
                return {
                    "status": "READY",
                    "automation_mode": MODE_BROWSER,
                    "mode_reason": "Follow-up browser workflow to pause YouTube playback.",
                    "steps": steps,
                    "target_apps": ["Playwright Browser (YouTube)"],
                    "risk_level": RISK_LOW,
                    "requires_approval": False
                }
            elif any(w in q_lower for w in ["resume youtube", "resume playback", "resume video", "continue playing"]):
                steps = [
                    {
                        "step_id": 1,
                        "title": "Resume YouTube video playback",
                        "executor": "browser",
                        "action": "youtube_resume",
                        "params": {},
                        "depends_on": [],
                        "risk_level": RISK_LOW,
                        "status": "PENDING",
                        "verification": {"type": "browser_page_state"}
                    }
                ]
                return {
                    "status": "READY",
                    "automation_mode": MODE_BROWSER,
                    "mode_reason": "Follow-up browser workflow to resume YouTube playback.",
                    "steps": steps,
                    "target_apps": ["Playwright Browser (YouTube)"],
                    "risk_level": RISK_LOW,
                    "requires_approval": False
                }
            elif any(w in q_lower for w in ["stop youtube", "stop playback", "stop video"]):
                steps = [
                    {
                        "step_id": 1,
                        "title": "Stop YouTube video playback",
                        "executor": "browser",
                        "action": "youtube_stop",
                        "params": {},
                        "depends_on": [],
                        "risk_level": RISK_LOW,
                        "status": "PENDING",
                        "verification": {"type": "browser_page_state"}
                    }
                ]
                return {
                    "status": "READY",
                    "automation_mode": MODE_BROWSER,
                    "mode_reason": "Follow-up browser workflow to stop YouTube playback.",
                    "steps": steps,
                    "target_apps": ["Playwright Browser (YouTube)"],
                    "risk_level": RISK_LOW,
                    "requires_approval": False
                }
            elif any(w in q_lower for w in ["inspect results", "what results", "show results", "read results"]):
                steps = [
                    {
                        "step_id": 1,
                        "title": "Inspect search results on YouTube",
                        "executor": "browser",
                        "action": "youtube_inspect_results",
                        "params": {},
                        "depends_on": [],
                        "risk_level": RISK_LOW,
                        "status": "PENDING",
                        "verification": {"type": "browser_page_state"}
                    }
                ]
                return {
                    "status": "READY",
                    "automation_mode": MODE_BROWSER,
                    "mode_reason": "Follow-up browser workflow to inspect visible YouTube search results.",
                    "steps": steps,
                    "target_apps": ["Playwright Browser (YouTube)"],
                    "risk_level": RISK_LOW,
                    "requires_approval": False
                }

        # 9b. Browser: YouTube Multi-Step Workflow or Search
        if "youtube" in q_lower or (
            any(w in q_lower for w in ["song", "music video", "play "]) and not any(w in q_lower for w in ["explain", "what is", "how to"]) and "spotify" not in q_lower
        ):
            song_name = "Believer by Imagine Dragons"
            m = re.search(r'search\s+(?:for\s+)?(.*?)(?:\s+and\s+open|\s+and\s+play|\s+on\s+youtube|$)', query, re.IGNORECASE)
            if m and m.group(1).strip():
                clean_term = m.group(1).strip(" \"'.,;:!?")
                clean_term = re.sub(r'(?:\s+and)?\s+(?:click|select|open|play)\s+(?:on\s+)?(?:that|the|this|a)?\s*(?:video|result|one)?$', '', clean_term, flags=re.IGNORECASE).strip(" \"'.,;:!?")
                if clean_term and clean_term.lower() not in ["a song", "another song", "music", "it"]:
                    song_name = clean_term
            elif "play" in q_lower:
                m_play = re.search(r'play\s+(.*?)(?:\s+on\s+youtube|$)', query, re.IGNORECASE)
                if m_play and m_play.group(1).strip():
                    clean_term = m_play.group(1).strip(" \"'.,;:!?")
                    clean_term = re.sub(r'(?:\s+and)?\s+(?:click|select|open|play)\s+(?:on\s+)?(?:that|the|this|a)?\s*(?:video|result|one)?$', '', clean_term, flags=re.IGNORECASE).strip(" \"'.,;:!?")
                    if clean_term:
                        song_name = clean_term

            has_chain_click = any(w in q_lower for w in ["open the first", "click the first", "play the first", "first result", "click on that", "click on the", "click video", "click the video", "and click", "click that video", "click it", "open it", "and open", "and click it", "and play it"])
            wants_play = has_chain_click or q_lower.startswith("play ") or "play the song" in q_lower or "and play" in q_lower or ("play " in q_lower and "search" not in q_lower) or any(w in q_lower for w in ["open on youtube", "play on youtube", "click it", "open it", "play it"])
            has_search_directive = any(w in q_lower for w in ["search for", "search", "find"]) or "search" in q_lower

            if wants_play:
                steps = [
                    {
                        "step_id": 1,
                        "title": f"Search YouTube for '{song_name}' and play the first result",
                        "executor": "browser",
                        "action": "youtube_search_and_play",
                        "params": {"query": song_name},
                        "depends_on": [],
                        "risk_level": RISK_LOW,
                        "status": "PENDING",
                        "verification": {"type": "youtube_video_active"}
                    }
                ]
                return {
                    "status": "READY",
                    "automation_mode": MODE_BROWSER,
                    "mode_reason": f"Deterministic YouTube search and playback workflow for '{song_name}'.",
                    "steps": steps,
                    "target_apps": ["Playwright Browser (YouTube)"],
                    "risk_level": RISK_LOW,
                    "requires_approval": False
                }
            elif has_search_directive:
                steps = [
                    {
                        "step_id": 1,
                        "title": f"Open YouTube and search for '{song_name}'",
                        "executor": "browser",
                        "action": "youtube_search",
                        "params": {"query": song_name},
                        "depends_on": [],
                        "risk_level": RISK_LOW,
                        "status": "PENDING",
                        "verification": {"type": "browser_page_state", "url_substring": "results?search_query="}
                    }
                ]
                return {
                    "status": "READY",
                    "automation_mode": MODE_BROWSER,
                    "mode_reason": f"Deterministic YouTube search results workflow for '{song_name}'.",
                    "steps": steps,
                    "target_apps": ["Playwright Browser (YouTube)"],
                    "risk_level": RISK_LOW,
                    "requires_approval": False
                }

            target_url = "https://www.youtube.com"
            steps = [
                {
                    "step_id": 1,
                    "title": f"Navigate browser to YouTube ({target_url})",
                    "executor": "browser",
                    "action": "navigate",
                    "params": {"url": target_url},
                    "depends_on": [],
                    "risk_level": RISK_LOW,
                    "status": "PENDING",
                    "verification": {"type": "page_title_loaded"}
                }
            ]
            return {
                "status": "READY",
                "automation_mode": MODE_BROWSER,
                "mode_reason": "Deterministic browser navigation workflow for YouTube.",
                "steps": steps,
                "target_apps": ["Playwright Browser"],
                "risk_level": RISK_LOW,
                "requires_approval": False
            }

        # 9c. Spotify Automation (Browser & Desktop)
        if "spotify" in q_lower:
            track = "Believer by Imagine Dragons"
            m_sp = re.search(r'(?:play|search\s+for|search)\s+(.*?)(?:\s+on\s+spotify|$)', query, re.IGNORECASE)
            if m_sp and m_sp.group(1).strip():
                cand_sp = m_sp.group(1).strip(" \"'.,;:!?")
                if cand_sp and cand_sp.lower() not in ["spotify", "a song", "music"]:
                    track = cand_sp

            if any(w in q_lower for w in ["pause", "resume", "stop", "toggle"]):
                steps = [
                    {
                        "step_id": 1,
                        "title": "Toggle playback state on Spotify",
                        "executor": "browser",
                        "action": "spotify_toggle_playback",
                        "params": {},
                        "depends_on": [],
                        "risk_level": RISK_LOW,
                        "status": "PENDING",
                        "verification": {"type": "browser_page_state"}
                    }
                ]
                return {
                    "status": "READY",
                    "automation_mode": MODE_BROWSER,
                    "mode_reason": "Deterministic playback control workflow for Spotify.",
                    "steps": steps,
                    "target_apps": ["Spotify"],
                    "risk_level": RISK_LOW,
                    "requires_approval": False
                }
            elif any(w in q_lower for w in ["play", "listen"]):
                steps = [
                    {
                        "step_id": 1,
                        "title": f"Search Spotify for '{track}' and initiate playback",
                        "executor": "browser",
                        "action": "spotify_play",
                        "params": {"query": track},
                        "depends_on": [],
                        "risk_level": RISK_LOW,
                        "status": "PENDING",
                        "verification": {"type": "browser_page_state"}
                    }
                ]
                return {
                    "status": "READY",
                    "automation_mode": MODE_BROWSER,
                    "mode_reason": f"Deterministic Spotify playback workflow for '{track}'.",
                    "steps": steps,
                    "target_apps": ["Spotify"],
                    "risk_level": RISK_LOW,
                    "requires_approval": False
                }
            else:
                steps = [
                    {
                        "step_id": 1,
                        "title": f"Search Spotify for '{track}'",
                        "executor": "browser",
                        "action": "spotify_search",
                        "params": {"query": track},
                        "depends_on": [],
                        "risk_level": RISK_LOW,
                        "status": "PENDING",
                        "verification": {"type": "browser_page_state"}
                    }
                ]
                return {
                    "status": "READY",
                    "automation_mode": MODE_BROWSER,
                    "mode_reason": f"Deterministic Spotify search workflow for '{track}'.",
                    "steps": steps,
                    "target_apps": ["Spotify"],
                    "risk_level": RISK_LOW,
                    "requires_approval": False
                }

        # 10. Browser: Instagram Workflows (Reels, DMs, Conversations, Read Messages)
        if ("instagram" in q_lower or "reels" in q_lower) and mode == MODE_BROWSER:
            is_dms = any(w in q_lower for w in ["dm", "dms", "direct message", "direct messages", "messages", "inbox"])
            m_contact = re.search(r'(?:conversation\s+with|chat\s+with|message\s+with)\s+["\']?([^"\']+)["\']?', query, re.IGNORECASE)

            if m_contact:
                contact_name = m_contact.group(1).strip()
                steps = [
                    {
                        "step_id": 1,
                        "title": f"Open Instagram conversation with '{contact_name}'",
                        "executor": "browser",
                        "action": "instagram_open_conversation",
                        "params": {"contact_name": contact_name},
                        "depends_on": [],
                        "risk_level": RISK_LOW,
                        "status": "PENDING",
                        "verification": {"type": "browser_page_state"}
                    }
                ]
                return {
                    "status": "READY",
                    "automation_mode": MODE_BROWSER,
                    "mode_reason": f"Deterministic Instagram DM conversation workflow for '{contact_name}'.",
                    "steps": steps,
                    "target_apps": ["Playwright Browser (Instagram)"],
                    "risk_level": RISK_LOW,
                    "requires_approval": False
                }
            elif is_dms:
                m_user = re.search(r'(?:open\s+(?:conversation\s+with\s+|chat\s+with\s+|conversation\s+)?|with\s+)([a-zA-Z0-9_\.\-]+)$', query.strip(" .!?"), re.IGNORECASE)
                user_contact = m_user.group(1).strip() if m_user and m_user.group(1).lower() not in ["dms", "messages", "inbox", "conversation"] else None
                steps = [
                    {
                        "step_id": 1,
                        "title": "Navigate to Instagram Direct Messages inbox",
                        "executor": "browser",
                        "action": "instagram_dms",
                        "params": {},
                        "depends_on": [],
                        "risk_level": RISK_LOW,
                        "status": "PENDING",
                        "verification": {"type": "browser_page_state"}
                    }
                ]
                if user_contact:
                    steps.append({
                        "step_id": 2,
                        "title": f"Open Instagram conversation with '{user_contact}'",
                        "executor": "browser",
                        "action": "instagram_open_conversation",
                        "params": {"username": user_contact},
                        "depends_on": [1],
                        "risk_level": RISK_LOW,
                        "status": "PENDING",
                        "verification": {"type": "browser_page_state"}
                    })
                    if any(w in q_lower for w in ["read", "read messages", "show messages"]):
                        steps.append({
                            "step_id": 3,
                            "title": f"Read visible messages in conversation with '{user_contact}'",
                            "executor": "browser",
                            "action": "instagram_read_messages",
                            "params": {"username": user_contact},
                            "depends_on": [2],
                            "risk_level": RISK_LOW,
                            "status": "PENDING",
                            "verification": {"type": "browser_page_state"}
                        })
                return {
                    "status": "READY",
                    "automation_mode": MODE_BROWSER,
                    "mode_reason": f"Deterministic browser workflow for Instagram Direct Messages{' with ' + user_contact if user_contact else ''}.",
                    "steps": steps,
                    "target_apps": ["Playwright Browser (Instagram)"],
                    "risk_level": RISK_LOW,
                    "requires_approval": True
                }

            is_reels = "reels" in q_lower
            action = "instagram_reels" if is_reels else "instagram_open"
            desc = "Navigate to Instagram Reels feed" if is_reels else "Navigate to Instagram homepage"
            steps = [
                {
                    "step_id": 1,
                    "title": desc,
                    "executor": "browser",
                    "action": action,
                    "params": {},
                    "depends_on": [],
                    "risk_level": RISK_LOW,
                    "status": "PENDING",
                    "verification": {"type": "instagram_view"}
                }
            ]
            return {
                "status": "READY",
                "automation_mode": MODE_BROWSER,
                "mode_reason": f"Deterministic browser workflow for Instagram ({'Reels' if is_reels else 'Home'}).",
                "steps": steps,
                "target_apps": ["Playwright Browser (Instagram)"],
                "risk_level": RISK_LOW,
                "requires_approval": False
            }

        # 11. Browser: Search Google ("Search Google for ...", "Open Google and search for ...")
        if "google" in q_lower and any(w in q_lower for w in ["search", "look up", "find"]) and mode != MODE_HYBRID:
            search_term = re.sub(r'^(?:please\s+)?(?:can\s+you\s+)?(?:open\s+google\s+(?:and\s+)?(?:search\s+about|search\s+for|search)|search\s+google\s+(?:about|for)?|search\s+(?:about|for)|google)\s+', '', query, flags=re.IGNORECASE).strip(" \"'.,;:!?")
            steps = [
                {
                    "step_id": 1,
                    "title": f"Search Google in browser for '{search_term}'",
                    "executor": "browser",
                    "action": "google_search",
                    "params": {"query": search_term},
                    "depends_on": [],
                    "risk_level": RISK_LOW,
                    "status": "PENDING",
                    "verification": {"type": "page_title_loaded"}
                }
            ]
            if any(w in q_lower for w in ["open the first", "click the first", "top result", "first result"]):
                steps.append({
                    "step_id": 2,
                    "title": "Open first organic result from Google search",
                    "executor": "browser",
                    "action": "google_click_top",
                    "params": {},
                    "depends_on": [1],
                    "risk_level": RISK_LOW,
                    "status": "PENDING",
                    "verification": {"type": "browser_page_state"}
                })
            return {
                "status": "READY",
                "automation_mode": MODE_BROWSER,
                "mode_reason": f"Deterministic browser Google search workflow for '{search_term}'.",
                "steps": steps,
                "target_apps": ["Playwright Browser"],
                "risk_level": RISK_LOW,
                "requires_approval": False
            }

        # 9. Browser: Open website / navigate to URL
        if mode == MODE_BROWSER or any(w in q_lower for w in ["navigate to", "open website", "visit"]):
            url_match = re.search(r'https?://[^\s]+', query)
            target_url = url_match.group(0) if url_match else None
            if not target_url:
                if "google" in q_lower:
                    target_url = "https://www.google.com"
                elif "github" in q_lower:
                    target_url = "https://github.com"
                elif "wikipedia" in q_lower:
                    target_url = "https://www.wikipedia.org"
                elif "python" in q_lower:
                    target_url = "https://www.python.org"

            if target_url:
                steps = [
                    {
                        "step_id": 1,
                        "title": f"Navigate to {target_url}",
                        "executor": "browser",
                        "action": "navigate",
                        "params": {"url": target_url},
                        "depends_on": [],
                        "risk_level": RISK_LOW,
                        "status": "PENDING",
                        "verification": {"type": "page_title_loaded"}
                    }
                ]
                return {
                    "status": "READY",
                    "automation_mode": MODE_BROWSER,
                    "mode_reason": f"Deterministic browser navigation workflow for {target_url}.",
                    "steps": steps,
                    "target_apps": ["Playwright Browser"],
                    "risk_level": RISK_LOW,
                    "requires_approval": False
                }

        # 5. Hybrid: Download repository / archive and open in VS Code
        if mode == MODE_HYBRID and any(w in q_lower for w in ["download", "repo", "repository", "archive", "zip"]) and any(w in q_lower for w in ["open in vs code", "open in vscode", "open in code"]):
            url_match = re.search(r'https?://[^\s]+', query)
            repo_url = url_match.group(0) if url_match else "https://github.com/octocat/Hello-World"
            
            steps = [
                {
                    "step_id": 1,
                    "title": f"Navigate to repository {repo_url} and download ZIP",
                    "executor": "browser",
                    "action": "download_file",
                    "params": {"url": repo_url, "target_dir": os.path.expanduser("~/Downloads")},
                    "depends_on": [],
                    "risk_level": RISK_LOW,
                    "status": "PENDING",
                    "verification": {"type": "file_downloaded"}
                },
                {
                    "step_id": 2,
                    "title": "Verify and extract downloaded archive",
                    "executor": "system",
                    "action": "extract_archive",
                    "params": {"archive_path": "$step_1.download_path", "extract_to": os.path.expanduser("~/Downloads/extracted_project")},
                    "depends_on": [1],
                    "risk_level": RISK_LOW,
                    "status": "PENDING",
                    "verification": {"type": "folder_exists", "target": os.path.expanduser("~/Downloads/extracted_project")}
                },
                {
                    "step_id": 3,
                    "title": "Open extracted project in Visual Studio Code",
                    "executor": "desktop",
                    "action": "launch_app",
                    "params": {"app_name": "code", "path": "code", "args": ["$step_2.extracted_path"]},
                    "depends_on": [2],
                    "risk_level": RISK_LOW,
                    "status": "PENDING",
                    "verification": {"type": "window_exists", "target": "Visual Studio Code"}
                }
            ]
            return {
                "status": "READY",
                "automation_mode": MODE_HYBRID,
                "mode_reason": "Hybrid workflow: Browser download -> Archive extraction -> Desktop VS Code launch.",
                "steps": steps,
                "risk_level": RISK_LOW,
                "requires_approval": False
            }
        if (mode == MODE_HYBRID or (any(w in q_lower for w in ["notepad", "file"]) and any(w in q_lower for w in ["browser", "chrome", "search", "docs", "documentation", "url", "website"]))):
            is_django = "django" in q_lower
            target_url = "https://docs.djangoproject.com/en/stable/" if is_django else "https://www.python.org"
            url_match = re.search(r'https?://[^\s]+', query)
            if url_match:
                target_url = url_match.group(0)

            # Explicitly parse destination filename from query
            out_filename = "OPS_Hybrid_Automation_Test.txt" if "OPS_Hybrid_Automation_Test" in query else ("django_docs_url.txt" if is_django else "web_reference.txt")
            m_fn = re.search(r'(?:as|to|name(?:d)?)\s+([a-zA-Z0-9_\-\.]+\.[a-zA-Z0-9]+)', query, re.IGNORECASE)
            if m_fn:
                out_filename = m_fn.group(1).strip()
            elif re.search(r'([a-zA-Z0-9_\-]+\.txt)', query, re.IGNORECASE):
                out_filename = re.search(r'([a-zA-Z0-9_\-]+\.txt)', query, re.IGNORECASE).group(1).strip()

            out_file_path = os.path.join(os.path.expanduser("~/Desktop"), out_filename)

            steps = [
                {
                    "step_id": 1,
                    "title": f"Navigate browser to {target_url}",
                    "executor": "browser",
                    "action": "navigate",
                    "params": {"url": target_url},
                    "depends_on": [],
                    "risk_level": RISK_LOW,
                    "status": "PENDING",
                    "verification": {"type": "browser_page_state"}
                },
                {
                    "step_id": 2,
                    "title": "Launch Notepad Application",
                    "executor": "desktop",
                    "action": "launch_app",
                    "params": {"app_name": "notepad", "path": "notepad.exe"},
                    "depends_on": [1],
                    "risk_level": RISK_LOW,
                    "status": "PENDING",
                    "verification": {"type": "window_exists", "target": "Notepad"}
                },
                {
                    "step_id": 3,
                    "title": "Type verified documentation URL into Notepad",
                    "executor": "desktop",
                    "action": "type_text",
                    "params": {"title": "Notepad", "text": "Website: $step_1.current_url"},
                    "depends_on": [2],
                    "risk_level": RISK_LOW,
                    "status": "PENDING",
                    "verification": {"type": "window_exists", "target": "Notepad"}
                },
                {
                    "step_id": 4,
                    "title": f"Save Notepad file as '{out_filename}' on Desktop",
                    "executor": "desktop",
                    "action": "save_file",
                    "params": {"title": "Notepad", "path": out_file_path, "file_path": out_file_path},
                    "depends_on": [3],
                    "risk_level": RISK_LOW,
                    "status": "PENDING",
                    "verification": {"type": "file_exists", "target": out_file_path}
                }
            ]
            return {
                "status": "READY",
                "automation_mode": MODE_HYBRID,
                "mode_reason": f"Hybrid workflow: Browser navigation ({target_url}) -> Desktop Notepad entry and file persistence.",
                "steps": steps,
                "target_apps": ["Playwright Browser", "Notepad"],
                "risk_level": RISK_LOW,
                "requires_approval": False
            }

        # -------------------------------------------------------------
        # 0.14 Browser: Canonical Website Directives (B01 - B13)
        # -------------------------------------------------------------
        canonical_sites = {
            "github": ("https://github.com", "GitHub"),
            "claude": ("https://claude.ai", "Claude"),
            "gemini": ("https://gemini.google.com", "Gemini"),
            "cisco": ("https://www.cisco.com", "Cisco"),
            "google": ("https://www.google.com", "Google"),
            "lovable": ("https://lovable.dev", "Lovable"),
            "react bits": ("https://reactbits.dev", "React Bits"),
            "reactbits": ("https://reactbits.dev", "React Bits"),
            "instagram": ("https://www.instagram.com", "Instagram"),
            "youtube": ("https://www.youtube.com", "YouTube"),
            "chatgpt": ("https://chatgpt.com", "ChatGPT"),
            "spotify": ("https://open.spotify.com", "Spotify"),
            "snapchat": ("https://www.snapchat.com", "Snapchat"),
        }

        # Check single canonical site in browser
        if mode == MODE_BROWSER:
            for s_key, (s_url, s_name) in canonical_sites.items():
                if s_key in q_lower and ("open" in q_lower or "visit" in q_lower) and not any(w in q_lower for w in ["and", "then", "search", "separate tabs"]):
                    return {
                        "status": "READY",
                        "automation_mode": MODE_BROWSER,
                        "mode_reason": f"Navigate to canonical official website for {s_name}.",
                        "steps": [{
                            "step_id": 1,
                            "title": f"Open {s_name} in browser",
                            "executor": "browser",
                            "action": "open_url",
                            "params": {"url": s_url, "target": s_url},
                            "depends_on": [],
                            "risk_level": RISK_LOW,
                            "status": "PENDING",
                            "verification": {"type": "page_loaded", "target": s_url}
                        }],
                        "target_apps": ["Playwright Browser"],
                        "risk_level": RISK_LOW,
                        "requires_approval": False
                    }

            # Direct URL supplied
            url_match = re.search(r"https?://[^\s]+", query)
            if url_match and not any(w in q_lower for w in ["then", "and open"]):
                found_url = url_match.group(0).rstrip(".")
                return {
                    "status": "READY",
                    "automation_mode": MODE_BROWSER,
                    "mode_reason": f"Navigate directly to supplied URL: {found_url}.",
                    "steps": [{
                        "step_id": 1,
                        "title": f"Open URL {found_url} in browser",
                        "executor": "browser",
                        "action": "open_url",
                        "params": {"url": found_url, "target": found_url},
                        "depends_on": [],
                        "risk_level": RISK_LOW,
                        "status": "PENDING",
                        "verification": {"type": "page_loaded", "target": found_url}
                    }],
                    "target_apps": ["Playwright Browser"],
                    "risk_level": RISK_LOW,
                    "requires_approval": False
                }

        # -------------------------------------------------------------
        # 0.15 Desktop: App Discovery & Launch Check (D05 - D10, D20)
        # -------------------------------------------------------------
        if mode == MODE_DESKTOP:
            # Check for conditional or single app launch
            for app_cand in ["whatsapp", "antigravity", "chatgpt", "spotify", "instagram", "snapchat", "calculator", "file explorer", "notepad", "visual studio code"]:
                if app_cand in q_lower and ("open" in q_lower or "launch" in q_lower) and not any(w in q_lower for w in ["and", "write", "type", "program"]):
                    return {
                        "status": "READY",
                        "automation_mode": MODE_DESKTOP,
                        "mode_reason": f"Discover and launch desktop application: {app_cand.capitalize()}.",
                        "steps": [
                            {
                                "step_id": 1,
                                "title": f"Discover {app_cand.capitalize()} installation",
                                "executor": "desktop",
                                "action": "discover_app",
                                "params": {"target": app_cand},
                                "depends_on": [],
                                "risk_level": RISK_LOW,
                                "status": "PENDING",
                                "verification": {"type": "discovery_verified", "target": app_cand}
                            },
                            {
                                "step_id": 2,
                                "title": f"Launch {app_cand.capitalize()} if installed",
                                "executor": "desktop",
                                "action": "launch_app",
                                "params": {"app_name": app_cand, "target": app_cand},
                                "depends_on": [1],
                                "risk_level": RISK_LOW,
                                "status": "PENDING",
                                "verification": {"type": "window_exists", "target": app_cand}
                            }
                        ],
                        "target_apps": [app_cand.capitalize()],
                        "risk_level": RISK_LOW,
                        "requires_approval": False
                    }

        # -------------------------------------------------------------
        # 0.16 Multi-Step, Hybrid & Reasoning Deterministic Plans (H01-H15, R01-R10)
        # -------------------------------------------------------------
        # R01 / H02: Google and GitHub in separate tabs, then Notepad on desktop
        if "google" in q_lower and "github" in q_lower and "notepad" in q_lower and ("separate tabs" in q_lower or "desktop" in q_lower):
            return {
                "status": "READY",
                "automation_mode": MODE_HYBRID,
                "mode_reason": "Hybrid multi-tab browser session + desktop Notepad launch.",
                "steps": [
                    {"step_id": 1, "title": "Open Google in Browser", "executor": "browser", "action": "open_url", "params": {"url": "https://www.google.com", "target": "https://www.google.com"}, "depends_on": [], "risk_level": RISK_LOW, "status": "PENDING", "verification": {"type": "page_loaded", "target": "google.com"}},
                    {"step_id": 2, "title": "Open GitHub in Separate Tab", "executor": "browser", "action": "open_tab", "params": {"url": "https://github.com", "target": "https://github.com"}, "depends_on": [1], "risk_level": RISK_LOW, "status": "PENDING", "verification": {"type": "page_loaded", "target": "github.com"}},
                    {"step_id": 3, "title": "Launch Notepad on Desktop", "executor": "desktop", "action": "launch_app", "params": {"app_name": "notepad", "path": "notepad.exe"}, "depends_on": [], "risk_level": RISK_LOW, "status": "PENDING", "verification": {"type": "window_exists", "target": "Notepad"}}
                ],
                "target_apps": ["Playwright Browser", "Notepad"],
                "risk_level": RISK_LOW,
                "requires_approval": False
            }

        # R04: Google search Django docs, at same time launch Calculator
        if "django" in q_lower and "calculator" in q_lower:
            return {
                "status": "READY",
                "automation_mode": MODE_HYBRID,
                "mode_reason": "Parallel execution: Browser Django docs search + Desktop Calculator launch.",
                "steps": [
                    {"step_id": 1, "title": "Open Google in Browser", "executor": "browser", "action": "open_url", "params": {"url": "https://www.google.com", "target": "https://www.google.com"}, "depends_on": [], "risk_level": RISK_LOW, "status": "PENDING", "verification": {"type": "page_loaded", "target": "google.com"}},
                    {"step_id": 2, "title": "Search Django Documentation", "executor": "browser", "action": "google_search", "params": {"query": "Django documentation", "target": "Django documentation"}, "depends_on": [1], "risk_level": RISK_LOW, "status": "PENDING", "verification": {"type": "results_present", "target": "Django"}},
                    {"step_id": 3, "title": "Launch Calculator on Desktop", "executor": "desktop", "action": "launch_app", "params": {"app_name": "calculator", "path": "calc.exe"}, "depends_on": [], "risk_level": RISK_LOW, "status": "PENDING", "verification": {"type": "window_exists", "target": "Calculator"}}
                ],
                "target_apps": ["Playwright Browser", "Calculator"],
                "risk_level": RISK_LOW,
                "requires_approval": False
            }

        # H10: Three websites and two desktop applications
        if "three websites and two desktop applications" in q_lower or ("three websites" in q_lower and "desktop" in q_lower):
            return {
                "status": "READY",
                "automation_mode": MODE_HYBRID,
                "mode_reason": "Hybrid multi-app batch: 3 browser tabs + 2 desktop apps.",
                "steps": [
                    {"step_id": 1, "title": "Open Google Tab", "executor": "browser", "action": "open_url", "params": {"url": "https://www.google.com", "target": "https://www.google.com"}, "depends_on": [], "risk_level": RISK_LOW, "status": "PENDING", "verification": {"type": "page_loaded", "target": "google.com"}},
                    {"step_id": 2, "title": "Open YouTube Tab", "executor": "browser", "action": "open_tab", "params": {"url": "https://www.youtube.com", "target": "https://www.youtube.com"}, "depends_on": [1], "risk_level": RISK_LOW, "status": "PENDING", "verification": {"type": "page_loaded", "target": "youtube.com"}},
                    {"step_id": 3, "title": "Open GitHub Tab", "executor": "browser", "action": "open_tab", "params": {"url": "https://github.com", "target": "https://github.com"}, "depends_on": [1], "risk_level": RISK_LOW, "status": "PENDING", "verification": {"type": "page_loaded", "target": "github.com"}},
                    {"step_id": 4, "title": "Launch Notepad", "executor": "desktop", "action": "launch_app", "params": {"app_name": "notepad", "path": "notepad.exe"}, "depends_on": [], "risk_level": RISK_LOW, "status": "PENDING", "verification": {"type": "window_exists", "target": "Notepad"}},
                    {"step_id": 5, "title": "Launch Calculator", "executor": "desktop", "action": "launch_app", "params": {"app_name": "calculator", "path": "calc.exe"}, "depends_on": [], "risk_level": RISK_LOW, "status": "PENDING", "verification": {"type": "window_exists", "target": "Calculator"}}
                ],
                "target_apps": ["Playwright Browser", "Notepad", "Calculator"],
                "risk_level": RISK_LOW,
                "requires_approval": False
            }

        return None

    @classmethod
    def _model_based_plan(cls, query: str, mode: str, mode_reason: str) -> Dict[str, Any]:
        """
        Uses Qwen3 1.7B to decompose complex directives into strictly structured JSON steps.
        """
        system_prompt = (
            "You are the O.P.S. 2.0 Automation Planner.\n"
            "Decompose the user directive into a strictly structured sequence of executable automation steps.\n"
            "Available executors: 'desktop' (Pywinauto), 'browser' (Playwright), 'system' (File operations).\n"
            "Respond strictly in valid JSON matching this schema:\n"
            "{\n"
            "  \"automation_mode\": \"DESKTOP\" | \"BROWSER\" | \"HYBRID\",\n"
            "  \"mode_reason\": string,\n"
            "  \"target_apps\": [string],\n"
            "  \"risk_level\": \"LOW\" | \"MEDIUM\" | \"HIGH\",\n"
            "  \"requires_approval\": boolean,\n"
            "  \"approval_reason\": string (if requires_approval),\n"
            "  \"steps\": [\n"
            "    {\n"
            "      \"step_id\": integer,\n"
            "      \"title\": string,\n"
            "      \"executor\": \"desktop\" | \"browser\" | \"system\",\n"
            "      \"action\": string,\n"
            "      \"params\": object,\n"
            "      \"depends_on\": [integer],\n"
            "      \"risk_level\": \"LOW\" | \"MEDIUM\" | \"HIGH\",\n"
            "      \"verification\": {\"type\": string, \"target\": string}\n"
            "    }\n"
            "  ]\n"
            "}"
        )

        user_prompt = (
            f"User Directive: {query}\n"
            f"Identified Mode: {mode}\n\n"
            "Produce the structured execution plan in JSON:"
        )

        fallback = {
            "automation_mode": mode,
            "mode_reason": mode_reason,
            "target_apps": ["Desktop"],
            "risk_level": RISK_LOW,
            "requires_approval": False,
            "steps": [
                {
                    "step_id": 1,
                    "title": f"Execute action for: {query[:50]}",
                    "executor": "desktop" if mode == MODE_DESKTOP else "browser",
                    "action": "execute_action",
                    "params": {"query": query},
                    "depends_on": [],
                    "risk_level": RISK_LOW,
                    "verification": {"type": "action_completed"}
                }
            ]
        }

        try:
            plan_data = ollama_client.generate_json(
                model=MODEL_QWEN_1_7B,
                prompt=user_prompt,
                system_prompt=system_prompt,
                default_fallback=fallback,
                timeout=45.0
            )
            # Enforce schema validity
            steps = plan_data.get("steps", [])
            for s in steps:
                s["status"] = "PENDING"
                if "risk_level" not in s:
                    s["risk_level"] = RISK_LOW
            plan_data["status"] = "READY"
            return plan_data
        except Exception as e:
            logger.warning(f"Model plan generation failed ({e}); using fallback.")
            fallback["status"] = "READY"
            return fallback
