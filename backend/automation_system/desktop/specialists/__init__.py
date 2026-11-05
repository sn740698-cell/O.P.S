"""
O.P.S. 2.0 Desktop Automation Specialists Package
Exports:
- DesktopSuperiorAgent
- D1_AppAgent
- D2_WindowAgent
- D3_GUIAgent
- D4_FileAgent
- D5_InputAgent
- D6_CodeAgent
- D7_VerificationAgent
- D8_RecoveryAgent
"""

from .d1_app_agent import D1_AppAgent
from .d2_window_agent import D2_WindowAgent
from .d3_gui_agent import D3_GUIAgent
from .d4_file_agent import D4_FileAgent
from .d5_input_agent import D5_InputAgent
from .d6_code_agent import D6_CodeAgent
from .d7_verification_agent import D7_VerificationAgent
from .d8_recovery_agent import D8_RecoveryAgent
from .desktop_superior_agent import DesktopSuperiorAgent

__all__ = [
    "DesktopSuperiorAgent",
    "D1_AppAgent",
    "D2_WindowAgent",
    "D3_GUIAgent",
    "D4_FileAgent",
    "D5_InputAgent",
    "D6_CodeAgent",
    "D7_VerificationAgent",
    "D8_RecoveryAgent",
]
