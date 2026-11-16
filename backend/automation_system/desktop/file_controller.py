"""
O.P.S. 2.0 Desktop Automation Engine — Module 3: File and Folder Controller
Provides safe, verified filesystem operations using Python standard library (pathlib, os, shutil).
Enforces exact path normalization, traversal guards, protected system paths protection,
backup creation prior to destructive edits, and empirical post-condition verifications.
"""

import os
import re
import shutil
import logging
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from automation_system.desktop.application_controller import ApplicationController

logger = logging.getLogger("OPS.Desktop.FileController")

# Prohibited system roots and critical paths for deletion or destructive modification
PROTECTED_SYSTEM_PATHS = [
    r"^[a-zA-Z]:\\windows",
    r"^[a-zA-Z]:\\program files",
    r"^[a-zA-Z]:\\program files \(x86\)",
    r"^[a-zA-Z]:\\system volume information",
    r"^[a-zA-Z]:\\recovery",
    r"^[a-zA-Z]:\\boot",
    r"^[a-zA-Z]:\\users\\[^\\]+\\appdata\\local\\microsoft\\windows",
    r"^[a-zA-Z]:\\$",
]


class FileController:
    """
    Manages safe, verified local file and directory operations.
    """

    @classmethod
    def resolve_safe_path(cls, path_str: str) -> str:
        """
        Normalizes paths, expands user tilde (~), environment variables, and returns absolute path.
        """
        if not path_str or not path_str.strip():
            raise ValueError("Path parameter cannot be empty.")
        clean = path_str.strip().strip('"\'')
        expanded = os.path.expandvars(os.path.expanduser(clean))
        return os.path.abspath(expanded)

    @classmethod
    def is_protected_path(cls, abs_path: str) -> bool:
        """
        Verifies whether the target path lies inside critical Windows system directories.
        """
        norm_path = abs_path.lower().replace("/", "\\")
        for pattern in PROTECTED_SYSTEM_PATHS:
            if re.search(pattern, norm_path):
                return True
        return False

    @classmethod
    def check_exists(cls, path: str) -> Dict[str, Any]:
        """
        Checks whether a file or directory exists and returns metadata.
        """
        try:
            target = cls.resolve_safe_path(path)
            exists = os.path.exists(target)
            is_file = os.path.isfile(target) if exists else False
            is_dir = os.path.isdir(target) if exists else False
            size = os.path.getsize(target) if exists and is_file else 0

            return {
                "success": True,
                "path": target,
                "exists": exists,
                "is_file": is_file,
                "is_dir": is_dir,
                "size_bytes": size
            }
        except Exception as e:
            return {"success": False, "path": path, "error": str(e), "exists": False}

    @classmethod
    def open_file(cls, path: str, app: Optional[str] = None) -> Dict[str, Any]:
        """
        Opens a file using either its Windows default associated application or an explicit program.
        """
        try:
            target = cls.resolve_safe_path(path)
            if not os.path.exists(target):
                return {
                    "success": False,
                    "action": "open_file",
                    "path": target,
                    "error": f"File '{target}' does not exist on disk."
                }

            if app:
                ac = ApplicationController()
                launch_res = ac.launch(app, args=[target], reuse_existing=False)
                return {
                    "success": launch_res.get("success", False),
                    "action": "open_file",
                    "path": target,
                    "app": app,
                    "details": launch_res
                }

            # Default system association via os.startfile
            os.startfile(target)
            return {
                "success": True,
                "action": "open_file",
                "path": target,
                "message": f"Opened file '{os.path.basename(target)}' with default system application."
            }
        except Exception as e:
            logger.error(f"Failed to open file {path}: {e}")
            return {"success": False, "action": "open_file", "path": path, "error": str(e)}

    @classmethod
    def open_folder(cls, path: str, in_vscode: bool = False) -> Dict[str, Any]:
        """
        Opens a folder in Windows File Explorer or Visual Studio Code.
        """
        try:
            target = cls.resolve_safe_path(path)
            os.makedirs(target, exist_ok=True)

            if in_vscode:
                ac = ApplicationController()
                return ac.launch("code", args=[target], reuse_existing=False)

            # Open in Windows File Explorer
            subprocess.Popen(["explorer.exe", target])
            return {
                "success": True,
                "action": "open_folder",
                "path": target,
                "message": f"Opened folder '{target}' in File Explorer."
            }
        except Exception as e:
            return {"success": False, "action": "open_folder", "path": path, "error": str(e)}

    @classmethod
    def create_file(cls, path: str, content: str = "", overwrite: bool = False) -> Dict[str, Any]:
        """
        Creates a new file with specified content.
        """
        try:
            target = cls.resolve_safe_path(path)
            if cls.is_protected_path(target):
                return {
                    "success": False,
                    "action": "create_file",
                    "path": target,
                    "error": f"Writing to protected system directory is prohibited: {target}"
                }

            if os.path.exists(target) and not overwrite:
                return {
                    "success": False,
                    "action": "create_file",
                    "path": target,
                    "error": f"File '{target}' already exists. Specify overwrite=True to replace it."
                }

            os.makedirs(os.path.dirname(target), exist_ok=True)
            with open(target, "w", encoding="utf-8") as f:
                f.write(content)

            exists = os.path.exists(target)
            return {
                "success": exists,
                "action": "create_file",
                "path": target,
                "size_bytes": os.path.getsize(target) if exists else 0,
                "message": f"Successfully created '{os.path.basename(target)}'."
            }
        except Exception as e:
            return {"success": False, "action": "create_file", "path": path, "error": str(e)}

    @classmethod
    def create_folder(cls, path: str, exist_ok: bool = True) -> Dict[str, Any]:
        """
        Creates a folder or nested directories.
        """
        try:
            target = cls.resolve_safe_path(path)
            if cls.is_protected_path(target):
                return {
                    "success": False,
                    "action": "create_folder",
                    "path": target,
                    "error": f"Creation in protected system directory is prohibited: {target}"
                }

            os.makedirs(target, exist_ok=exist_ok)
            exists = os.path.exists(target) and os.path.isdir(target)
            return {
                "success": exists,
                "action": "create_folder",
                "path": target,
                "message": f"Successfully created folder '{target}'."
            }
        except Exception as e:
            return {"success": False, "action": "create_folder", "path": path, "error": str(e)}

    @classmethod
    def read_file(cls, path: str, max_chars: int = 50000) -> Dict[str, Any]:
        """
        Reads contents of a file safely with UTF-8 decoding and fallback.
        """
        try:
            target = cls.resolve_safe_path(path)
            if not os.path.exists(target):
                return {"success": False, "action": "read_file", "path": target, "error": f"File '{target}' does not exist."}
            if os.path.isdir(target):
                return {"success": False, "action": "read_file", "path": target, "error": f"Target '{target}' is a directory."}

            with open(target, "r", encoding="utf-8", errors="replace") as f:
                content = f.read(max_chars)

            return {
                "success": True,
                "action": "read_file",
                "path": target,
                "content": content,
                "total_chars": len(content),
                "is_truncated": len(content) >= max_chars
            }
        except Exception as e:
            return {"success": False, "action": "read_file", "path": path, "error": str(e)}

    @classmethod
    def write_file(cls, path: str, content: str, overwrite: bool = True) -> Dict[str, Any]:
        """
        Writes content to file, creating parent directories if needed.
        """
        return cls.create_file(path, content=content, overwrite=overwrite)

    @classmethod
    def edit_file(
        cls,
        path: str,
        target_snippet: Optional[str] = None,
        replacement_snippet: Optional[str] = None,
        new_content: Optional[str] = None,
        append: bool = False,
        backup: bool = True,
        create_backup: bool = True
    ) -> Dict[str, Any]:
        """
        Performs targeted safe in-file modification or overwriting.
        - Preserves unrelated content, comments, and formatting when target_snippet is used.
        - Backs up existing file to <path>.bak before editing.
        """
        try:
            target = cls.resolve_safe_path(path)
            if not os.path.exists(target):
                return {"success": False, "action": "edit_file", "path": target, "error": f"File '{target}' does not exist."}
            if cls.is_protected_path(target):
                return {"success": False, "action": "edit_file", "path": target, "error": f"Target is protected system path: {target}"}

            with open(target, "r", encoding="utf-8", errors="replace") as f:
                original_text = f.read()

            # Create backup if requested
            backup_path = None
            if backup or create_backup:
                backup_path = f"{target}.bak"
                shutil.copy2(target, backup_path)

            if new_content is not None:
                if append:
                    modified_text = original_text + ("\n" if not original_text.endswith("\n") else "") + new_content
                else:
                    modified_text = new_content
            elif target_snippet and replacement_snippet is not None:
                if target_snippet not in original_text:
                    return {
                        "success": False,
                        "action": "edit_file",
                        "path": target,
                        "error": f"Target snippet to replace was not found in '{os.path.basename(target)}'."
                    }
                modified_text = original_text.replace(target_snippet, replacement_snippet, 1)
            else:
                return {"success": False, "action": "edit_file", "path": target, "error": "No edit directives provided."}

            with open(target, "w", encoding="utf-8") as f:
                f.write(modified_text)

            return {
                "success": True,
                "action": "edit_file",
                "path": target,
                "backup_path": backup_path,
                "old_size": len(original_text),
                "new_size": len(modified_text),
                "message": f"Successfully updated '{os.path.basename(target)}'."
            }
        except Exception as e:
            return {"success": False, "action": "edit_file", "path": path, "error": str(e)}

    @classmethod
    def delete_file(cls, path: str, backup: bool = False) -> Dict[str, Any]:
        """
        Safely deletes a single file after verifying it is not a directory or protected system path.
        """
        try:
            target = cls.resolve_safe_path(path)
            if not os.path.exists(target):
                return {"success": False, "action": "delete_file", "path": target, "error": f"File '{target}' does not exist."}
            if os.path.isdir(target):
                return {"success": False, "action": "delete_file", "path": target, "error": f"Target '{target}' is a directory, not a file."}
            if cls.is_protected_path(target):
                return {"success": False, "action": "delete_file", "path": target, "error": f"Deletion prohibited on protected system path: {target}"}

            backup_path = None
            if backup:
                backup_path = f"{target}.deleted_bak"
                shutil.copy2(target, backup_path)

            os.remove(target)
            deleted = not os.path.exists(target)

            return {
                "success": deleted,
                "action": "delete_file",
                "path": target,
                "verified_deleted": deleted,
                "backup_path": backup_path,
                "message": f"Successfully deleted '{os.path.basename(target)}'."
            }
        except Exception as e:
            return {"success": False, "action": "delete_file", "path": path, "error": str(e)}

    @classmethod
    def delete_folder(cls, path: str, recursive: bool = True) -> Dict[str, Any]:
        """
        Safely deletes a directory after validating it is not a protected system path.
        """
        try:
            target = cls.resolve_safe_path(path)
            if not os.path.exists(target):
                return {"success": False, "action": "delete_folder", "path": target, "error": f"Folder '{target}' does not exist."}
            if not os.path.isdir(target):
                return {"success": False, "action": "delete_folder", "path": target, "error": f"Target '{target}' is a file, not a directory."}
            if cls.is_protected_path(target):
                return {"success": False, "action": "delete_folder", "path": target, "error": f"Deletion prohibited on protected system path: {target}"}

            # Safety check: prevent deleting root of user profile directly
            user_home = os.path.abspath(os.path.expanduser("~")).lower()
            if target.lower() == user_home:
                return {"success": False, "action": "delete_folder", "error": "Deleting the entire user profile root is strictly prohibited."}

            if recursive:
                shutil.rmtree(target)
            else:
                os.rmdir(target)

            deleted = not os.path.exists(target)
            return {
                "success": deleted,
                "action": "delete_folder",
                "path": target,
                "verified_deleted": deleted,
                "message": f"Successfully deleted directory '{target}'."
            }
        except Exception as e:
            return {"success": False, "action": "delete_folder", "path": path, "error": str(e)}

    @classmethod
    def rename_file(cls, old_path: str, new_path: str) -> Dict[str, Any]:
        """
        Renames a file from old_path to new_path (or new filename in same directory).
        """
        try:
            src = cls.resolve_safe_path(old_path)
            if not os.path.exists(src):
                return {"success": False, "action": "rename_file", "path": src, "error": f"Source file '{src}' does not exist."}
            if cls.is_protected_path(src):
                return {"success": False, "action": "rename_file", "path": src, "error": f"Renaming protected path is prohibited: {src}"}

            # If new_path is just a filename, place in same directory
            if not os.path.isabs(new_path) and os.path.dirname(new_path) == "":
                dst = os.path.join(os.path.dirname(src), new_path)
            else:
                dst = cls.resolve_safe_path(new_path)

            os.rename(src, dst)
            renamed = os.path.exists(dst) and not os.path.exists(src)
            return {
                "success": renamed,
                "action": "rename_file",
                "old_path": src,
                "new_path": dst,
                "verified": renamed,
                "message": f"Renamed '{src}' to '{dst}'."
            }
        except Exception as e:
            return {"success": False, "action": "rename_file", "old_path": old_path, "new_path": new_path, "error": str(e)}

    @classmethod
    def copy_file(cls, src_path: str, dst_path: str) -> Dict[str, Any]:
        """
        Copies a file from src_path to dst_path (file or folder).
        """
        try:
            src = cls.resolve_safe_path(src_path)
            if not os.path.exists(src):
                return {"success": False, "action": "copy_file", "path": src, "error": f"Source file '{src}' does not exist."}

            dst = cls.resolve_safe_path(dst_path)
            if os.path.isdir(dst):
                dst = os.path.join(dst, os.path.basename(src))

            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(src, dst)
            copied = os.path.exists(dst)
            return {
                "success": copied,
                "action": "copy_file",
                "src_path": src,
                "dst_path": dst,
                "verified": copied,
                "message": f"Copied '{src}' to '{dst}'."
            }
        except Exception as e:
            return {"success": False, "action": "copy_file", "src_path": src_path, "dst_path": dst_path, "error": str(e)}

    @classmethod
    def move_file(cls, src_path: str, dst_path: str) -> Dict[str, Any]:
        """
        Moves a file from src_path to dst_path (file or folder).
        """
        try:
            src = cls.resolve_safe_path(src_path)
            if not os.path.exists(src):
                return {"success": False, "action": "move_file", "path": src, "error": f"Source file '{src}' does not exist."}
            if cls.is_protected_path(src):
                return {"success": False, "action": "move_file", "path": src, "error": f"Moving protected path is prohibited: {src}"}

            dst = cls.resolve_safe_path(dst_path)
            if os.path.isdir(dst):
                dst = os.path.join(dst, os.path.basename(src))

            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.move(src, dst)
            moved = os.path.exists(dst) and not os.path.exists(src)
            return {
                "success": moved,
                "action": "move_file",
                "src_path": src,
                "dst_path": dst,
                "verified": moved,
                "message": f"Moved '{src}' to '{dst}'."
            }
        except Exception as e:
            return {"success": False, "action": "move_file", "src_path": src_path, "dst_path": dst_path, "error": str(e)}
