"""
O.P.S. 2.0 — Floating Desktop Cockpit Window
Native PySide6 QtWebEngine container hosting the O.P.S. 2.0 Pop-up Cockpit.
Renders above all desktop applications with hardware-accelerated Chromium,
translucent styling, native Windows dragging, dynamic resizing, and geometry persistence.
"""

import os
import sys
import json
import logging
import winsound
from typing import Optional

from PySide6.QtCore import Qt, QUrl, QPoint, QRect
from PySide6.QtGui import QColor, QScreen, QGuiApplication, QCursor
from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import QWebEngineSettings, QWebEnginePage

if sys.platform == "win32":
    import win32gui
    import win32con

logger = logging.getLogger("OPSDesktopOverlay.Window")


class CockpitWebEnginePage(QWebEnginePage):
    """
    Custom WebEnginePage that intercepts 'ops://' bridge actions from React:
    - ops://drag -> Native Windows window dragging
    - ops://resize/{edge} -> Native Windows edge/corner resizing
    - ops://close -> Hide cockpit
    """
    def __init__(self, window: 'FloatingCockpitWindow', parent=None):
        super().__init__(parent)
        self.window = window

    def acceptNavigationRequest(self, url: QUrl, nav_type, is_main_frame) -> bool:
        if url.scheme() == "ops":
            action = url.host().lower()
            param = url.path().lstrip("/").lower()
            if action == "drag":
                self.window.start_native_drag()
            elif action == "resize":
                self.window.start_native_resize(param)
            elif action == "close":
                self.window.hide()
            return False
        return super().acceptNavigationRequest(url, nav_type, is_main_frame)

    def javaScriptConsoleMessage(self, level, message, line_number, source_id):
        logger.info(f"[JS {source_id}:{line_number}] {message}")


class FloatingCockpitWindow(QMainWindow):
    """
    Native floating desktop overlay window for the O.P.S. 2.0 Pop-up Cockpit.
    Supports smooth native dragging, dynamic multi-directional resizing,
    and persistent window geometry.
    """
    def __init__(self, frontend_url: str = "http://localhost:3000/?mode=cockpit", parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.frontend_url = frontend_url

        # Audio paths
        root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.sound_appear = os.path.join(root_dir, "assets", "sounds", "cockpit_appear.wav")
        self.sound_disappear = os.path.join(root_dir, "assets", "sounds", "cockpit_disappear.wav")
        self.geometry_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cockpit_geometry.json")

        # Debounced geometry save timer to prevent disk I/O lag during continuous resizing
        from PySide6.QtCore import QTimer
        self._save_timer = QTimer(self)
        self._save_timer.setSingleShot(True)
        self._save_timer.setInterval(250)
        self._save_timer.timeout.connect(self._do_save_geometry)

        self._init_window_flags()
        self._init_web_engine()

    def _init_window_flags(self):
        """Sets up frameless, transparent, always-on-top window attributes with sizing bounds."""
        self.setWindowTitle("O.P.S. Pop-up Cockpit")
        self.setObjectName("OPSFloatingCockpit")

        # Set window flags for always-on-top floating HUD
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )

        # Enforce minimum dimensions matching Section 3.2: 440px x 580px
        self.setMinimumSize(440, 580)

        # Translucent background for cyber aesthetic
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setStyleSheet("""
            QMainWindow#OPSFloatingCockpit {
                background-color: transparent;
            }
        """)

    def _init_web_engine(self):
        """Initializes the embedded Chromium web engine with custom bridge page."""
        self.central_widget = QWidget(self)
        self.central_widget.setStyleSheet("background: transparent;")
        self.layout = QVBoxLayout(self.central_widget)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        self.web_view = QWebEngineView(self)
        self.web_view.setStyleSheet("background: transparent;")

        # Set custom page to handle native dragging & resizing bridge calls
        self.custom_page = CockpitWebEnginePage(self, self.web_view)
        self.custom_page.setBackgroundColor(QColor(0, 0, 0, 0))
        self.web_view.setPage(self.custom_page)

        # Connect title-based IPC bridge (instantaneous, unblocked by Chromium CSP)
        self.web_view.titleChanged.connect(self._handle_title_action)

        # Enable modern web capabilities
        settings = self.web_view.settings()
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessFileUrls, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.ScrollAnimatorEnabled, True)

        # Allow JavaScript window.close() to hide the overlay
        self.custom_page.windowCloseRequested.connect(self.hide)

        self.web_view.load(QUrl(self.frontend_url))
        self.layout.addWidget(self.web_view)
        self.setCentralWidget(self.central_widget)

    def _enable_win32_resize_frame(self):
        """Ensures the frameless window has WS_THICKFRAME so Windows DWM permits native resizing."""
        if sys.platform != "win32":
            return
        try:
            hwnd = int(self.winId())
            style = win32gui.GetWindowLong(hwnd, win32con.GWL_STYLE)
            if not (style & win32con.WS_THICKFRAME):
                win32gui.SetWindowLong(hwnd, win32con.GWL_STYLE, style | win32con.WS_THICKFRAME)
                win32gui.SetWindowPos(
                    hwnd, 0, 0, 0, 0, 0,
                    win32con.SWP_NOMOVE | win32con.SWP_NOSIZE |
                    win32con.SWP_NOZORDER | win32con.SWP_FRAMECHANGED
                )
        except Exception as e:
            logger.debug(f"_enable_win32_resize_frame notice: {e}")

    def showEvent(self, event):
        super().showEvent(event)
        self._enable_win32_resize_frame()

    def _handle_title_action(self, title: str):
        """Fast title-based IPC bridge triggered from React."""
        if not title or not title.startswith("ops://"):
            return
        try:
            raw = title.replace("ops://", "")
            parts = raw.split("/")
            action = parts[0].lower()
            if action == "drag":
                self.start_native_drag()
            elif action == "move_by" and len(parts) >= 3:
                dx, dy = int(parts[1]), int(parts[2])
                self.dynamic_move_by(dx, dy)
            elif action == "resize" and len(parts) > 1:
                self.start_native_resize(parts[1].lower())
            elif action == "resize_to" and len(parts) >= 3:
                w, h = int(parts[1]), int(parts[2])
                self.dynamic_resize_to(w, h)
            elif action == "set_geometry" and len(parts) >= 5:
                x, y, w, h = int(parts[1]), int(parts[2]), int(parts[3]), int(parts[4])
                self.dynamic_set_geometry(x, y, w, h)
            elif action == "close":
                self.hide()
        except Exception as e:
            logger.debug(f"_handle_title_action notice: {e}")

    def start_native_drag(self):
        """
        Enters native window moving loop via Qt QWindow.startSystemMove()
        and fallback Win32 WM_NCLBUTTONDOWN message.
        """
        wh = self.windowHandle()
        if wh and hasattr(wh, "startSystemMove"):
            try:
                if wh.startSystemMove():
                    return
            except Exception:
                pass

        if sys.platform == "win32":
            try:
                hwnd = int(self.winId())
                win32gui.ReleaseCapture()
                pos = win32gui.GetCursorPos()
                lparam = (pos[1] << 16) | (pos[0] & 0xFFFF)
                win32gui.SendMessage(hwnd, win32con.WM_NCLBUTTONDOWN, win32con.HTCAPTION, lparam)
            except Exception as e:
                logger.debug(f"start_native_drag notice: {e}")

    def start_native_resize(self, direction: str):
        """
        Enters native window resizing loop via Qt QWindow.startSystemResize()
        and fallback Win32 WM_NCLBUTTONDOWN message.
        """
        edge_map = {
            "top": Qt.Edge.TopEdge,
            "bottom": Qt.Edge.BottomEdge,
            "left": Qt.Edge.LeftEdge,
            "right": Qt.Edge.RightEdge,
            "top-left": Qt.Edge.TopEdge | Qt.Edge.LeftEdge,
            "top-right": Qt.Edge.TopEdge | Qt.Edge.RightEdge,
            "bottom-left": Qt.Edge.BottomEdge | Qt.Edge.LeftEdge,
            "bottom-right": Qt.Edge.BottomEdge | Qt.Edge.RightEdge,
        }
        wh = self.windowHandle()
        edge = edge_map.get(direction)
        if wh and edge and hasattr(wh, "startSystemResize"):
            try:
                if wh.startSystemResize(edge):
                    return
            except Exception:
                pass

        if sys.platform == "win32":
            try:
                self._enable_win32_resize_frame()
                hwnd = int(self.winId())
                hit_map = {
                    "left": win32con.HTLEFT,
                    "right": win32con.HTRIGHT,
                    "top": win32con.HTTOP,
                    "bottom": win32con.HTBOTTOM,
                    "top-left": win32con.HTTOPLEFT,
                    "top-right": win32con.HTTOPRIGHT,
                    "bottom-left": win32con.HTBOTTOMLEFT,
                    "bottom-right": win32con.HTBOTTOMRIGHT,
                }
                hit_code = hit_map.get(direction)
                if hit_code:
                    win32gui.ReleaseCapture()
                    pos = win32gui.GetCursorPos()
                    lparam = (pos[1] << 16) | (pos[0] & 0xFFFF)
                    win32gui.SendMessage(hwnd, win32con.WM_NCLBUTTONDOWN, hit_code, lparam)
            except Exception as e:
                logger.debug(f"start_native_resize notice: {e}")

    def dynamic_resize_to(self, width: int, height: int):
        """Dynamically resize window in real-time as user drags mouse."""
        min_w, min_h = self.minimumWidth(), self.minimumHeight()
        w = max(min_w, min(width, 1600))
        h = max(min_h, min(height, 1800))
        self.resize(w, h)
        self.schedule_geometry_save()

    def dynamic_move_by(self, dx: int, dy: int):
        """Dynamically move window in real-time as user drags mouse."""
        self.move(self.x() + dx, self.y() + dy)
        self.schedule_geometry_save()

    def dynamic_set_geometry(self, x: int, y: int, width: int, height: int):
        """Dynamically set full window geometry in real-time."""
        min_w, min_h = self.minimumWidth(), self.minimumHeight()
        w = max(min_w, min(width, 1600))
        h = max(min_h, min(height, 1800))
        self.setGeometry(x, y, w, h)
        self.schedule_geometry_save()

    def schedule_geometry_save(self):
        """Debounces disk persistence during continuous mouse resizing to maintain 120 FPS."""
        self._save_timer.start()

    def _do_save_geometry(self):
        """Persists the cockpit's last valid position and dimensions to disk."""
        if not self.isVisible() or self.width() < 380 or self.height() < 450:
            return
        data = {
            "x": self.x(),
            "y": self.y(),
            "width": self.width(),
            "height": self.height()
        }
        try:
            with open(self.geometry_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            logger.debug(f"Saved Cockpit geometry: [{self.x()}, {self.y()}, {self.width()}x{self.height()}]")
        except Exception as e:
            logger.debug(f"Failed to persist cockpit geometry: {e}")

    def save_geometry_to_file(self):
        self._do_save_geometry()

    def restore_saved_geometry(self) -> bool:
        """
        Restores the previous window position and dimensions if they safely
        intersect an active monitor's available desktop work area.
        """
        if not os.path.exists(self.geometry_file):
            return False
        try:
            with open(self.geometry_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            x = data.get("x", 100)
            y = data.get("y", 100)
            w = max(440, min(data.get("width", 480), 1200))
            h = max(580, min(data.get("height", 680), 1400))

            # Verify intersection with an existing desktop monitor
            screen = QGuiApplication.screenAt(QPoint(x + 50, y + 50))
            if not screen:
                screen = QGuiApplication.primaryScreen()
                if screen:
                    avail = screen.availableGeometry()
                    x = avail.x() + (avail.width() - w) // 2
                    y = avail.y() + (avail.height() - h) // 2

            if screen:
                avail = screen.availableGeometry()
                w = min(w, avail.width() - 10)
                h = min(h, avail.height() - 10)
                x = max(avail.left() + 5, min(x, avail.right() - w - 5))
                y = max(avail.top() + 5, min(y, avail.bottom() - h - 5))
                self.setGeometry(x, y, w, h)
                logger.info(f"Restored saved Cockpit geometry: [{x}, {y}, {w}x{h}]")
                return True
        except Exception as e:
            logger.warning(f"Error restoring geometry: {e}")
        return False

    def reposition_on_active_screen(self):
        """
        Restores saved geometry if available.
        Otherwise centers on the active monitor where cursor is located.
        """
        if self.restore_saved_geometry():
            return

        cursor_pos = QCursor.pos()
        screen = QGuiApplication.screenAt(cursor_pos) or QGuiApplication.primaryScreen()
        if not screen:
            return

        avail_geom: QRect = screen.availableGeometry()

        # Recommended default dimensions matching Section 3.2: 480px x 680px
        target_w = 480
        target_h = 680

        cockpit_width = max(380, min(target_w, int(avail_geom.width() * 0.95)))
        cockpit_height = max(480, min(target_h, int(avail_geom.height() * 0.90)))

        pos_x = avail_geom.x() + (avail_geom.width() - cockpit_width) // 2
        pos_y = avail_geom.y() + (avail_geom.height() - cockpit_height) // 2

        pos_x = max(avail_geom.left() + 10, min(pos_x, avail_geom.right() - cockpit_width - 10))
        pos_y = max(avail_geom.top() + 10, min(pos_y, avail_geom.bottom() - cockpit_height - 10))

        self.setGeometry(pos_x, pos_y, cockpit_width, cockpit_height)
        logger.info(f"Initialized Cockpit on screen '{screen.name()}' at [{pos_x}, {pos_y}, {cockpit_width}x{cockpit_height}]")

    def moveEvent(self, event):
        super().moveEvent(event)
        self.schedule_geometry_save()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.schedule_geometry_save()

    def hideEvent(self, event):
        super().hideEvent(event)
        self.save_geometry_to_file()

    def enforce_win32_topmost(self):
        """Enforces Windows OS-level HWND_TOPMOST Z-order."""
        if sys.platform != "win32":
            return

        try:
            hwnd = int(self.winId())
            win32gui.SetWindowPos(
                hwnd,
                win32con.HWND_TOPMOST,
                self.x(), self.y(), self.width(), self.height(),
                win32con.SWP_SHOWWINDOW | win32con.SWP_NOACTIVATE
            )
        except Exception as e:
            logger.warning(f"Failed to enforce Win32 topmost: {e}")

    def play_sound_appear(self):
        """Plays the retro activation sound effect."""
        if os.path.exists(self.sound_appear) and sys.platform == "win32":
            try:
                winsound.PlaySound(self.sound_appear, winsound.SND_FILENAME | winsound.SND_ASYNC)
            except Exception:
                pass

    def play_sound_disappear(self):
        """Plays the retro dismissal sound effect."""
        if os.path.exists(self.sound_disappear) and sys.platform == "win32":
            try:
                winsound.PlaySound(self.sound_disappear, winsound.SND_FILENAME | winsound.SND_ASYNC)
            except Exception:
                pass

    def trigger_quick_action_in_frontend(self):
        """Dispatches quick action event to the React frontend."""
        js = "window.dispatchEvent(new CustomEvent('ops:quick-action'));"
        self.web_view.page().runJavaScript(js)

    def trigger_hitl_in_frontend(self, approval_data: dict):
        """Dispatches HITL approval event to the React frontend."""
        payload_json = json.dumps(approval_data)
        js = f"window.dispatchEvent(new CustomEvent('ops:hitl-approval', {{ detail: {payload_json} }}));"
        self.web_view.page().runJavaScript(js)

    def reload_frontend(self):
        """Reloads the frontend webview."""
        self.web_view.reload()
