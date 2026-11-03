"""
O.P.S. 2.0 — Global Desktop Cockpit Activation & Overlay System
Provides desktop-wide floating overlay, global system hotkeys, multi-monitor management,
and Human-in-the-Loop (HITL) authorization gates.
"""

from .visibility_controller import CockpitVisibilityController
from .hotkeys import GlobalHotkeyDaemon
from .window import FloatingCockpitWindow

__all__ = [
    "CockpitVisibilityController",
    "GlobalHotkeyDaemon",
    "FloatingCockpitWindow"
]
