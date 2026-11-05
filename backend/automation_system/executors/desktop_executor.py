"""
O.P.S. 2.0 Desktop Automation Executor
Technology: Pywinauto + Win32/UIA Controllers
Delegates all core desktop operations to:
- ApplicationController (Module 1)
- GUIController (Module 2)
- FileController (Module 3)
- CodeWriter (Module 4)
- VerificationEngine (Module 5)
Provides backward compatibility while delivering 100% verified, reliable desktop automation.
"""

import os
import time
import logging
from typing import Dict, Any, List, Optional, Union

from automation_system.desktop import (
    ApplicationController,
    GUIController,
    FileController,
    CodeWriter,
    VerificationEngine
)

logger = logging.getLogger("OPS.DesktopExecutor")


class DesktopExecutor:
    """
    Unified executor connecting LangGraph agents to the 5 Desktop Automation Core modules.
    """

    def __init__(self, default_backend: str = "uia"):
        self.default_backend = default_backend
        self.app_controller = ApplicationController(default_backend=default_backend)
        self.gui_controller = GUIController(default_backend=default_backend)
        self.file_controller = FileController()
        self.code_writer = CodeWriter()
        self.verification_engine = VerificationEngine()

    def launch_app(
        self,
        app_name: str,
        path: Optional[str] = None,
        args: Optional[List[str]] = None,
        reuse_existing: bool = True
    ) -> Dict[str, Any]:
        """
        Launches or brings an application to the front.
        """
        return self.app_controller.launch(
            app_name=app_name,
            path=path,
            args=args,
            reuse_existing=reuse_existing
        )

    def close_window(
        self,
        title_or_app: str,
        force: bool = False
    ) -> Dict[str, Any]:
        """
        Gracefully closes an application window with unsaved changes detection.
        """
        return self.app_controller.close(title_or_app, force=force)

    def connect_window(self, title: str, backend: Optional[str] = None) -> Dict[str, Any]:
        """
        Connects Pywinauto to an existing open desktop window.
        """
        return self.gui_controller.connect_window(title, backend=backend)

    def inspect_controls(self, title: str) -> Dict[str, Any]:
        """
        Inspects accessible UI Automation controls for an application window.
        """
        return self.gui_controller.inspect_controls(title)

    def type_text(
        self,
        title: str,
        text: str,
        control_id: Optional[str] = None,
        replace: bool = False
    ) -> Dict[str, Any]:
        """
        Enters text into an accessible edit or document control.
        """
        locator = {"auto_id": control_id} if control_id else None
        return self.gui_controller.type_text(title, text, control_locator=locator, replace=replace)

    def send_keys(self, title: str, keys: str) -> Dict[str, Any]:
        """
        Sends keyboard shortcuts to the window.
        """
        return self.gui_controller.send_keys(title, keys)

    def click_button(self, title: str, button_name: str) -> Dict[str, Any]:
        """
        Locates and clicks an accessible button or UI element in the target window.
        """
        return self.gui_controller.click_button(title, button_locator=button_name)

    def read_text(self, title: str, control_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Reads visible or edit text from target window.
        """
        locator = {"auto_id": control_id} if control_id else None
        return self.gui_controller.read_control_text(title, control_locator=locator)

    def create_desktop_folder(self, path: str, folder_name: str) -> Dict[str, Any]:
        """
        Creates a directory on the local Windows desktop or specified path and verifies it.
        """
        full_path = os.path.join(FileController.resolve_safe_path(path), folder_name)
        res = self.file_controller.create_folder(full_path)
        verif = self.verification_engine.verify_file_exists(full_path, min_size=0, timeout=2.0)
        res["verification"] = verif
        return res

    def open_file(self, path: str, app: Optional[str] = None) -> Dict[str, Any]:
        """
        Opens a file using system association or specified app.
        """
        return self.file_controller.open_file(path, app=app)

    def open_folder(self, path: str, in_vscode: bool = False) -> Dict[str, Any]:
        """
        Opens a folder in File Explorer or VS Code.
        """
        return self.file_controller.open_folder(path, in_vscode=in_vscode)

    def create_code_file(
        self,
        path: str,
        code: Optional[str] = None,
        prompt: Optional[str] = None,
        language: Optional[str] = None,
        overwrite: bool = True
    ) -> Dict[str, Any]:
        """
        Generates and writes complete code file to disk.
        """
        res = self.code_writer.write_code_file(
            path=path,
            code=code,
            prompt=prompt,
            language=language,
            overwrite=overwrite
        )
        verif = self.verification_engine.verify_file_exists(path, min_size=1, timeout=3.0)
        res["verification"] = verif
        return res

    def edit_code_file(
        self,
        path: str,
        instruction: Optional[str] = None,
        target_snippet: Optional[str] = None,
        replacement_snippet: Optional[str] = None,
        backup: bool = True
    ) -> Dict[str, Any]:
        """
        Edits an existing file, either via exact snippet replacement or LLM refactoring.
        """
        if target_snippet and replacement_snippet is not None:
            return self.file_controller.edit_file(
                path=path,
                target_snippet=target_snippet,
                replacement_snippet=replacement_snippet,
                backup=backup
            )
        elif instruction:
            return self.code_writer.edit_existing_code_file(
                path=path,
                instruction=instruction,
                backup=backup
            )
        else:
            return {"success": False, "action": "edit_code_file", "error": "Must provide either snippet or instruction."}

    def save_file(self, title: str, file_path: str, expected_content: Optional[str] = None) -> Dict[str, Any]:
        """
        Saves document via standard Ctrl+S or file writing.
        """
        expanded = FileController.resolve_safe_path(file_path)
        os.makedirs(os.path.dirname(expanded), exist_ok=True)

        # 1. First trigger save in window via Ctrl+S
        self.gui_controller.send_keys(title, "^s")
        time.sleep(0.5)

        # 2. Check if file was saved directly or write content if provided
        if expected_content and not os.path.exists(expanded):
            self.file_controller.write_file(expanded, content=expected_content)

        verif = self.verification_engine.verify_file_exists(expanded, min_size=0, timeout=3.0)
        content_verif = True
        if expected_content:
            c_verif = self.verification_engine.verify_file_content(expanded, expected_content)
            content_verif = c_verif.get("verified", False)

        return {
            "success": verif.get("verified", False) and content_verif,
            "action": "save_file",
            "file_path": expanded,
            "file_exists": verif.get("verified", False),
            "content_verified": content_verif,
            "verification": verif
        }

    def delete_file(self, path: str, backup: bool = False) -> Dict[str, Any]:
        """
        Safely deletes a single file.
        """
        return self.file_controller.delete_file(path, backup=backup)

    def delete_folder(self, path: str, recursive: bool = True) -> Dict[str, Any]:
        """
        Safely deletes a directory.
        """
        return self.file_controller.delete_folder(path, recursive=recursive)

    def vscode_open_project(self, project_path: str) -> Dict[str, Any]:
        """
        Opens a folder or repository in Visual Studio Code.
        """
        return self.open_folder(project_path, in_vscode=True)

    def vscode_create_code_file(self, project_dir: str, filename: str, code: str) -> Dict[str, Any]:
        """
        Creates source code file and opens it in VS Code.
        """
        full_path = os.path.join(FileController.resolve_safe_path(project_dir), filename)
        file_res = self.file_controller.create_file(full_path, content=code, overwrite=True)
        if file_res.get("success"):
            self.app_controller.launch("code", args=[full_path], reuse_existing=False)
        return file_res
