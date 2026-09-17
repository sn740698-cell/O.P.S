"""
O.P.S. Execution Safety & Validation Gatekeeper
Ensures AI models NEVER execute raw system commands or automation actions directly.
All tool calls proposed by Ollama models MUST pass safety verification.
"""

import re
import logging
from typing import Dict, Any, Tuple

logger = logging.getLogger("ops.safety")

ALLOWED_AUTOMATION_ACTIONS = [
    "web_scrape",
    "dom_click",
    "dom_type",
    "gui_click",
    "gui_type",
    "take_screenshot",
    "run_terminal_cmd"
]

FORBIDDEN_CMD_PATTERNS = [
    r"rm\s+-rf",
    r"format\s+[a-zA-Z]:",
    r"del\s+/f\s+/s\s+/q",
    r"drop\s+database",
    r"shutdown",
    r"reg\s+delete"
]

class OPSSafetyGatekeeper:

    @staticmethod
    def validate_tool_call(tool_name: str, params: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Validates whether a tool call is safe to execute.
        """
        if tool_name not in ALLOWED_AUTOMATION_ACTIONS:
            return False, f"Tool '{tool_name}' is not in the whitelist of approved actions."

        if tool_name == "run_terminal_cmd":
            cmd = params.get("command", "")
            for pattern in FORBIDDEN_CMD_PATTERNS:
                if re.search(pattern, cmd, re.IGNORECASE):
                    return False, f"Command blocked by safety filter: matches pattern '{pattern}'"

        if tool_name in ["web_scrape", "dom_click", "dom_type"]:
            url = params.get("url", "")
            if url and not (url.startswith("http://") or url.startswith("https://") or url.startswith("file://")):
                return False, f"Invalid or unsafe URL protocol: {url}"

        return True, "Tool call validated successfully."
