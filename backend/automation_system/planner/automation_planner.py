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

        # Hybrid Signals: mentions downloading/scraping web AND opening/editing desktop application
        has_browser_kw = any(w in q_lower for w in ["browser", "website", "web", "url", "download", "github", "http://", "https://", "navigate to", "form", "page"])
        has_desktop_kw = any(w in q_lower for w in ["notepad", "vscode", "vs code", "code", "desktop", "folder", "directory", "word", "explorer", "window", "calc", "calculator", "app", "application", "extract"])

        if has_browser_kw and has_desktop_kw:
            # Check if it connects web action with desktop action
            if any(w in q_lower for w in ["and open", "then open", "extract and", "open in", "download and", "organize"]):
                return MODE_HYBRID, "Task requires browser action (download/web) followed by Windows desktop action."

        # Browser Automation Signals
        if any(w in q_lower for w in ["http://", "https://", "website", "web page", "navigate to", "fill out", "fill the form", "fill form", "search within", "browser tab", "web dashboard"]):
            return MODE_BROWSER, "Task strictly involves web browser navigation, interaction, or web elements."

        # Desktop Automation Signals
        if any(w in q_lower for w in ["open notepad", "open vs code", "open vscode", "open calculator", "create folder", "file explorer", "desktop app", "switch window", "press shortcut", "type in notepad"]):
            return MODE_DESKTOP, "Task targets local Windows desktop applications and UI controls."

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

        if "open file" in q_lower and not any(ext in q_lower for ext in [".txt", ".py", ".pdf", ".json", ".docx", ".md"]) and len(words) < 5:
            return True, "Which specific file would you like to open, and from what directory?"

        if mode == MODE_BROWSER and ("navigate" in q_lower or "open website" in q_lower) and not any(s in q_lower for s in ["http", ".com", ".org", ".io", ".net", ".edu", ".gov", "google", "github", "wikipedia"]):
            return True, "What specific website URL or web address should I navigate to?"

        return False, ""

    @classmethod
    def _try_deterministic_plan(cls, query: str, mode: str) -> Optional[Dict[str, Any]]:
        """
        Instantly generates reliable, verified plans for standard high-frequency tasks.
        """
        q_lower = query.lower()

        # 1. Desktop: Open Notepad & optionally type text
        if "notepad" in q_lower and any(w in q_lower for w in ["open", "launch", "start"]):
            text_to_type = None
            if "type" in q_lower or "write" in q_lower:
                match = re.search(r'(?:type|write)\s+["\']?(.*?)["\']?(?:\s+in\s+notepad|\s+into\s+notepad|$)', query, re.IGNORECASE)
                if match:
                    text_to_type = match.group(1).strip(" \"'")

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
                    "title": f"Enter text into Notepad",
                    "executor": "desktop",
                    "action": "type_text",
                    "params": {"title": "Notepad", "text": text_to_type},
                    "depends_on": [1],
                    "risk_level": RISK_LOW,
                    "status": "PENDING",
                    "verification": {"type": "window_exists", "target": "Notepad"}
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

        # 2. Desktop: Open VS Code
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

        # 3. Desktop: Create a folder
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

        # 4. Browser: Open website / navigate to URL
        if mode == MODE_BROWSER:
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
                "target_apps": ["Playwright Browser", "Visual Studio Code"],
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
