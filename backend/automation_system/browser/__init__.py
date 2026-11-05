"""
O.P.S. 2.0 Browser Automation Subsystem
Playwright-based modular browser automation core library.
Provides session persistence, thread-safe execution, multi-tab management,
search and navigation engines, authentication awareness, page inspection,
recovery management, and specialized website adapters.
"""

from .browser_manager import BrowserManager, BrowserSessionManager, PageProxy
from .tab_manager import TabManager
from .locator_engine import LocatorEngine
from .navigation_engine import NavigationEngine
from .search_engine import SearchEngine
from .interaction_engine import InteractionEngine
from .verification_engine import BrowserVerificationEngine
from .page_inspector import PageInspector
from .auth_manager import AuthenticationManager
from .recovery_manager import RecoveryManager

__all__ = [
    "BrowserManager",
    "BrowserSessionManager",
    "PageProxy",
    "TabManager",
    "LocatorEngine",
    "NavigationEngine",
    "SearchEngine",
    "InteractionEngine",
    "BrowserVerificationEngine",
    "PageInspector",
    "AuthenticationManager",
    "RecoveryManager",
]
