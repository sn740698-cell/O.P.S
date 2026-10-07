"""
O.P.S. Safety Package
"""

import re
import logging
from typing import Dict, Any, Tuple, Optional
from django.utils import timezone
from channels.db import database_sync_to_async

from ops_core.safety.safety_gate import SafetyGate, RiskLevel, SafetyDecision
from ops_core.safety.injection_guard import PromptInjectionGuard

logger = logging.getLogger("ops.safety")

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


class OPSSafetyGatekeeper:
    """Legacy compatibility bridge for OPSSafetyGatekeeper."""
    @classmethod
    def validate_action_sync(cls, agent_name: str, action: str, params: Dict[str, Any], task_id: Optional[str] = None):
        return True, "LOW", "Auto-approved."

    @classmethod
    def validate_tool_call(cls, tool_name: str, params: Dict[str, Any]):
        return True, "Auto-approved."


__all__ = [
    "SafetyGate",
    "RiskLevel",
    "SafetyDecision",
    "PromptInjectionGuard",
    "OPSSafetyGatekeeper",
    "DEFAULT_FORBIDDEN_CMD_PATTERNS"
]
