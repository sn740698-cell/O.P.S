"""
O.P.S. 2.0 — Global Hotkey Daemon
Registers and manages system-wide keyboard shortcuts at the Windows OS level.
Works above all applications (Chrome, VS Code, Word, File Explorer, Terminal, Games).

Exact Required Behavior:
- [ Ctrl + Alt ] -> OPEN / SHOW the O.P.S. Pop-up Cockpit
  * When closed: Opens cockpit, brings to foreground, focuses input.
  * When already open: Does nothing (no duplicate instances, does not close).
- [ Ctrl + Alt + Space ] -> CLOSE / HIDE the O.P.S. Pop-up Cockpit
  * When open: Hides/closes the cockpit window, preserves backend state.
  * When already closed: Does nothing.
"""

import sys
import time
import threading
import logging
import ctypes
from typing import Callable, Optional

logger = logging.getLogger("OPSDesktopOverlay.Hotkeys")

# Windows Virtual Key Codes
VK_CONTROL = 0x11
VK_MENU = 0x12       # Alt key
VK_SPACE = 0x20

ERROR_ALREADY_EXISTS = 183


class SingleInstanceLock:
    """
    Enforces a single running instance of the O.P.S. desktop overlay daemon
    using a Windows Named Mutex.
    """
    def __init__(self, mutex_name: str = "Local\\OPS_2_0_Desktop_Cockpit_Mutex"):
        self.mutex_name = mutex_name
        self.mutex_handle = None
        self.is_primary = False

    def acquire(self) -> bool:
        if sys.platform != "win32":
            self.is_primary = True
            return True

        kernel32 = ctypes.windll.kernel32
        self.mutex_handle = kernel32.CreateMutexW(None, True, self.mutex_name)
        last_error = kernel32.GetLastError()

        if last_error == ERROR_ALREADY_EXISTS:
            logger.warning(f"Another instance of O.P.S. Desktop Overlay is already active (Mutex: {self.mutex_name}).")
            if self.mutex_handle:
                kernel32.CloseHandle(self.mutex_handle)
                self.mutex_handle = None
            self.is_primary = False
            return False

        self.is_primary = True
        logger.info(f"Acquired single-instance mutex: {self.mutex_name}")
        return True

    def release(self):
        if self.mutex_handle and sys.platform == "win32":
            ctypes.windll.kernel32.CloseHandle(self.mutex_handle)
            self.mutex_handle = None
            self.is_primary = False


class GlobalHotkeyDaemon:
    """
    System-wide global hotkey listener.
    Exact specification:
      - [ Ctrl + Alt ] -> Open / Show the O.P.S. Pop-up Cockpit
      - [ Ctrl + Alt + Space ] -> Close / Hide the O.P.S. Pop-up Cockpit
    """
    def __init__(
        self,
        on_open_cockpit: Optional[Callable[[], None]] = None,
        on_close_cockpit: Optional[Callable[[], None]] = None,
        is_visible_fn: Optional[Callable[[], bool]] = None,
        on_toggle_cockpit: Optional[Callable[[], None]] = None,
        on_quick_action: Optional[Callable[[], None]] = None
    ):
        self.on_open_cockpit = on_open_cockpit
        self.on_close_cockpit = on_close_cockpit
        self.is_visible_fn = is_visible_fn or (lambda: False)
        self.on_toggle_cockpit = on_toggle_cockpit
        self.on_quick_action = on_quick_action

        self._running = False
        self._thread: Optional[threading.Thread] = None

        # Lock to prevent duplicate instances
        self.instance_lock = SingleInstanceLock()

        # Controlled disambiguation state machine
        self._ctrl_alt_pressed_time: Optional[float] = None
        self._opened_this_press = False
        self._closed_this_press = False

    def start(self) -> bool:
        """Starts the global hotkey polling thread."""
        if self._running:
            return True

        if not self.instance_lock.acquire():
            logger.error("Cannot start GlobalHotkeyDaemon: Another instance is already running.")
            return False

        self._running = True
        self._thread = threading.Thread(target=self._hotkey_listener_loop, name="OPS-HotkeyDaemon", daemon=True)
        self._thread.start()
        logger.info("Global Hotkey Daemon online: [Ctrl+Alt] to Open Cockpit | [Ctrl+Alt+Space] to Close Cockpit.")
        return True

    def stop(self):
        """Stops the global hotkey polling thread and releases mutex."""
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)
        self.instance_lock.release()
        logger.info("Global Hotkey Daemon halted.")

    def _hotkey_listener_loop(self):
        """
        High-performance Win32 key state polling loop with prefix disambiguation.
        Distinguishes:
        - Ctrl + Alt without Space -> Open Cockpit (if closed)
        - Ctrl + Alt with Space -> Close Cockpit (if open)
        """
        if sys.platform != "win32":
            logger.warning("Global Hotkey Daemon is only supported on Windows.")
            return

        user32 = ctypes.windll.user32

        while self._running:
            try:
                # Bit 15 indicates if key is currently held down
                ctrl_down = bool(user32.GetAsyncKeyState(VK_CONTROL) & 0x8000)
                alt_down = bool(user32.GetAsyncKeyState(VK_MENU) & 0x8000)
                space_down = bool(user32.GetAsyncKeyState(VK_SPACE) & 0x8000)
                now = time.time()

                if ctrl_down and alt_down:
                    if space_down:
                        # Full combination [Ctrl + Alt + Space]
                        # Action: Close Cockpit if currently OPEN
                        if not self._closed_this_press:
                            if self.is_visible_fn():
                                logger.info(">> Global Hotkey [Ctrl + Alt + Space] triggered -> Closing Cockpit")
                                if self.on_close_cockpit:
                                    self.on_close_cockpit()
                                elif self.on_toggle_cockpit:
                                    self.on_toggle_cockpit()
                                self._closed_this_press = True
                            else:
                                # When already closed: do nothing
                                pass
                    else:
                        # [Ctrl + Alt] alone WITHOUT Space
                        if self._ctrl_alt_pressed_time is None:
                            self._ctrl_alt_pressed_time = now

                        # Controlled disambiguation window: 120ms to verify Space is not pressed
                        if (now - self._ctrl_alt_pressed_time >= 0.12) and not self._opened_this_press and not self._closed_this_press:
                            if not self.is_visible_fn():
                                logger.info(">> Global Hotkey [Ctrl + Alt] triggered -> Opening Cockpit")
                                if self.on_open_cockpit:
                                    self.on_open_cockpit()
                                elif self.on_toggle_cockpit:
                                    self.on_toggle_cockpit()
                                self._opened_this_press = True
                            else:
                                # When already open: do nothing (do not close, do not duplicate)
                                pass
                else:
                    # Modifier keys released: reset state for next combo
                    self._ctrl_alt_pressed_time = None
                    self._opened_this_press = False
                    self._closed_this_press = False

                # 15ms sleep: ~66Hz polling rate (minimal CPU overhead, instant feel)
                time.sleep(0.015)

            except Exception as e:
                logger.error(f"Error in hotkey loop: {e}", exc_info=True)
                time.sleep(0.1)
