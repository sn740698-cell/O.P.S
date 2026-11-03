"""
O.P.S. 2.0 — Cockpit Visibility Controller
Central visibility, multi-monitor focus, and lifecycle manager for the desktop overlay.
Marshals hotkey triggers and background Human-in-the-Loop (HITL) approvals to the Qt main thread.
"""

import sys
import time
import json
import logging
import threading
import urllib.request
from typing import Optional, Dict, Any

from PySide6.QtCore import QObject, Signal, Slot
from PySide6.QtWidgets import QApplication

if sys.platform == "win32":
    import win32gui
    import win32con

from .window import FloatingCockpitWindow
from .hotkeys import GlobalHotkeyDaemon

logger = logging.getLogger("OPSDesktopOverlay.VisibilityController")


def force_set_foreground_window(target_hwnd: int):
    """
    Bypasses Windows lock on SetForegroundWindow using AttachThreadInput and AllowSetForegroundWindow.
    Guarantees keyboard focus is given to the overlay across Chrome, VS Code, Word, Terminal, and Games.
    """
    if sys.platform != "win32" or not target_hwnd:
        return

    import ctypes
    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32

    try:
        user32.AllowSetForegroundWindow(-1)

        fore_hwnd = user32.GetForegroundWindow()
        fore_tid = user32.GetWindowThreadProcessId(fore_hwnd, None)
        cur_tid = kernel32.GetCurrentThreadId()

        if fore_tid and fore_tid != cur_tid:
            user32.AttachThreadInput(cur_tid, fore_tid, True)
            user32.BringWindowToTop(target_hwnd)
            user32.SetForegroundWindow(target_hwnd)
            user32.AttachThreadInput(cur_tid, fore_tid, False)
        else:
            user32.BringWindowToTop(target_hwnd)
            user32.SetForegroundWindow(target_hwnd)
    except Exception as err:
        logger.debug(f"force_set_foreground_window notice: {err}")


class CockpitVisibilityController(QObject):
    """
    Central Controller for desktop overlay visibility, global shortcuts,
    active window tracking, and real-time HITL authorization alerts.
    """
    # Qt Signals to safely marshal background thread calls to the Qt main GUI thread
    signal_show = Signal()
    signal_hide = Signal()
    signal_toggle = Signal()
    signal_quick_action = Signal()
    signal_hitl_alert = Signal(dict)

    def __init__(
        self,
        window: FloatingCockpitWindow,
        backend_url: str = "http://127.0.0.1:8000",
        parent: Optional[QObject] = None
    ):
        super().__init__(parent)
        self.window = window
        self.backend_url = backend_url.rstrip("/")

        self.is_visible = False
        self.prev_active_hwnd: Optional[int] = None
        self._running = False

        # HITL Tracking
        self._last_surfaced_approval_id: Optional[str] = None
        self._hitl_thread: Optional[threading.Thread] = None

        # Connect Qt Signals to GUI Slots
        self.signal_show.connect(self._do_show)
        self.signal_hide.connect(self._do_hide)
        self.signal_toggle.connect(self._do_toggle)
        self.signal_quick_action.connect(self._do_quick_action)
        self.signal_hitl_alert.connect(self._do_hitl_alert)

        # Initialize Global Hotkey Daemon with exact specification:
        # [Ctrl + Alt] -> Opens Cockpit (when closed)
        # [Ctrl + Alt + Space] -> Closes Cockpit (when open)
        self.hotkey_daemon = GlobalHotkeyDaemon(
            on_open_cockpit=self.request_show,
            on_close_cockpit=self.request_hide,
            is_visible_fn=lambda: self.is_visible
        )

    def start(self) -> bool:
        """Starts the visibility controller, hotkey daemon, and HITL listener."""
        self._running = True

        # 1. Start Global Hotkey Daemon
        if not self.hotkey_daemon.start():
            logger.error("Failed to start Global Hotkey Daemon.")
            return False

        # 2. Start Background HITL Approval Monitor
        self._hitl_thread = threading.Thread(
            target=self._hitl_monitor_loop,
            name="OPS-HitlMonitor",
            daemon=True
        )
        self._hitl_thread.start()

        logger.info("Cockpit Visibility Controller initialized and monitoring desktop.")
        return True

    def stop(self):
        """Stops the visibility controller and hotkey daemon cleanly."""
        self._running = False
        self.hotkey_daemon.stop()
        if self._hitl_thread and self._hitl_thread.is_alive():
            self._hitl_thread.join(timeout=1.0)
        logger.info("Cockpit Visibility Controller halted.")

    # -------------------------------------------------------------------------
    # Thread-Safe Request Methods (called by hotkeys or background threads)
    # -------------------------------------------------------------------------
    def request_show(self):
        self.signal_show.emit()

    def request_hide(self):
        self.signal_hide.emit()

    def request_toggle(self):
        self.signal_toggle.emit()

    def request_quick_action(self):
        self.signal_quick_action.emit()

    # -------------------------------------------------------------------------
    # Qt GUI Slots (Execute on Qt Main Thread)
    # -------------------------------------------------------------------------
    @Slot()
    def _do_show(self):
        """Activates and surfaces the Pop-up Cockpit above all desktop applications."""
        if self.is_visible:
            return

        # 1. Record the previously active application window to restore focus later
        if sys.platform == "win32":
            try:
                self.prev_active_hwnd = win32gui.GetForegroundWindow()
                title = win32gui.GetWindowText(self.prev_active_hwnd)
                logger.info(f"Captured previous active window: [{self.prev_active_hwnd}] '{title}'")
            except Exception as e:
                logger.warning(f"Failed to capture foreground window: {e}")

        # 2. Reposition on active monitor (where cursor resides)
        self.window.reposition_on_active_screen()

        # 3. Show and activate window
        self.window.show()
        self.window.raise_()
        self.window.activateWindow()

        if sys.platform == "win32":
            try:
                hwnd = int(self.window.winId())
                force_set_foreground_window(hwnd)
                self.window.enforce_win32_topmost()
            except Exception as e:
                logger.warning(f"Could not set foreground window: {e}")

        # 4. Play audio feedback
        self.window.play_sound_appear()
        self.is_visible = True
        logger.info("O.P.S. Pop-up Cockpit is now ACTIVE on desktop.")

    @Slot()
    def _do_hide(self):
        """Hides the Pop-up Cockpit and restores keyboard focus to previous app."""
        if not self.is_visible:
            return

        # 1. Hide overlay window
        self.window.hide()
        self.window.play_sound_disappear()
        self.is_visible = False

        # 2. Restore keyboard focus to previous application window
        if sys.platform == "win32" and self.prev_active_hwnd:
            try:
                if win32gui.IsWindow(self.prev_active_hwnd):
                    force_set_foreground_window(self.prev_active_hwnd)
                    logger.info(f"Restored keyboard focus to window: {self.prev_active_hwnd}")
            except Exception as e:
                logger.warning(f"Could not restore focus to window {self.prev_active_hwnd}: {e}")

        logger.info("O.P.S. Pop-up Cockpit is now HIDDEN. Backend state preserved.")

    @Slot()
    def _do_toggle(self):
        """Toggles the visibility state."""
        if self.is_visible:
            self._do_hide()
        else:
            self._do_show()

    @Slot()
    def _do_quick_action(self):
        """Surfaces the cockpit and triggers quick command / voice focus."""
        if not self.is_visible:
            self._do_show()
        self.window.trigger_quick_action_in_frontend()
        logger.info("Triggered Quick Action inside Cockpit.")

    @Slot(dict)
    def _do_hitl_alert(self, approval_data: dict):
        """
        When LangGraph requests Human-in-the-Loop approval:
        1. Automatically surfaces the Cockpit into view.
        2. Injects the pending approval event into the React frontend.
        """
        logger.info(f"🚨 HITL Gate Alert received: {approval_data.get('approval_id')}")
        if not self.is_visible:
            self._do_show()
        self.window.trigger_hitl_in_frontend(approval_data)

    # -------------------------------------------------------------------------
    # Background HITL Polling Thread
    # -------------------------------------------------------------------------
    def _hitl_monitor_loop(self):
        """
        Monitors the Django backend for PENDING Human-in-the-Loop approval gates.
        When LangGraph creates a pending approval, surfaces the Cockpit immediately.
        """
        poll_url = f"{self.backend_url}/api/chat/approvals/pending/"

        while self._running:
            try:
                req = urllib.request.Request(
                    poll_url,
                    headers={"Accept": "application/json"}
                )
                with urllib.request.urlopen(req, timeout=3.0) as resp:
                    if resp.status == 200:
                        data = json.loads(resp.read().decode("utf-8"))
                        approvals = data.get("approvals", [])

                        if approvals:
                            top = approvals[0]
                            appr_id = top.get("approval_id")

                            # If a new approval is pending that has not been surfaced yet
                            if appr_id and appr_id != self._last_surfaced_approval_id:
                                self._last_surfaced_approval_id = appr_id
                                self.signal_hitl_alert.emit(top)
                        else:
                            # Reset last surfaced ID once resolved
                            self._last_surfaced_approval_id = None

            except Exception:
                # Backend may be starting or offline, retry smoothly
                pass

            time.sleep(1.2)
