"""
O.P.S. 2.0 Browser Automation Subsystem
Playwright-based modular browser automation library.
Provides session persistence, headed interactive browsing, search and navigation engines,
and specialized adapters for YouTube, Instagram, and Google.
"""

from .browser_manager import BrowserManager, BrowserSessionManager
from .navigation_engine import NavigationEngine
from .search_engine import SearchEngine
from .interaction_engine import InteractionEngine
from .verification_engine import BrowserVerificationEngine

__all__ = [
    "BrowserManager",
    "BrowserSessionManager",
    "NavigationEngine",
    "SearchEngine",
    "InteractionEngine",
    "BrowserVerificationEngine",
]
