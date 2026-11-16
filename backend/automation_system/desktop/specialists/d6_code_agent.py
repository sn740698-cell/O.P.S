"""
O.P.S. 2.0 Desktop Automation Specialist — Agent D6: Code Generation & File Writer Agent
Responsibilities:
- Synthesize syntactically valid code files using local Qwen3 1.7B model
- Validate AST / syntax parsing before touching disk
- Apply atomic file writes with .bak rollbacks
- Edit existing code bases with targeted diffs or rewrites
- Type generated code directly into active editor windows
"""

import logging
from typing import Dict, Any, Optional
from automation_system.desktop.code_writer import CodeWriter

logger = logging.getLogger("OPS.Desktop.D6_CodeAgent")


class D6_CodeAgent:
    """Specialist Agent D6: Synthesizes, validates, writes, and edits code files."""

    def __init__(self):
        self.agent_id = "agent_d6_code"
        self.agent_name = "Code Generation & File Writer Agent"
        self.writer = CodeWriter()

    def generate_and_write(
        self,
        target_path: str,
        prompt: str,
        language: Optional[str] = None,
        overwrite: bool = True
    ) -> Dict[str, Any]:
        """Synthesizes code and writes to disk with AST verification."""
        try:
            res = self.writer.write_code_file(
                path=target_path,
                prompt=prompt,
                language=language,
                overwrite=overwrite
            )
            res["agent_id"] = self.agent_id
            if "ast_valid" not in res:
                res["ast_valid"] = res.get("syntax_valid", False)
            return res
        except Exception as e:
            logger.error(f"D6_CodeAgent generation failed: {e}")
            return {"success": False, "agent_id": self.agent_id, "action": "generate_and_write", "error": str(e)}

    def edit_code(
        self,
        target_path: str,
        instructions: str,
        language: Optional[str] = None
    ) -> Dict[str, Any]:
        """Applies modifications to existing code file."""
        try:
            res = self.writer.edit_existing_code_file(
                path=target_path,
                instructions=instructions,
                language=language
            )
            res["agent_id"] = self.agent_id
            return res
        except Exception as e:
            return {"success": False, "agent_id": self.agent_id, "action": "edit_code", "error": str(e)}

    def type_into_editor(self, title: str, code: str) -> Dict[str, Any]:
        """Types code directly into an active editor window."""
        try:
            res = self.writer.type_into_active_editor(title, code)
            res["agent_id"] = self.agent_id
            return res
        except Exception as e:
            return {"success": False, "agent_id": self.agent_id, "action": "type_into_editor", "error": str(e)}
