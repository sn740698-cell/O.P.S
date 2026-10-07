"""
O.P.S. Deterministic Safety Gate
Evaluates tool calls against strict risk policies (SAFE, ELEVATED, DANGEROUS, FORBIDDEN).
The model can NEVER override the Safety Gate.
"""

import re
import logging
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from ops_core.capabilities.schemas import ToolCallRequest, RiskLevel
from ops_core.core.errors import OPSError, OPSErrorCode
from ops_core.services.permission_manager import OPSPermissionManager

logger = logging.getLogger("ops.safety.gate")


class SafetyDecision(BaseModel):
    approved: bool
    risk_level: RiskLevel
    reason: str


class SafetyGate:
    # 1. FORBIDDEN patterns: Absolutely blocked under all circumstances
    FORBIDDEN_PATTERNS = [
        r"(?i)\bformat\s+[a-z]:",
        r"(?i)\bdel\s+(?:\/[a-z]\s+)?c:\\windows",
        r"(?i)\brm\s+-rf\s+\/(?:$|\s)",
        r"(?i)\bchmod\s+-R\s+777\s+\/",
        r"(?i)\bdiskpart\b",
        r"(?i)\bdrop\s+database\b",
        r"(?i)\bshutdown\s+\/s\s+\/t\s+0\b",
        r"(?i):(){ :|:& };:"  # Fork bomb
    ]

    # 2. DANGEROUS patterns: Require explicit Human-in-the-Loop approval
    DANGEROUS_PATTERNS = [
        r"(?i)\brm\s+-rf\b",
        r"(?i)\bdel\s+\/f\b",
        r"(?i)\brmdir\s+\/s\b",
        r"(?i)\bgit\s+reset\s+--hard\b",
        r"(?i)\bgit\s+clean\s+-fdx\b",
        r"(?i)\bkill\s+-9\b",
        r"(?i)\btaskkill\s+\/f\b"
    ]

    @classmethod
    async def evaluate(cls, request: ToolCallRequest) -> SafetyDecision:
        """Evaluates risk and returns structured SafetyDecision."""
        risk = cls.evaluate_risk(request)
        if risk == RiskLevel.FORBIDDEN:
            return SafetyDecision(approved=False, risk_level=risk, reason="Matches forbidden pattern.")
        elif risk == RiskLevel.DANGEROUS:
            return SafetyDecision(approved=False, risk_level=risk, reason="Requires user confirmation.")
        return SafetyDecision(approved=True, risk_level=risk, reason="Safe execution.")

    @classmethod
    def evaluate_risk(cls, request: ToolCallRequest) -> RiskLevel:
        """
        Determines the true deterministic risk level of a requested tool execution.
        """
        capability = request.capability
        cmd = request.arguments.get("command", "") or ""
        path = request.arguments.get("path", "") or ""

        # Check FORBIDDEN
        for pattern in cls.FORBIDDEN_PATTERNS:
            if re.search(pattern, cmd) or re.search(pattern, path):
                return RiskLevel.FORBIDDEN

        # Specific dangerous capabilities
        if capability in ["filesystem.delete"]:
            return RiskLevel.DANGEROUS

        # Check DANGEROUS patterns in terminal commands
        for pattern in cls.DANGEROUS_PATTERNS:
            if re.search(pattern, cmd):
                return RiskLevel.DANGEROUS

        # Elevated operations (file writes, app launches, test runs)
        if capability in ["filesystem.write", "filesystem.move", "desktop.launch_app", "terminal.execute", "browser.click"]:
            return RiskLevel.ELEVATED

        return RiskLevel.SAFE

    @classmethod
    async def authorize_or_prompt(cls, request: ToolCallRequest) -> bool:
        """
        Authorizes execution. If DANGEROUS or requires confirmation, pauses and prompts the user via HITL.
        Returns True if authorized, raises OPSError if blocked/declined.
        """
        risk = cls.evaluate_risk(request)
        request.risk = risk

        # 1. Block FORBIDDEN immediately
        if risk == RiskLevel.FORBIDDEN:
            logger.error(f"Safety Gate blocked FORBIDDEN operation: {request.capability} -> {request.arguments}")
            raise OPSError(
                code=OPSErrorCode.SAFETY_BLOCK,
                message=f"Forbidden operation blocked by system safety policy: {request.capability}",
                agent=request.requested_by,
                task_id=request.task_id
            )

        # 2. Check if DANGEROUS or requires confirmation
        if risk == RiskLevel.DANGEROUS:
            action_desc = f"Execute [{request.capability}]"
            command_desc = request.arguments.get("command") or request.arguments.get("path") or str(request.arguments)
            
            # Check pre-approval whitelist for active task
            if OPSPermissionManager.is_action_pre_approved(action_desc, command_desc, request.task_id):
                return True

            # Prompt via HITL permission manager
            logger.info(f"Safety Gate requesting user approval for DANGEROUS action: {action_desc}")
            perm_res = await OPSPermissionManager.request_permission(
                agent=request.requested_by,
                action=action_desc,
                command=command_desc,
                reason=f"Action '{request.capability}' requires user authorization.\nTarget: {command_desc}",
                risk_level="DANGEROUS",
                task_id=request.task_id,
                timeout_seconds=45
            )

            if not perm_res.get("approved"):
                raise OPSError(
                    code=OPSErrorCode.PERMISSION_DENIED,
                    message=f"Action declined by user: {request.capability}",
                    agent=request.requested_by,
                    task_id=request.task_id
                )

        return True
