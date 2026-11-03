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
    r"\b(?:install|uninstall|setup)\b.*?\b(?:software|application|package|driver|installer)\b",
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
