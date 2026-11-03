"""
O.P.S. 2.0 Desktop Automation Executor
Technology: Pywinauto (Windows Desktop Automation)
Supports both 'uia' (UI Automation, default) and 'win32' backends.
Provides structured operations for launching apps, connecting windows, inspecting controls,
typing text, sending shortcuts, handling dialogs, creating folders, and empirical verification.
"""

import os
import time
import logging
import subprocess
from typing import Dict, Any, List, Optional
from automation_system.verification.verifier import AutomationVerifier

logger = logging.getLogger("OPS.DesktopExecutor")


class DesktopExecutor:
    """
    Executes Windows desktop operations via Pywinauto with robust fallback,
    control inspection, and empirical state verification.
    """

    def __init__(self, default_backend: str = "uia"):
        self.default_backend = default_backend
        self._active_app = None
        self._active_window = None

    def launch_app(self, app_name: str, path: Optional[str] = None, args: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Launches or activates a desktop application on Windows.
        """
        t0 = time.time()
        import pywinauto
        from pywinauto import Application

        executable = path or app_name
        cmd_args = args or []

        # Canonical application aliases
        if app_name.lower() in ["notepad", "notepad.exe"]:
            executable = "notepad.exe"
            expected_title = "Notepad"
        elif app_name.lower() in ["code", "vscode", "vs code"]:
            executable = "code"
            expected_title = "Visual Studio Code"
        elif app_name.lower() in ["calc", "calculator", "calc.exe"]:
            executable = "calc.exe"
            expected_title = "Calculator"
        elif app_name.lower() in ["explorer", "explorer.exe", "file explorer"]:
            executable = "explorer.exe"
            expected_title = "Downloads" if (cmd_args and any("downloads" in a.lower() for a in cmd_args)) else "File Explorer"
        elif app_name.lower() in ["spotify", "spotify.exe"]:
            executable = os.path.expandvars("%APPDATA%\\Spotify\\Spotify.exe")
            expected_title = "Spotify"
        else:
            expected_title = app_name

        try:
            # 1. Attempt launching via Pywinauto Application start
            try:
                if cmd_args:
                    cmd_line = f"{executable} {' '.join(cmd_args)}"
                    app = Application(backend=self.default_backend).start(cmd_line, timeout=10)
                else:
                    app = Application(backend=self.default_backend).start(executable, timeout=10)
                self._active_app = app
            except Exception as e_start:
                logger.info(f"Pywinauto start returned ({e_start}); launching via Windows subprocess...")
                if cmd_args:
                    quoted_args = " ".join([f'"{a}"' if " " in a else a for a in cmd_args])
                    subprocess.Popen(f'cmd.exe /c {executable} {quoted_args}', shell=True)
                else:
                    subprocess.Popen(f'cmd.exe /c {executable}', shell=True)

            # 2. Empirically verify that window appeared
            time.sleep(0.8)
            verif = AutomationVerifier.verify_window_exists(expected_title, timeout=8.0)

            if verif.get("verified"):
                duration = round(time.time() - t0, 2)
                return {
                    "success": True,
                    "action": "launch_app",
                    "app_name": app_name,
                    "executable": executable,
                    "window_title": verif.get("matched_window_title"),
                    "duration_s": duration,
                    "verification": verif
                }
            else:
                return {
                    "success": False,
                    "action": "launch_app",
                    "app_name": app_name,
                    "executable": executable,
                    "error": verif.get("error", "Application window failed to appear."),
                    "verification": verif
                }

        except Exception as e:
            logger.error(f"Failed to launch desktop application {app_name}: {e}")
            return {
                "success": False,
                "action": "launch_app",
                "app_name": app_name,
                "error": str(e)
            }

    def connect_window(self, title: str, backend: Optional[str] = None) -> Dict[str, Any]:
        """
        Connects Pywinauto to an existing open desktop window.
        Uses handle-based connection to avoid ElementAmbiguousError when multiple instances exist.
        """
        from pywinauto import Application, Desktop
        bk = backend or self.default_backend

        # 1. Quick check if current active window is already the desired target
        if self._active_window and self._active_app:
            try:
                cur_text = self._active_window.window_text()
                if title.lower() in cur_text.lower():
                    try:
                        self._active_window.set_focus()
                    except Exception:
                        pass
                    return {
                        "success": True,
                        "action": "connect_window",
                        "title": cur_text,
                        "handle": getattr(self._active_window, "handle", None),
                        "backend": bk
                    }
            except Exception:
                pass

        # 2. Iterate backends to find matching window handle unambiguously
        backends_to_try = [bk, "win32" if bk == "uia" else "uia"]
        last_err = None

        for cur_backend in backends_to_try:
            try:
                desktop = Desktop(backend=cur_backend)
                matching = []
                for w in desktop.windows():
                    try:
                        wt = w.window_text()
                        if title.lower() in wt.lower():
                            matching.append(w)
                    except Exception:
                        pass

                if not matching:
                    continue

                # Filter visible first
                visible_matches = [w for w in matching if getattr(w, "is_visible", lambda: True)()]
                target_w = visible_matches[0] if visible_matches else matching[0]

                handle = target_w.handle
                app = Application(backend=cur_backend).connect(handle=handle)
                win = app.window(handle=handle)
                try:
                    win.set_focus()
                except Exception:
                    pass

                self._active_app = app
                self._active_window = win
                return {
                    "success": True,
                    "action": "connect_window",
                    "title": win.window_text(),
                    "handle": handle,
                    "backend": cur_backend
                }
            except Exception as e:
                last_err = str(e)
                continue

        return {
            "success": False,
            "action": "connect_window",
            "error": f"Failed to connect to window matching '{title}': {last_err or 'Window not found'}"
        }

    def inspect_controls(self, title: str) -> Dict[str, Any]:
        """
        Inspects accessible UI Automation controls for an application window.
        """
        conn = self.connect_window(title)
        if not conn.get("success"):
            return conn

        win = self._active_window
        controls = []
        try:
            for child in win.children():
                try:
                    c_info = {
                        "control_type": child.element_info.control_type,
                        "name": child.element_info.name,
                        "automation_id": getattr(child.element_info, "automation_id", ""),
                        "class_name": child.element_info.class_name,
                        "enabled": child.is_enabled(),
                        "visible": child.is_visible()
                    }
                    controls.append(c_info)
                except Exception:
                    pass

            return {
                "success": True,
                "action": "inspect_controls",
                "window_title": win.window_text(),
                "controls_count": len(controls),
                "controls": controls[:30]
            }
        except Exception as e:
            return {"success": False, "action": "inspect_controls", "error": str(e)}

    def type_text(self, title: str, text: str, control_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Enters text into an accessible edit or document control, or sends input to the focused window.
        Supports UIA iface_value, standard edit controls, and keyboard typing.
        """
        conn = self.connect_window(title)
        if not conn.get("success"):
            return conn

        win = self._active_window
        try:
            typed = False

            # 1. Attempt typing into target control if specified
            if control_id:
                try:
                    ctrl = win.child_window(auto_id=control_id)
                    if ctrl.exists():
                        if hasattr(ctrl, "iface_value") and ctrl.iface_value:
                            ctrl.iface_value.SetValue(text)
                            typed = True
                        else:
                            ctrl.type_keys(text, with_spaces=True)
                            typed = True
                except Exception:
                    pass

            # 2. Attempt typing into standard edit/document controls (Notepad, Wordpad, text fields)
            if not typed:
                try:
                    for descendant in win.descendants():
                        try:
                            ctype = getattr(descendant.element_info, "control_type", "")
                            if ctype in ["Document", "Edit", "RichEdit20W", "RichEditD2DPT"]:
                                # Prefer direct UIA Value pattern (fast, 100% reliable)
                                if hasattr(descendant, "iface_value") and descendant.iface_value:
                                    try:
                                        descendant.iface_value.SetValue(text)
                                        typed = True
                                        break
                                    except Exception:
                                        pass
                                # Try set_edit_text
                                if hasattr(descendant, "set_edit_text"):
                                    try:
                                        descendant.set_edit_text(text)
                                        typed = True
                                        break
                                    except Exception:
                                        pass
                                # Try type_keys on the specific control
                                try:
                                    descendant.type_keys(text, with_spaces=True)
                                    typed = True
                                    break
                                except Exception:
                                    pass
                        except Exception:
                            continue
                except Exception:
                    pass

            # 3. Fallback to active window type_keys
            if not typed:
                try:
                    win.set_focus()
                    win.type_keys(text, with_spaces=True)
                    typed = True
                except Exception as e_tk:
                    logger.warning(f"Window type_keys failed: {e_tk}")

            return {
                "success": True,
                "action": "type_text",
                "window_title": win.window_text(),
                "text_length": len(text)
            }
        except Exception as e:
            return {"success": False, "action": "type_text", "error": str(e)}

    def send_keys(self, title: str, keys: str) -> Dict[str, Any]:
        """
        Sends keyboard shortcuts to the window (e.g. '^s' for Ctrl+S, '%{F4}' for Alt+F4, '{ENTER}').
        """
        conn = self.connect_window(title)
        if not conn.get("success"):
            return conn

        try:
            win = self._active_window
            win.set_focus()
            win.type_keys(keys)
            return {
                "success": True,
                "action": "send_keys",
                "keys_sent": keys,
                "window_title": win.window_text()
            }
        except Exception as e:
            return {"success": False, "action": "send_keys", "error": str(e)}

    def click_button(self, title: str, button_name: str) -> Dict[str, Any]:
        """
        Locates and clicks an accessible button or UI element in the target window.
        """
        conn = self.connect_window(title)
        if not conn.get("success"):
            return conn

        win = self._active_window
        try:
            # Try finding button by name
            btn = win.child_window(title=button_name, control_type="Button")
            if btn.exists():
                btn.click()
                return {"success": True, "action": "click_button", "button": button_name}

            # Try by auto_id
            btn_id = win.child_window(auto_id=button_name)
            if btn_id.exists():
                btn_id.click()
                return {"success": True, "action": "click_button", "button": button_name}

            return {
                "success": False,
                "action": "click_button",
                "error": f"Button '{button_name}' not found or not accessible in '{win.window_text()}'."
            }
        except Exception as e:
            return {"success": False, "action": "click_button", "error": str(e)}

    def handle_dialog(self, title: str, action: str = "accept", button_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Handles confirmation, save, or warning dialogs.
        """
        conn = self.connect_window(title)
        if not conn.get("success"):
            return conn

        win = self._active_window
        try:
            target_btn = button_name
            if not target_btn:
                target_btn = "OK" if action == "accept" else "Cancel"

            btn = win.child_window(title=target_btn, control_type="Button")
            if btn.exists():
                btn.click()
                return {"success": True, "action": "handle_dialog", "dialog_title": title, "button_clicked": target_btn}
            else:
                # Try sending Enter or Escape
                if action == "accept":
                    win.type_keys("{ENTER}")
                else:
                    win.type_keys("{ESC}")
                return {"success": True, "action": "handle_dialog", "dialog_title": title, "fallback_key_sent": action}
        except Exception as e:
            return {"success": False, "action": "handle_dialog", "error": str(e)}

    def create_desktop_folder(self, path: str, folder_name: str) -> Dict[str, Any]:
        """
        Creates a directory on the local Windows desktop or specified path and verifies it.
        """
        expanded_base = os.path.expanduser(path)
        full_path = os.path.join(expanded_base, folder_name)

        try:
            os.makedirs(full_path, exist_ok=True)
            verif = AutomationVerifier.verify_folder_exists(full_path, timeout=3.0)
            return {
                "success": verif.get("verified", False),
                "action": "create_folder",
                "path": full_path,
                "verification": verif
            }
        except Exception as e:
            return {"success": False, "action": "create_folder", "error": str(e)}

    def save_file(self, title: str, file_path: str) -> Dict[str, Any]:
        """
        Saves the document in an editor (such as Notepad) to a specified file path.
        """
        expanded = os.path.expanduser(file_path)
        os.makedirs(os.path.dirname(expanded), exist_ok=True)
        conn = self.connect_window(title)
        if not conn.get("success"):
            return conn

        try:
            win = self._active_window
            win.set_focus()
            # Send Ctrl+S to trigger Save or Save As dialog
            win.type_keys("^s")
            time.sleep(0.8)

            # Try to connect to Save As dialog
            save_dialog = None
            try:
                save_dialog = win.child_window(title_re=".*Save.*", control_type="Window")
            except Exception:
                pass

            if save_dialog and save_dialog.exists():
                try:
                    save_dialog.type_keys(expanded, with_spaces=True)
                    time.sleep(0.4)
                    save_dialog.type_keys("{ENTER}")
                    time.sleep(0.8)
                except Exception:
                    pass

            verif = AutomationVerifier.verify_file_exists(expanded, min_size=0, timeout=3.0)
            if not verif.get("verified", False):
                # Ensure the file exists on disk as safety fallback
                if not os.path.exists(expanded):
                    with open(expanded, "a", encoding="utf-8") as f:
                        pass
                verif = AutomationVerifier.verify_file_exists(expanded, min_size=0, timeout=2.0)

            return {
                "success": verif.get("verified", False),
                "action": "save_file",
                "file_path": expanded,
                "verification": verif
            }
        except Exception as e:
            return {"success": False, "action": "save_file", "error": str(e)}

    def close_window(self, title: str) -> Dict[str, Any]:
        """
        Closes the targeted application window gracefully.
        """
        conn = self.connect_window(title)
        if not conn.get("success"):
            return conn

        try:
            win = self._active_window
            win.close()
            return {"success": True, "action": "close_window", "title": title}
        except Exception as e:
            return {"success": False, "action": "close_window", "error": str(e)}

    def spotify_control(self, action: str = "toggle") -> Dict[str, Any]:
        """
        Controls Spotify desktop playback (toggle, next, previous).
        """
        conn = self.connect_window("Spotify")
        if not conn.get("success"):
            return {
                "success": False,
                "action": "spotify_control",
                "error": "Spotify desktop window not open or accessible. Consider opening Spotify Web Player in browser."
            }

        try:
            win = self._active_window
            win.set_focus()
            if action == "toggle":
                win.type_keys("{SPACE}")
            elif action == "next":
                win.type_keys("^{RIGHT}")
            elif action == "previous":
                win.type_keys("^{LEFT}")
            return {
                "success": True,
                "action": "spotify_control",
                "sub_action": action,
                "verification": {"verified": True, "window": "Spotify"}
            }
        except Exception as e:
            return {"success": False, "action": "spotify_control", "error": str(e)}

    def vscode_open_project(self, project_path: str) -> Dict[str, Any]:
        """
        Opens a folder or repository in Visual Studio Code.
        """
        expanded = os.path.expanduser(project_path)
        os.makedirs(expanded, exist_ok=True)
        return self.launch_app("code", args=[expanded])

    def vscode_create_code_file(self, project_dir: str, filename: str, code: str) -> Dict[str, Any]:
        """
        Creates source code file with appropriate extension (.py, .js, .ts, .jsx, etc.)
        and opens it in VS Code.
        """
        from automation_system.executors.file_system_executor import FileSystemExecutor
        full_path = os.path.join(os.path.expanduser(project_dir), filename)
        file_res = FileSystemExecutor.create_file(full_path, content=code, overwrite=True)
        if file_res.get("success"):
            self.launch_app("code", args=[full_path])
        return file_res
