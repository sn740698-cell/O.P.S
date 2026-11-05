"""
O.P.S. 2.0 Browser Automation Specialists Package
Exports:
- BrowserSuperiorAgent
- B1_LifecycleAgent
- B2_TabAgent
- B3_NavigationAgent
- B4_InteractionAgent
- B5_FormAgent
- B6_TransferAgent
- B7_VerificationAgent
- B8_RecoveryAgent
"""

from .b1_lifecycle_agent import B1_LifecycleAgent
from .b2_tab_agent import B2_TabAgent
from .b3_navigation_agent import B3_NavigationAgent
from .b4_interaction_agent import B4_InteractionAgent
from .b5_form_agent import B5_FormAgent
from .b6_transfer_agent import B6_TransferAgent
from .b7_verification_agent import B7_VerificationAgent
from .b8_recovery_agent import B8_RecoveryAgent
from .browser_superior_agent import BrowserSuperiorAgent

__all__ = [
    "BrowserSuperiorAgent",
    "B1_LifecycleAgent",
    "B2_TabAgent",
    "B3_NavigationAgent",
    "B4_InteractionAgent",
    "B5_FormAgent",
    "B6_TransferAgent",
    "B7_VerificationAgent",
    "B8_RecoveryAgent",
]
