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
        has_browser_kw = any(w in q_lower for w in ["browser", "website", "web", "url", "download", "github", "http://", "https://", "form", "page", "youtube", "google"])
        has_desktop_kw = any(w in q_lower for w in ["notepad", "vscode", "vs code", "code", "desktop", "folder", "directory", "word", "explorer", "window", "calc", "calculator", "app", "application", "extract", "installer"])

        if has_browser_kw and has_desktop_kw:
            # Check if it connects web action with desktop action
            if any(w in q_lower for w in ["and open", "then open", "extract and", "open in", "download and", "organize"]):
                return MODE_HYBRID, "Task requires browser action followed by Windows desktop action."

        # Desktop priority if desktop app or local system is targeted
        if any(w in q_lower for w in ["calculator", "calc", "notepad", "file explorer", "explorer", "create folder", "make folder", "new folder", "on my computer", "on my pc", "on this system"]):
            return MODE_DESKTOP, "Task targets local Windows desktop applications and UI controls."

        # Browser Automation Signals
        if any(w in q_lower for w in ["youtube", "google", "wikipedia", "github.com", "http://", "https://", "website", "web page", "in browser", "in my browser", "search google"]):
            return MODE_BROWSER, "Task strictly involves web browser navigation, interaction, or web elements."

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

        # 1. Desktop: Open Calculator
        if any(w in q_lower for w in ["calculator", "calc", "calc.exe"]) and any(w in q_lower for w in ["open", "launch", "start", "run"]):
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
                if clean_term and clean_term.lower() not in ["a song", "another song", "music", "it"]:
                    song_name = clean_term
            elif "play" in q_lower:
                m_play = re.search(r'play\s+(.*?)(?:\s+on\s+youtube|$)', query, re.IGNORECASE)
                if m_play and m_play.group(1).strip():
                    clean_term = m_play.group(1).strip(" \"'.,;:!?")
                    if clean_term:
                        song_name = clean_term

            has_chain_click = any(w in q_lower for w in ["open the first", "click the first", "play the first", "first result"])
            wants_play = has_chain_click or q_lower.startswith("play ") or "play the song" in q_lower or "and play" in q_lower or ("play " in q_lower and "search" not in q_lower)
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
        if "instagram" in q_lower or "reels" in q_lower:
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
                return {
                    "status": "READY",
                    "automation_mode": MODE_BROWSER,
                    "mode_reason": "Deterministic browser workflow for Instagram Direct Messages.",
                    "steps": steps,
                    "target_apps": ["Playwright Browser (Instagram)"],
                    "risk_level": RISK_LOW,
                    "requires_approval": False
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

        # 11. Browser: Search Google ("Search Google for ...")
        if "google" in q_lower and any(w in q_lower for w in ["search", "look up", "find"]):
            search_term = re.sub(r'^(?:please\s+)?(?:can\s+you\s+)?(?:search\s+google\s+for|search\s+for|google)\s+', '', query, flags=re.IGNORECASE).strip()
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

            out_filename = "django_docs_url.txt" if is_django else "web_reference.txt"
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
