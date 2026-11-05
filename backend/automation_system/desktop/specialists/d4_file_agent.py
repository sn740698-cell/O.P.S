"""
O.P.S. 2.0 Desktop Automation Specialist — Agent D4: File and Folder Agent
Responsibilities:
- Create, read, edit, and safely delete files and folders
- Enforce strict system path protection guards against accidental OS corruption
- Manage automated file backups (.bak) prior to destructive operations
- Open files and folders in native explorer or VS Code
"""

import logging
from typing import Dict, Any, Optional
from automation_system.desktop.file_controller import FileController

logger = logging.getLogger("OPS.Desktop.D4_FileAgent")


class D4_FileAgent:
    """Specialist Agent D4: Manages disk file operations, workspace paths, and backups."""

    def __init__(self):
        self.agent_id = "agent_d4_file"
        self.agent_name = "File and Folder Agent"
        self.controller = FileController()

    def check_exists(self, path: str) -> Dict[str, Any]:
        """Checks if file or folder exists."""
        res = self.controller.check_exists(path)
        res["agent_id"] = self.agent_id
        return res

    def open_file(self, path: str, app: Optional[str] = None) -> Dict[str, Any]:
        """Opens file in system default application or specific app."""
        res = self.controller.open_file(path, app=app)
        res["agent_id"] = self.agent_id
        return res

    def open_folder(self, path: str, in_vscode: bool = False) -> Dict[str, Any]:
        """Opens folder in Windows Explorer or VS Code."""
        res = self.controller.open_folder(path, in_vscode=in_vscode)
        res["agent_id"] = self.agent_id
        return res

    def create_file(self, path: str, content: str = "", overwrite: bool = False) -> Dict[str, Any]:
        """Creates a file with optional content."""
        res = self.controller.create_file(path, content=content, overwrite=overwrite)
        res["agent_id"] = self.agent_id
        return res

    def read_file(self, path: str, max_chars: int = 50000) -> Dict[str, Any]:
        """Reads content from text file."""
        res = self.controller.read_file(path, max_chars=max_chars)
        res["agent_id"] = self.agent_id
        return res

    def edit_file(self, path: str, new_content: Optional[str] = None, append: bool = False, create_backup: bool = True) -> Dict[str, Any]:
        """Modifies existing file with safety backup."""
        res = self.controller.edit_file(path, new_content=new_content, append=append, create_backup=create_backup)
        res["agent_id"] = self.agent_id
        return res

    def delete_file(self, path: str, backup: bool = False) -> Dict[str, Any]:
        """Safely removes file after path protection check."""
        res = self.controller.delete_file(path, backup=backup)
        res["agent_id"] = self.agent_id
        return res

    def create_folder(self, path: str, exist_ok: bool = True) -> Dict[str, Any]:
        """Creates directory and any missing parent directories."""
        res = self.controller.create_folder(path, exist_ok=exist_ok)
        res["agent_id"] = self.agent_id
        return res

    def delete_folder(self, path: str, recursive: bool = True) -> Dict[str, Any]:
        """Safely deletes folder after path protection check."""
        res = self.controller.delete_folder(path, recursive=recursive)
        res["agent_id"] = self.agent_id
        return res
