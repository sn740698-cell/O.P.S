"""
O.P.S. 2.0 File System Automation Executor
Technology: Python standard library (os, shutil, pathlib) with strict path validation
Provides verified filesystem operations:
- Safe file and folder creation (including nested project hierarchies)
- Reading, appending, and precise in-file code replacement
- Renaming, moving, and safe deletion
- Comprehensive protection against unauthorized access to Windows system directories
- Empirical post-operation verification
"""

import os
import shutil
import logging
import re
from typing import Dict, Any, List, Optional, Tuple
from automation_system.verification.verifier import AutomationVerifier

logger = logging.getLogger("OPS.FileSystemExecutor")

# Prohibited system roots and critical paths for deletion or destructive modification
PROTECTED_SYSTEM_PATHS = [
    r"^[a-zA-Z]:\\windows",
    r"^[a-zA-Z]:\\program files",
    r"^[a-zA-Z]:\\program files \(x86\)",
    r"^[a-zA-Z]:\\system volume information",
    r"^[a-zA-Z]:\\recovery",
    r"^[a-zA-Z]:\\boot",
    r"^[a-zA-Z]:\\users\\[^\\]+\\appdata\\local\\microsoft\\windows",
    r"^[a-zA-Z]:\\$"
]


class FileSystemExecutor:
    """
    Executes controlled, verified filesystem operations on the local host.
    Enforces strict path safety and validates outcomes before reporting completion.
    """

    @classmethod
    def resolve_safe_path(cls, path_str: str) -> str:
        """
        Expands user tilde (~), environment variables, and normalizes path.
        """
        if not path_str:
            raise ValueError("Path argument cannot be empty.")
        expanded = os.path.expandvars(os.path.expanduser(path_str.strip(" \"'")))
        return os.path.abspath(expanded)

    @classmethod
    def is_protected_path(cls, abs_path: str) -> bool:
        """
        Checks whether target path lies inside a protected Windows system directory.
        """
        norm_path = abs_path.lower().replace("/", "\\")
        for pattern in PROTECTED_SYSTEM_PATHS:
            if re.search(pattern, norm_path):
                return True
        return False

    @classmethod
    def create_file(cls, path: str, content: str = "", overwrite: bool = False) -> Dict[str, Any]:
        """
        Creates a new file with user-specified content and validates creation.
        """
        try:
            target = cls.resolve_safe_path(path)
            if cls.is_protected_path(target):
                return {"success": False, "action": "create_file", "path": target, "error": "Operation prohibited on protected system directory."}

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

            verif = AutomationVerifier.verify_file_exists(target, min_size=0, timeout=3.0)
            return {
                "success": verif.get("verified", False),
                "action": "create_file",
                "path": target,
                "bytes_written": len(content.encode("utf-8")),
                "verification": verif
            }
        except Exception as e:
            logger.error(f"Failed to create file: {e}")
            return {"success": False, "action": "create_file", "path": path, "error": str(e)}

    @classmethod
    def create_folder(cls, path: str, folder_name: Optional[str] = None, exist_ok: bool = True) -> Dict[str, Any]:
        """
        Creates a directory or nested directory structure on the filesystem.
        """
        try:
            base = cls.resolve_safe_path(path)
            target = os.path.join(base, folder_name) if folder_name else base
            if cls.is_protected_path(target):
                return {"success": False, "action": "create_folder", "path": target, "error": "Operation prohibited on protected system directory."}

            os.makedirs(target, exist_ok=exist_ok)
            verif = AutomationVerifier.verify_folder_exists(target, timeout=3.0)
            return {
                "success": verif.get("verified", False),
                "action": "create_folder",
                "path": target,
                "verification": verif
            }
        except Exception as e:
            logger.error(f"Failed to create folder: {e}")
            return {"success": False, "action": "create_folder", "path": path, "error": str(e)}

    @classmethod
    def create_project_structure(cls, base_path: str, structure: Dict[str, Any]) -> Dict[str, Any]:
        """
        Creates complex project directory and file hierarchies.
        Example structure: {"src": {"index.js": "console.log('hi')", "utils": {}}, "README.md": "# Project"}
        """
        try:
            root = cls.resolve_safe_path(base_path)
            if cls.is_protected_path(root):
                return {"success": False, "action": "create_project_structure", "error": "Cannot create project in protected system directory."}

            os.makedirs(root, exist_ok=True)
            created_files = []
            created_dirs = []

            def _build(current_dir: str, node: Any):
                if isinstance(node, dict):
                    for name, val in node.items():
                        sub_target = os.path.join(current_dir, name)
                        if isinstance(val, (dict, list)):
                            os.makedirs(sub_target, exist_ok=True)
                            created_dirs.append(sub_target)
                            _build(sub_target, val)
                        else:
                            with open(sub_target, "w", encoding="utf-8") as f:
                                f.write(str(val or ""))
                            created_files.append(sub_target)
                elif isinstance(node, list):
                    for item in node:
                        sub_target = os.path.join(current_dir, str(item))
                        os.makedirs(sub_target, exist_ok=True)
                        created_dirs.append(sub_target)

            _build(root, structure)
            return {
                "success": True,
                "action": "create_project_structure",
                "base_path": root,
                "directories_created": len(created_dirs),
                "files_created": len(created_files),
                "files": created_files
            }
        except Exception as e:
            return {"success": False, "action": "create_project_structure", "error": str(e)}

    @classmethod
    def read_file(cls, path: str, max_chars: int = 15000) -> Dict[str, Any]:
        """
        Reads contents of target file with character bounds.
        """
        try:
            target = cls.resolve_safe_path(path)
            if not os.path.exists(target):
                return {"success": False, "action": "read_file", "path": target, "error": f"File '{target}' not found."}
            if os.path.isdir(target):
                return {"success": False, "action": "read_file", "path": target, "error": f"Target '{target}' is a directory, not a file."}

            with open(target, "r", encoding="utf-8", errors="replace") as f:
                content = f.read(max_chars)

            total_lines = content.count("\n") + 1
            return {
                "success": True,
                "action": "read_file",
                "path": target,
                "content": content,
                "total_lines": total_lines,
                "is_truncated": len(content) >= max_chars
            }
        except Exception as e:
            return {"success": False, "action": "read_file", "path": path, "error": str(e)}

    @classmethod
    def append_to_file(cls, path: str, content: str) -> Dict[str, Any]:
        """
        Appends text to a file, preserving line breaks.
        """
        try:
            target = cls.resolve_safe_path(path)
            if cls.is_protected_path(target):
                return {"success": False, "action": "append_to_file", "error": "Operation prohibited on protected directory."}

            os.makedirs(os.path.dirname(target), exist_ok=True)
            with open(target, "a", encoding="utf-8") as f:
                if not content.startswith("\n") and os.path.exists(target) and os.path.getsize(target) > 0:
                    f.write("\n")
                f.write(content)

            verif = AutomationVerifier.verify_file_exists(target, min_size=1)
            return {
                "success": verif.get("verified", False),
                "action": "append_to_file",
                "path": target,
                "bytes_appended": len(content.encode("utf-8")),
                "verification": verif
            }
        except Exception as e:
            return {"success": False, "action": "append_to_file", "path": path, "error": str(e)}

    @classmethod
    def replace_in_file(cls, path: str, target_content: str, replacement_content: str) -> Dict[str, Any]:
        """
        Replaces a specific snippet or block within an existing file.
        """
        try:
            target = cls.resolve_safe_path(path)
            if not os.path.exists(target):
                return {"success": False, "action": "replace_in_file", "path": target, "error": f"File '{target}' not found."}

            with open(target, "r", encoding="utf-8", errors="replace") as f:
                old_text = f.read()

            if target_content not in old_text:
                return {
                    "success": False,
                    "action": "replace_in_file",
                    "path": target,
                    "error": f"Target snippet not found in '{target}'."
                }

            new_text = old_text.replace(target_content, replacement_content, 1)
            with open(target, "w", encoding="utf-8") as f:
                f.write(new_text)

            return {
                "success": True,
                "action": "replace_in_file",
                "path": target,
                "replaced": True,
                "new_size": len(new_text.encode("utf-8"))
            }
        except Exception as e:
            return {"success": False, "action": "replace_in_file", "path": path, "error": str(e)}

    @classmethod
    def rename_file(cls, source_path: str, new_name_or_path: str) -> Dict[str, Any]:
        """
        Renames a file or folder.
        """
        try:
            src = cls.resolve_safe_path(source_path)
            if not os.path.exists(src):
                return {"success": False, "action": "rename_file", "path": src, "error": f"Source '{src}' not found."}
            if cls.is_protected_path(src):
                return {"success": False, "action": "rename_file", "path": src, "error": "Prohibited on system directories."}

            if os.path.sep in new_name_or_path or "/" in new_name_or_path:
                dst = cls.resolve_safe_path(new_name_or_path)
            else:
                dst = os.path.join(os.path.dirname(src), new_name_or_path)

            os.rename(src, dst)
            return {
                "success": os.path.exists(dst) and not os.path.exists(src),
                "action": "rename_file",
                "source": src,
                "destination": dst,
                "verification": {"verified": os.path.exists(dst)}
            }
        except Exception as e:
            return {"success": False, "action": "rename_file", "error": str(e)}

    @classmethod
    def move_file(cls, source_path: str, destination_dir_or_path: str) -> Dict[str, Any]:
        """
        Moves a file or folder to a new destination.
        """
        try:
            src = cls.resolve_safe_path(source_path)
            dst = cls.resolve_safe_path(destination_dir_or_path)
            if not os.path.exists(src):
                return {"success": False, "action": "move_file", "path": src, "error": f"Source '{src}' not found."}
            if cls.is_protected_path(src) or cls.is_protected_path(dst):
                return {"success": False, "action": "move_file", "error": "Operation prohibited on system directories."}

            if os.path.isdir(dst):
                dst = os.path.join(dst, os.path.basename(src))

            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.move(src, dst)
            return {
                "success": os.path.exists(dst) and not os.path.exists(src),
                "action": "move_file",
                "source": src,
                "destination": dst,
                "verification": {"verified": os.path.exists(dst)}
            }
        except Exception as e:
            return {"success": False, "action": "move_file", "error": str(e)}

    @classmethod
    def delete_file(cls, path: str, force: bool = False) -> Dict[str, Any]:
        """
        Safely deletes a single file after path validation and verification.
        Requires explicit path, never allows wildcard or directory deletion.
        """
        try:
            target = cls.resolve_safe_path(path)
            if not os.path.exists(target):
                return {"success": False, "action": "delete_file", "path": target, "error": f"File '{target}' does not exist."}
            if os.path.isdir(target):
                return {"success": False, "action": "delete_file", "path": target, "error": f"Target '{target}' is a directory, not a file. Use delete_folder instead."}
            if cls.is_protected_path(target):
                return {"success": False, "action": "delete_file", "path": target, "error": f"Deletion prohibited on protected system path: {target}"}

            os.remove(target)
            deleted = not os.path.exists(target)
            return {
                "success": deleted,
                "action": "delete_file",
                "path": target,
                "verification": {"verified": deleted, "file_removed": deleted}
            }
        except Exception as e:
            return {"success": False, "action": "delete_file", "path": path, "error": str(e)}

    @classmethod
    def delete_folder(cls, path: str, recursive: bool = True) -> Dict[str, Any]:
        """
        Safely deletes a user folder after validating it is not a system directory.
        """
        try:
            target = cls.resolve_safe_path(path)
            if not os.path.exists(target):
                return {"success": False, "action": "delete_folder", "path": target, "error": f"Folder '{target}' does not exist."}
            if not os.path.isdir(target):
                return {"success": False, "action": "delete_folder", "path": target, "error": f"Target '{target}' is a file, not a directory. Use delete_file instead."}
            if cls.is_protected_path(target):
                return {"success": False, "action": "delete_folder", "path": target, "error": f"Deletion prohibited on protected system path: {target}"}

            # Safety check: Prevent deleting user home directory root directly
            user_home = os.path.abspath(os.path.expanduser("~")).lower()
            if target.lower() == user_home:
                return {"success": False, "action": "delete_folder", "error": "Deletion of entire user home directory is strictly prohibited."}

            if recursive:
                shutil.rmtree(target)
            else:
                os.rmdir(target)

            deleted = not os.path.exists(target)
            return {
                "success": deleted,
                "action": "delete_folder",
                "path": target,
                "verification": {"verified": deleted, "folder_removed": deleted}
            }
        except Exception as e:
            return {"success": False, "action": "delete_folder", "path": path, "error": str(e)}

    @classmethod
    def delete_code_region(cls, path: str, target_code: str) -> Dict[str, Any]:
        """
        Deletes a specific code snippet or function within a source file.
        """
        return cls.replace_in_file(path, target_content=target_code, replacement_content="")
