"""
O.P.S. 2.0 Safety Policy & Human-in-the-Loop Approval Manager
Enforces strict safety barriers before consequential or irreversible operations:
- File or directory deletion
- Software installation / uninstallation
- File overwriting
- External form submission with sensitive data
- System setting modifications
- Privileged operations
"""

import re
import uuid
import time
import logging
from typing import Dict, Any, List, Optional, Tuple
from django.utils import timezone
from research_system.models import PendingApproval, Conversation
from research_system.events.event_bus import event_bus

logger = logging.getLogger("OPS.SafetyPolicy")

# High-Risk Actions that MUST trigger Human-in-the-Loop approval
CONSEQUENTIAL_ACTIONS = {
    "delete_file": "Permanent deletion of file(s)",
    "delete_folder": "Permanent deletion of folder(s)",
    "install_software": "Installation of system software or packages",
    "uninstall_software": "Removal of installed software",
    "overwrite_file": "Overwriting existing file content",
    "submit_form": "Submitting external web form or transactions",
    "send_email": "Transmitting external electronic messages",
    "modify_system_setting": "Modifying Windows system registry or environment settings",
    "execute_privileged": "Executing administrative or elevated processes"
}

# High-Risk Keywords in Directives
CONSEQUENTIAL_KEYWORDS = [
    r"\b(?:delete|remove|erase|destroy|purge|wipe)\b.*?\b(?:file|files|folder|folders|dir|directory|data)\b",
    r"\b(?:install|uninstall|setup)\b",
    r"\b(?:taskkill|kill\s+process|shutdown|format|repartition)\b",
    r"\boverwrite\b.*?\b(?:file|document|code)\b",
    r"\b(?:submit|send|buy|purchase|pay|commit)\b",
    r"\b(?:format|repartition)\s+[a-zA-Z]:\b"
]


class SafetyPolicy:
    """
    Evaluates automation tasks and individual steps for safety risks,
    raising Human-in-the-Loop gates whenever consequential actions are detected.
    """

    @classmethod
    def evaluate_step_risk(cls, action: str, params: Dict[str, Any], query: str = "") -> Tuple[str, bool, str]:
        """
        Evaluates risk for an individual step.
        Returns: (risk_level, requires_approval, reason)
        """
        action_clean = action.lower().strip()
        
        # 1. Direct match on consequential action verbs
        if action_clean in CONSEQUENTIAL_ACTIONS:
            desc = CONSEQUENTIAL_ACTIONS[action_clean]
            target = params.get("target") or params.get("path") or params.get("file_path") or "unspecified target"
            return "HIGH", True, f"Operation requires explicit authorization: {desc} ({target})."

        # 2. Check parameters for dangerous operations
        if action_clean == "create_folder" and params.get("overwrite"):
            return "HIGH", True, "Overwriting existing folder requires explicit approval."

        if action_clean == "click" and any(k in str(params).lower() for k in ["submit", "purchase", "pay", "delete", "confirm order"]):
            return "HIGH", True, "Submitting external transaction or destructive web action requires approval."

        # 3. Check query context for destructive keywords
        for pattern in CONSEQUENTIAL_KEYWORDS:
            if re.search(pattern, query, re.IGNORECASE):
                return "HIGH", True, "Directive contains destructive or consequential operations requiring authorization."

        return "LOW", False, "Safe, non-destructive operation."

    @classmethod
    def create_approval_request(
        cls,
        task_id: str,
        conversation_id: str,
        step_id: int,
        action: str,
        reason: str,
        consequences: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> PendingApproval:
        """
        Registers a formal Human-in-the-Loop pending approval record and emits event.
        """
        approval_id = f"appr_{int(time.time())}_{uuid.uuid4().hex[:6]}"
        conv = Conversation.objects.filter(conversation_id=conversation_id).first()

        default_consequences = consequences or [
            f"Execute potentially consequential action: '{action}' on step #{step_id}.",
            "Changes made during this step may modify or permanently remove system resources.",
            "Verify the target and operational parameters before accepting."
        ]

        appr = PendingApproval.objects.create(
            approval_id=approval_id,
            conversation=conv,
            target_conversation_id=conversation_id,
            execution_id=task_id,
            action_type=f"AUTOMATION_{action.upper()}",
            status="PENDING",
            description=reason,
            metadata={
                "task_id": task_id,
                "step_id": step_id,
                "action": action,
                "consequences": default_consequences,
                **(metadata or {})
            }
        )

        # Publish Approval Required Event to Cockpit & EventBus
        event_bus.publish(
            request_id=f"req_{approval_id}",
            execution_id=task_id,
            conversation_id=conversation_id,
            node_id="safety_policy_gate",
            component_name="Safety & HITL Policy Gate",
            component_type="approval_controller",
            event_type="APPROVAL_REQUIRED",
            execution_status="WAITING_FOR_APPROVAL",
            safe_task_summary=f"Safety Gate: {reason}",
            approval_id=approval_id,
            task_id=task_id,
            step_id=step_id,
            action=action,
            consequences=default_consequences,
            timestamp=time.time()
        )

        logger.info(f"Generated HITL Approval Gate: id={approval_id} task={task_id} action={action}")
        return appr

    @classmethod
    def build_automation_hitl_details(
        cls,
        query: str,
        steps: List[Dict[str, Any]],
        mode: str = "AUTOMATION"
    ) -> Dict[str, Any]:
        """
        Constructs comprehensive, user-friendly Human-in-the-Loop approval metadata
        covering Action Summary, Target, Execution Plan, Input/Content, Expected Result,
        Destructive classification, and Plan Hash.
        """
        import hashlib
        import json

        q_lower = query.lower()
        targets = []
        target_app = ""
        target_url = ""
        target_file = ""
        input_content = ""
        is_destructive = False

        # 1. Inspect Steps for targets, actions, and inputs
        formatted_ops = []
        for idx, step in enumerate(steps, 1):
            action = step.get("action", "")
            params = step.get("params", {})
            title = step.get("title", f"Step {idx}")
            executor = step.get("executor", "system")

            # Extract URLs
            if "url" in params:
                u = params["url"]
                if u and u not in targets:
                    targets.append(u)
                    target_url = u

            # Extract Apps
            if "app_name" in params:
                app = params["app_name"]
                if app and app not in targets:
                    targets.append(app)
                    target_app = app

            # Extract Files / Folders
            for f_key in ["file_path", "path", "filename", "project_path", "folder_path"]:
                if f_key in params and params[f_key]:
                    fp = params[f_key]
                    if fp not in targets:
                        targets.append(fp)
                        target_file = fp

            # Extract Input / Content
            if "text" in params and params["text"]:
                input_content = params["text"]
            elif "code" in params and params["code"]:
                input_content = params["code"]
            elif "query" in params and params["query"]:
                input_content = f"Search query: \"{params['query']}\""

            # Check for Destructive operations
            if action in ["delete_file", "delete_folder", "delete_code_region"] or "delete" in action.lower():
                is_destructive = True
            if params.get("overwrite"):
                is_destructive = True

            # Formulate clear user-facing operation label
            if action == "launch_app":
                op_desc = f"Launch application: {params.get('app_name', 'Desktop App')}"
            elif action == "navigate":
                op_desc = f"Navigate browser to {params.get('url', 'URL')}"
            elif action == "google_search":
                op_desc = f"Enter search query on Google: '{params.get('query', '')}'"
            elif action == "youtube_search":
                op_desc = f"Search YouTube for: '{params.get('query', '')}' (inspect results without auto-playing)"
            elif action == "youtube_search_and_play":
                op_desc = f"Search YouTube for '{params.get('query', '')}' and play top result"
            elif action == "youtube_pause":
                op_desc = "Pause YouTube video playback"
            elif action == "youtube_resume":
                op_desc = "Resume YouTube video playback"
            elif action == "spotify_search":
                op_desc = f"Search Spotify for track/artist: '{params.get('query', '')}'"
            elif action == "spotify_play":
                op_desc = f"Play top Spotify result for: '{params.get('query', '')}'"
            elif action == "instagram_reels":
                op_desc = "Navigate browser to Instagram Reels feed"
            elif action == "instagram_dms":
                op_desc = "Open Instagram Direct Messages interface (verify authorization)"
            elif action == "type_text":
                txt = params.get("text", "")
                op_desc = f"Enter text ({len(txt)} chars) into active application window"
            elif action in ["save_file", "save_as"]:
                op_desc = f"Save file to disk at: {params.get('file_path', 'target destination')}"
            elif action == "create_file":
                op_desc = f"Create file on disk at: {params.get('file_path', 'target path')}"
            elif action == "create_folder":
                op_desc = f"Create directory on disk at: {params.get('folder_path', 'target path')}"
            elif action == "delete_file":
                op_desc = f"Permanently delete file at: {params.get('file_path', 'target path')}"
            elif action == "delete_folder":
                op_desc = f"Permanently delete folder and contents at: {params.get('folder_path', 'target path')}"
            elif action == "vscode_open_project":
                op_desc = f"Open project workspace in Visual Studio Code at: {params.get('project_path', 'workspace')}"
            elif action == "vscode_create_code_file":
                op_desc = f"Create code file '{params.get('filename', 'file')}' in VS Code project"
            else:
                op_desc = title

            formatted_ops.append(f"{idx}. {op_desc}")

        # If query contains explicit delete words, flag destructive
        if any(w in q_lower for w in ["delete", "remove file", "remove folder", "erase", "destroy"]):
            is_destructive = True

        # 2. Action Summary
        if "google" in q_lower and "search" in q_lower:
            action_summary = "Open Google and perform an automated search."
            if not target_app: target_app = "Google Chrome"
            if not target_url: target_url = "https://www.google.com/"
        elif "youtube" in q_lower and ("play" in q_lower or "song" in q_lower):
            action_summary = "Open YouTube and play requested media."
            if not target_app: target_app = "Google Chrome"
            if not target_url: target_url = "https://www.youtube.com/"
        elif "youtube" in q_lower:
            action_summary = "Open YouTube and search for requested videos."
            if not target_app: target_app = "Google Chrome"
            if not target_url: target_url = "https://www.youtube.com/"
        elif "spotify" in q_lower:
            action_summary = "Open Spotify and control music playback."
            if not target_app: target_app = "Spotify"
        elif "instagram" in q_lower and "reel" in q_lower:
            action_summary = "Navigate to Instagram Reels."
            if not target_app: target_app = "Playwright Chromium"
            if not target_url: target_url = "https://www.instagram.com/reels/"
        elif "instagram" in q_lower and ("message" in q_lower or "dm" in q_lower):
            action_summary = "Open Instagram Direct Messages."
            if not target_app: target_app = "Playwright Chromium"
            if not target_url: target_url = "https://www.instagram.com/direct/inbox/"
        elif "vs code" in q_lower or "vscode" in q_lower:
            action_summary = "Create and write source code in Visual Studio Code."
            if not target_app: target_app = "Visual Studio Code"
        elif "notepad" in q_lower:
            action_summary = "Open Notepad, enter text/code, and save document."
            if not target_app: target_app = "Windows Notepad"
        elif is_destructive:
            action_summary = f"Delete specified {'folder' if 'folder' in q_lower or 'dir' in q_lower else 'file'} from disk."
        elif "create" in q_lower and ("file" in q_lower or "folder" in q_lower):
            action_summary = "Create file system resources at specified path."
        else:
            action_summary = f"Execute {mode.capitalize()} automation directive: '{query[:60]}'."

        # If steps did not yield target_file, inspect query for absolute/relative file paths
        if not target_file:
            import re
            m_path = re.search(r'([A-Za-z]:\\[^\s"\']+|[A-Za-z]:/[^\s"\']+|\b[\w\.-]+\.(?:py|txt|json|md|js|ts|html|css)\b)', query)
            if m_path:
                target_file = m_path.group(1).strip()
                if target_file not in targets:
                    targets.append(target_file)

        # 3. Target Formulation
        target_components = []
        if target_app: target_components.append(f"Application: {target_app}")
        if target_url: target_components.append(f"Website: {target_url}")
        if target_file: target_components.append(f"File/Folder: {target_file}")
        if not target_components:
            if targets:
                target_components = [f"Target: {', '.join(targets[:2])}"]
            else:
                target_components = [f"Target: System Automation ({mode})"]
        target_desc = " | ".join(target_components)

        # 4. Expected Result
        if "google" in q_lower:
            expected_result = "Search results rendered and verified in browser."
        elif "youtube" in q_lower and "play" in q_lower:
            expected_result = "Requested media playing in browser with verified playback controls."
        elif "youtube" in q_lower:
            expected_result = "Search results displayed without auto-playing media."
        elif "spotify" in q_lower:
            expected_result = "Spotify search results rendered and audio track playback engaged."
        elif "instagram" in q_lower:
            expected_result = "Instagram view active (subject to valid user session authentication)."
        elif "vs code" in q_lower or "vscode" in q_lower:
            expected_result = "Visual Studio Code workspace active with requested code file saved."
        elif "notepad" in q_lower and ("save" in q_lower or target_file):
            expected_result = f"Document saved and verified on disk at destination."
        elif "notepad" in q_lower:
            expected_result = "Notepad launched with requested text entered into editor."
        elif is_destructive:
            expected_result = "Target file system item permanently removed."
        elif "create" in q_lower:
            expected_result = "New file/folder created and verified on disk."
        else:
            expected_result = f"All {len(steps)} planned operations executed and empirically verified."

        # 5. Plan Hash for idempotency & tamper-proof authorization
        plan_str = json.dumps({"query": query, "targets": targets, "ops": formatted_ops}, sort_keys=True)
        plan_hash = hashlib.sha256(plan_str.encode("utf-8")).hexdigest()[:16]

        return {
            "action_summary": action_summary,
            "target": target_desc,
            "target_application": target_app,
            "target_url": target_url,
            "target_file_path": target_file,
            "execution_plan": formatted_ops,
            "input_content": input_content,
            "expected_result": expected_result,
            "is_destructive": is_destructive,
            "risk_level": "HIGH" if is_destructive else "STANDARD",
            "plan_hash": plan_hash
        }
