"""
O.P.S. 2.0 Desktop Automation Engine Package
Exports all core modules:
1. ApplicationController (Module 1)
2. GUIController (Module 2)
3. FileController (Module 3)
4. CodeWriter (Module 4)
5. VerificationEngine (Module 5)
"""

from automation_system.desktop.application_controller import (
    ApplicationController,
    ensure_desktop_access,
    CANONICAL_APP_ALIASES
)
from automation_system.desktop.gui_controller import GUIController
from automation_system.desktop.file_controller import FileController
from automation_system.desktop.code_writer import CodeWriter
from automation_system.desktop.verification_engine import (
    VerificationEngine,
    STATUS_PENDING,
    STATUS_EXECUTING,
    STATUS_VERIFYING,
    STATUS_COMPLETED,
    STATUS_FAILED,
    STATUS_CANCELLED,
    STATUS_CLARIFICATION
)

__all__ = [
    "ApplicationController",
    "ensure_desktop_access",
    "CANONICAL_APP_ALIASES",
    "GUIController",
    "FileController",
    "CodeWriter",
    "VerificationEngine",
    "STATUS_PENDING",
    "STATUS_EXECUTING",
    "STATUS_VERIFYING",
    "STATUS_COMPLETED",
    "STATUS_FAILED",
    "STATUS_CANCELLED",
    "STATUS_CLARIFICATION",
]
