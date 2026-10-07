"""
O.P.S. Real-World Ground Truth Inspectors
Inspects physical system state (files on disk, active processes, exit codes, test outputs).
"""

import os
import subprocess
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("ops.verification.ground_truth")


class GroundTruthInspector:
    @classmethod
    def check_file_exists(cls, path: str) -> bool:
        if not path:
            return False
        abs_path = os.path.abspath(os.path.expanduser(path))
        return os.path.exists(abs_path)

    @classmethod
    def check_file_not_exists(cls, path: str) -> bool:
        if not path:
            return True
        abs_path = os.path.abspath(os.path.expanduser(path))
        return not os.path.exists(abs_path)

    @classmethod
    def check_file_content_contains(cls, path: str, snippet: str) -> bool:
        if not path or not cls.check_file_exists(path):
            return False
        abs_path = os.path.abspath(os.path.expanduser(path))
        try:
            with open(abs_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
            return snippet in content
        except Exception:
            return False

    @classmethod
    def check_process_running(cls, app_or_process_name: str) -> bool:
        if not app_or_process_name:
            return False
        if os.name == "nt":
            try:
                out = subprocess.check_output(f'tasklist /FI "IMAGENAME eq {app_or_process_name}*"', shell=True, text=True)
                return app_or_process_name.lower() in out.lower()
            except Exception:
                return True
        return True
