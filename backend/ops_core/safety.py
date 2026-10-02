"""
O.P.S. Execution Safety & Validation Gatekeeper Subsystem
Enforces strict security checks, policy rule matching, interactive human-in-the-loop
permission prompts, and immutable database audit logging.
"""

import re
import time
import logging
import asyncio
from typing import Dict, Any, Tuple, Optional
from django.utils import timezone
from channels.db import database_sync_to_async

logger = logging.getLogger("ops.safety")

# Default hardcoded forbidden patterns (Critical Risk)
DEFAULT_FORBIDDEN_CMD_PATTERNS = [
    r"rm\s+-[rRfF]+\s+[/~]",              # rm -rf / or ~
    r"rm\s+-rf\s+\*",                     # rm -rf *
    r"format\s+[a-zA-Z]:",                # format C:
    r"del\s+/[fFsSqQ\s]+[a-zA-Z]:\\",     # del /f /s C:\
    r"drop\s+database",                   # drop database
    r"shutdown(\.exe)?\s+",               # shutdown commands
    r"reg\s+delete",                      # registry deletion
    r":\(\)\{\s*:\|:&\s*\};:",           # bash fork bomb
    r"mkfs(\.[a-z0-9]+)?\s+",             # format filesystem
    r"dd\s+if=.*of=/dev/[a-z]+",         # raw disk write
]

# Sensitive operations that require human authorization
SENSITIVE_ACTIONS = {
    "launch_app": "HIGH",
    "open_browser_search": "HIGH",
    "open_file_or_folder": "HIGH",
    "open_in_vscode": "HIGH",
    "run_claude_routine": "HIGH",
    "browser_dom_task": "HIGH",
    "run_terminal_cmd": "HIGH",
    "git_push": "HIGH",
    "git_commit": "MEDIUM",
    "edit_file": "MEDIUM",
    "delete_file": "HIGH",
    "dom_click": "HIGH",
    "dom_type": "HIGH",
    "gui_click": "MEDIUM",
    "gui_type": "MEDIUM",
}

# Safe operations that can execute automatically
SAFE_ACTIONS = {
    "web_scrape": "LOW",
    "take_screenshot": "LOW",
    "read_file": "LOW",
    "list_directory": "LOW",
    "get_status": "LOW",
    "web_search": "LOW",
    "crawl_research": "LOW",
    "crawl_person_bio": "LOW",
    "crawl_concept_theory": "LOW",
    "crawl_news_live": "LOW",
}


class OPSSafetyGatekeeper:

    @staticmethod
    def assess_risk(action: str, params: Dict[str, Any]) -> Tuple[str, str]:
        """
        Determines the risk level of an action.
        Returns: (risk_level: 'LOW'|'MEDIUM'|'HIGH'|'CRITICAL', reason: str)
        """
        cmd = params.get("command", "")
        url = params.get("url", "")

        # 1. Check for Critical Destructive Patterns
        if action == "run_terminal_cmd" or cmd:
            for pattern in DEFAULT_FORBIDDEN_CMD_PATTERNS:
                if re.search(pattern, cmd, re.IGNORECASE):
                    return "CRITICAL", f"Command matched critical security blacklist pattern: '{pattern}'"

        # 2. Check for URL validity
        if action in ["web_scrape", "dom_click", "dom_type"] or url:
            if url and not (url.startswith("http://") or url.startswith("https://") or url.startswith("file://")):
                return "CRITICAL", f"Invalid or unsafe URL protocol: '{url}'"

        # 3. Check action category risk
        if action == "run_claude_routine":
            return "HIGH", "Permission required to execute Claude workflow (cd D:\\freellmapi -> npm run dev -> launch Claude)."

        if action == "open_file_or_folder":
            target = params.get("target") or params.get("path", "file/folder")
            return "HIGH", f"Permission required to open file or folder: '{target}'."

        if action == "open_in_vscode":
            target = params.get("target") or params.get("file", "file")
            return "HIGH", f"Permission required to open in VS Code: '{target}'."

        if action == "browser_dom_task":
            site = params.get("site", "website")
            query = params.get("query", "")
            return "HIGH", f"Permission required for browser DOM task on {site} ('{query}')."

        if action == "launch_app":
            app = params.get("app") or params.get("application") or params.get("target", "item")
            return "HIGH", f"Permission required to open/launch: '{app}'."

        if action == "open_browser_search":
            query = params.get("query", "")
            return "HIGH", f"Permission required to open browser search: '{query}'."

        if action in SAFE_ACTIONS:
            return SAFE_ACTIONS[action], "Safe read-only operation."

        if action in SENSITIVE_ACTIONS:
            return SENSITIVE_ACTIONS[action], f"Action '{action}' requires authorization."

        # Default for unknown actions
        return "MEDIUM", f"Unclassified action '{action}' evaluated with default medium risk."

    @classmethod
    def validate_action_sync(
        cls,
        agent_name: str,
        action: str,
        params: Dict[str, Any],
        task_id: Optional[str] = None
    ) -> Tuple[bool, str, str]:
        """
        Synchronously validates an action against safety policies.
        Returns: (is_approved: bool, risk_level: str, reason: str)
        """
        risk_level, reason = cls.assess_risk(action, params)

        if risk_level == "CRITICAL":
            cls.record_audit_log_sync(
                agent_name=agent_name,
                action_type=action,
                target=params.get("command") or params.get("url") or params.get("target", ""),
                parameters=params,
                status="BLOCKED",
                stderr=reason,
                task_id=task_id
            )
            return False, risk_level, reason

        if risk_level == "LOW":
            return True, risk_level, "Auto-approved safe action."

        # Medium / High requires explicit interactive approval or task whitelist
        return True, risk_level, reason

    @classmethod
    def validate_tool_call(cls, tool_name: str, params: Dict[str, Any]) -> Tuple[bool, str]:
        """Backward-compatible validation helper."""
        is_approved, _, reason = cls.validate_action_sync(
            agent_name="ToolCaller",
            action=tool_name,
            params=params
        )
        return is_approved, reason

    @classmethod
    async def validate_and_authorize_async(
        cls,
        agent_name: str,
        action: str,
        params: Dict[str, Any],
        reason_explanation: str = "AI Agent requested execution",
        task_id: Optional[str] = None,
        timeout_seconds: int = 60
    ) -> Dict[str, Any]:
        """
        Complete async security gate:
        1. Evaluates risk.
        2. If CRITICAL -> Blocks immediately & logs to DB.
        3. If LOW -> Auto-approves & logs.
        4. If MEDIUM/HIGH -> Creates PermissionRequest DB record, broadcasts WebSocket modal, awaits user decision.
        """
        from ops_core.models import PermissionRequest, RiskLevel, PermissionStatus, PermissionDecision
        from ops_core.services.permission_manager import OPSPermissionManager

        risk_level, risk_reason = cls.assess_risk(action, params)
        command_str = params.get("command") or params.get("url") or params.get("selector") or str(params)

        # 1. Hard Block for Critical Patterns
        if risk_level == "CRITICAL":
            await database_sync_to_async(cls._create_audit_record)(
                agent_name=agent_name,
                action_type=action,
                target=command_str,
                parameters=params,
                status="BLOCKED",
                stderr=risk_reason,
                task_id=task_id
            )
            await database_sync_to_async(PermissionRequest.objects.create)(
                task_id=task_id,
                agent_name=agent_name,
                action_type=action,
                command_text=command_str,
                reason=risk_reason,
                risk_level=RiskLevel.CRITICAL,
                status=PermissionStatus.BLOCKED_POLICY,
                decision=PermissionDecision.AUTO_BLOCKED,
                resolved_at=timezone.now()
            )
            return {
                "approved": False,
                "decision": "AUTO_BLOCKED",
                "risk_level": risk_level,
                "reason": risk_reason
            }

        # 2. Auto-Approve Low Risk
        if risk_level == "LOW":
            return {
                "approved": True,
                "decision": "AUTO_APPROVED",
                "risk_level": risk_level,
                "reason": "Low risk read-only action."
            }

        # 3. Interactive Human-in-the-Loop for Medium & High Risk
        req_record = await database_sync_to_async(PermissionRequest.objects.create)(
            task_id=task_id,
            agent_name=agent_name,
            action_type=action,
            command_text=command_str,
            reason=reason_explanation,
            risk_level=risk_level,
            status=PermissionStatus.PENDING,
            timeout_seconds=timeout_seconds
        )

        perm_result = await OPSPermissionManager.request_permission(
            agent=agent_name,
            action=action,
            command=command_str,
            reason=reason_explanation,
            risk_level=risk_level,
            task_id=task_id,
            timeout_seconds=timeout_seconds,
            request_id=str(req_record.request_id)
        )

        decision = perm_result.get("decision", "DENY")
        approved = perm_result.get("approved", False)

        # Update DB record with resolution
        status_map = {
            "ALLOW_ONCE": PermissionStatus.APPROVED,
            "ALLOW_TASK": PermissionStatus.APPROVED,
            "DENY": PermissionStatus.DENIED,
            "TIMEOUT": PermissionStatus.TIMEOUT,
        }
        req_record.status = status_map.get(decision, PermissionStatus.DENIED)
        req_record.decision = decision if decision in PermissionDecision.values else None
        req_record.resolved_at = timezone.now()
        await database_sync_to_async(req_record.save)()

        return {
            "approved": approved,
            "decision": decision,
            "risk_level": risk_level,
            "request_id": str(req_record.request_id),
            "reason": perm_result.get("reason", "")
        }

    @staticmethod
    def _create_audit_record(
        agent_name: str,
        action_type: str,
        target: str = "",
        parameters: Optional[Dict[str, Any]] = None,
        status: str = "SUCCESS",
        stdout: str = "",
        stderr: str = "",
        duration_ms: int = 0,
        task_id: Optional[str] = None
    ):
        from ops_core.models import ExecutionAuditLog
        return ExecutionAuditLog.objects.create(
            task_id=task_id,
            agent_name=agent_name,
            action_type=action_type,
            target=target,
            parameters=parameters or {},
            status=status,
            stdout=stdout,
            stderr=stderr,
            duration_ms=duration_ms,
            executed_at=timezone.now()
        )

    @classmethod
    def record_audit_log_sync(
        cls,
        agent_name: str,
        action_type: str,
        target: str = "",
        parameters: Optional[Dict[str, Any]] = None,
        status: str = "SUCCESS",
        stdout: str = "",
        stderr: str = "",
        duration_ms: int = 0,
        task_id: Optional[str] = None
    ):
        """Records an execution audit entry synchronously into the database."""
        try:
            cls._create_audit_record(
                agent_name=agent_name,
                action_type=action_type,
                target=target,
                parameters=parameters,
                status=status,
                stdout=stdout,
                stderr=stderr,
                duration_ms=duration_ms,
                task_id=task_id
            )
        except Exception as e:
            logger.error(f"Failed to record execution audit log: {e}")
