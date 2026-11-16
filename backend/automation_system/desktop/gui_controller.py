"""
O.P.S. 2.0 Desktop Automation Engine — Module 2: Window and GUI Controller
Provides Pywinauto-based UI automation across UIA and Win32 backends.
Implements accessible locators (Automation ID, Control Type, Title/Name, Class Name),
safe typing, hotkeys, button clicking, control inspection, and text extraction.
"""

import time
import logging
import ctypes
from typing import Dict, Any, List, Optional, Union
from automation_system.desktop.application_controller import ensure_desktop_access, ApplicationController

logger = logging.getLogger("OPS.Desktop.GUIController")


class GUIController:
    """
    Handles Windows window manipulation, accessible element discovery,
    keyboard/mouse interactions, and text extraction via Pywinauto.
    """

    def __init__(self, default_backend: str = "uia"):
        self.default_backend = default_backend
        self._active_app = None
        self._active_window = None
        ensure_desktop_access()

    def connect_window(self, title_or_handle: Union[str, int], backend: Optional[str] = None) -> Dict[str, Any]:
        """
        Connects Pywinauto to an existing window.
        Uses exact handle connection to prevent ElementAmbiguousError.
        """
        ensure_desktop_access()
        from pywinauto import Application, Desktop
        bk = backend or self.default_backend

        # 1. Handle passed as integer
        if isinstance(title_or_handle, int):
            try:
                app = Application(backend=bk).connect(handle=title_or_handle)
                win = app.window(handle=title_or_handle)
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
                    "handle": title_or_handle,
                    "backend": bk
                }
            except Exception as e:
                return {"success": False, "action": "connect_window", "error": str(e)}

        title_str = str(title_or_handle).strip()

        # 2. Check if currently active window already matches
        if self._active_window:
            try:
                cur_text = self._active_window.window_text()
                if title_str.lower() in cur_text.lower():
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

        # 3. Search via ApplicationController / EnumWindows handle
        running = ApplicationController.find_running_window(title_str)
        if running and running.get("hwnd"):
            handle = running["hwnd"]
            ApplicationController.bring_to_front(handle)
            backends_to_try = [bk, "win32" if bk == "uia" else "uia"]
            for cur_bk in backends_to_try:
                try:
                    app = Application(backend=cur_bk).connect(handle=handle)
                    win = app.window(handle=handle)
                    self._active_app = app
                    self._active_window = win
                    return {
                        "success": True,
                        "action": "connect_window",
                        "title": win.window_text() or running.get("title", ""),
                        "handle": handle,
                        "backend": cur_bk
                    }
                except Exception:
                    continue

        # 4. Search Desktop windows directly
        backends_to_try = [bk, "win32" if bk == "uia" else "uia"]
        for cur_bk in backends_to_try:
            try:
                desktop = Desktop(backend=cur_bk)
                for w in desktop.windows():
                    try:
                        w_text = w.window_text()
                        if title_str.lower() in w_text.lower():
                            h = getattr(w, "handle", None)
                            app = Application(backend=cur_bk).connect(handle=h)
                            win = app.window(handle=h)
                            try:
                                win.set_focus()
                            except Exception:
                                pass
                            self._active_app = app
                            self._active_window = win
                            return {
                                "success": True,
                                "action": "connect_window",
                                "title": w_text,
                                "handle": h,
                                "backend": cur_bk
                            }
                    except Exception:
                        continue
            except Exception:
                continue

        return {
            "success": False,
            "action": "connect_window",
            "error": f"Could not find or connect to window matching '{title_str}'."
        }

    def inspect_controls(self, title: str, max_elements: int = 40) -> Dict[str, Any]:
        """
        Inspects accessible UI Automation controls for the targeted window.
        Returns list of interactive controls with types, names, and automation IDs.
        """
        conn = self.connect_window(title)
        if not conn.get("success"):
            running = ApplicationController.find_running_window(title)
            if running and running.get("pid"):
                try:
                    import pywinauto
                    pywinauto.keyboard.send_keys(text, with_spaces=True)
                    return {
                        "success": True,
                        "action": "type_text",
                        "target": title,
                        "typed_length": len(text)
                    }
                except Exception:
                    pass
            return conn

        win = self._active_window
        controls = []
        try:
            for child in win.descendants():
                if len(controls) >= max_elements:
                    break
                try:
                    c_info = {
                        "control_type": getattr(child.element_info, "control_type", ""),
                        "name": getattr(child.element_info, "name", ""),
                        "automation_id": getattr(child.element_info, "automation_id", ""),
                        "class_name": getattr(child.element_info, "class_name", ""),
                        "enabled": child.is_enabled() if hasattr(child, "is_enabled") else True,
                        "visible": child.is_visible() if hasattr(child, "is_visible") else True
                    }
                    if c_info["name"] or c_info["automation_id"]:
                        controls.append(c_info)
                except Exception:
                    continue

            return {
                "success": True,
                "action": "inspect_controls",
                "window_title": win.window_text(),
                "controls_count": len(controls),
                "controls": controls
            }
        except Exception as e:
            return {"success": False, "action": "inspect_controls", "error": str(e)}

    def find_element(self, win, locator: Union[str, Dict[str, Any]]):
        """
        Finds a child element using prioritized locator strategies:
        1. auto_id
        2. control_type + title/name
        3. title/name only
        4. class_name
        """
        if isinstance(locator, str):
            # Try by auto_id first
            try:
                elem = win.child_window(auto_id=locator)
                if elem.exists():
                    return elem
            except Exception:
                pass
            # Try by title / name
            try:
                elem = win.child_window(title=locator)
                if elem.exists():
                    return elem
            except Exception:
                pass
            # Try by title regex
            try:
                elem = win.child_window(title_re=f".*{locator}.*")
                if elem.exists():
                    return elem
            except Exception:
                pass
            # Search descendants
            try:
                for desc in win.descendants():
                    try:
                        name = getattr(desc.element_info, "name", "")
                        auto_id = getattr(desc.element_info, "automation_id", "")
                        if locator.lower() in name.lower() or locator.lower() in auto_id.lower():
                            return desc
                    except Exception:
                        continue
            except Exception:
                pass
            return None

        # Dict locator
        kwargs = {}
        if locator.get("auto_id"):
            kwargs["auto_id"] = locator["auto_id"]
        if locator.get("control_type"):
            kwargs["control_type"] = locator["control_type"]
        if locator.get("title"):
            kwargs["title"] = locator["title"]
        if locator.get("class_name"):
            kwargs["class_name"] = locator["class_name"]

        try:
            elem = win.child_window(**kwargs)
            if elem.exists():
                return elem
        except Exception:
            pass
        return None

    def click_button(self, title: str, button_locator: Union[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Locates and clicks an accessible button or UI control.
        """
        conn = self.connect_window(title)
        if not conn.get("success"):
            running = ApplicationController.find_running_window(title)
            if running and running.get("pid"):
                try:
                    import pywinauto
                    pywinauto.keyboard.send_keys(text, with_spaces=True)
                    return {
                        "success": True,
                        "action": "type_text",
                        "target": title,
                        "typed_length": len(text)
                    }
                except Exception:
                    pass
            return conn

        win = self._active_window
        try:
            target_elem = self.find_element(win, button_locator)
            if not target_elem and isinstance(button_locator, str):
                # Try finding button specifically by title
                try:
                    btn = win.child_window(title=button_locator, control_type="Button")
                    if btn.exists():
                        target_elem = btn
                except Exception:
                    pass

            if target_elem and target_elem.exists():
                try:
                    target_elem.click_input()
                except Exception:
                    target_elem.click()
                return {
                    "success": True,
                    "action": "click_button",
                    "window_title": win.window_text(),
                    "button": str(button_locator)
                }

            return {
                "success": False,
                "action": "click_button",
                "error": f"Button or control '{button_locator}' not found in window '{win.window_text()}'."
            }
        except Exception as e:
            return {"success": False, "action": "click_button", "error": str(e)}

    def type_text(
        self,
        title: str,
        text: str,
        control_locator: Optional[Union[str, Dict[str, Any]]] = None,
        replace: bool = False
    ) -> Dict[str, Any]:
        """
        Enters text into an accessible edit control, document surface, or active window.
        Uses UIA ValuePattern (SetValue) for instant fidelity, falling back to set_edit_text and type_keys.
        """
        conn = self.connect_window(title)
        if not conn.get("success"):
            running = ApplicationController.find_running_window(title)
            if running and running.get("pid"):
                try:
                    import pywinauto
                    pywinauto.keyboard.send_keys(text, with_spaces=True)
                    return {
                        "success": True,
                        "action": "type_text",
                        "target": title,
                        "typed_length": len(text)
                    }
                except Exception:
                    pass
            return conn

        win = self._active_window
        try:
            typed = False

            # 1. Target specific control if locator supplied
            if control_locator:
                target_ctrl = self.find_element(win, control_locator)
                if target_ctrl and target_ctrl.exists():
                    if hasattr(target_ctrl, "iface_value") and target_ctrl.iface_value:
                        try:
                            if replace:
                                target_ctrl.iface_value.SetValue(text)
                            else:
                                cur_val = target_ctrl.iface_value.CurrentValue or ""
                                target_ctrl.iface_value.SetValue(cur_val + text)
                            typed = True
                        except Exception:
                            pass
                    if not typed and hasattr(target_ctrl, "set_edit_text"):
                        try:
                            target_ctrl.set_edit_text(text)
                            typed = True
                        except Exception:
                            pass
                    if not typed:
                        try:
                            target_ctrl.type_keys(text, with_spaces=True)
                            typed = True
                        except Exception:
                            pass

            # 2. Search for standard edit / document controls (Notepad, Wordpad, text input fields)
            if not typed:
                for desc in win.descendants():
                    try:
                        ctype = getattr(desc.element_info, "control_type", "")
                        cname = getattr(desc.element_info, "class_name", "")
                        if ctype in ["Document", "Edit", "Text"] or "Edit" in cname:
                            # UIA ValuePattern
                            if hasattr(desc, "iface_value") and desc.iface_value:
                                try:
                                    if replace:
                                        desc.iface_value.SetValue(text)
                                    else:
                                        cur_val = desc.iface_value.CurrentValue or ""
                                        desc.iface_value.SetValue(cur_val + text)
                                    typed = True
                                    break
                                except Exception:
                                    pass
                            # set_edit_text
                            if hasattr(desc, "set_edit_text"):
                                try:
                                    desc.set_edit_text(text)
                                    typed = True
                                    break
                                except Exception:
                                    pass
                            # type_keys
                            try:
                                desc.type_keys(text, with_spaces=True)
                                typed = True
                                break
                            except Exception:
                                pass
                    except Exception:
                        continue

            # 3. Fallback to active window type_keys
            if not typed:
                win.set_focus()
                if replace:
                    win.type_keys("^a{BACKSPACE}")
                win.type_keys(text, with_spaces=True)
                typed = True

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
            running = ApplicationController.find_running_window(title)
            if running and running.get("pid"):
                try:
                    import pywinauto
                    pywinauto.keyboard.send_keys(text, with_spaces=True)
                    return {
                        "success": True,
                        "action": "type_text",
                        "target": title,
                        "typed_length": len(text)
                    }
                except Exception:
                    pass
            return conn

        try:
            win = self._active_window
            win.set_focus()
            time.sleep(0.1)
            try:
                win.type_keys(keys)
            except Exception as e_tk:
                logger.info(f"win.type_keys failed ({e_tk}), using keybd_event fallback...")
                user32 = ctypes.windll.user32
                if keys.startswith("^") and len(keys) == 2:
                    char_code = ord(keys[1].upper())
                    VK_CONTROL = 0x11
                    user32.keybd_event(VK_CONTROL, 0, 0, 0)
                    user32.keybd_event(char_code, 0, 0, 0)
                    time.sleep(0.05)
                    user32.keybd_event(char_code, 0, 2, 0)
                    user32.keybd_event(VK_CONTROL, 0, 2, 0)
                elif "%{F4}" in keys:
                    VK_MENU = 0x12
                    VK_F4 = 0x73
                    user32.keybd_event(VK_MENU, 0, 0, 0)
                    user32.keybd_event(VK_F4, 0, 0, 0)
                    time.sleep(0.05)
                    user32.keybd_event(VK_F4, 0, 2, 0)
                    user32.keybd_event(VK_MENU, 0, 2, 0)
                else:
                    pass

            return {
                "success": True,
                "action": "send_keys",
                "keys_sent": keys,
                "window_title": win.window_text()
            }
        except Exception as e:
            return {"success": False, "action": "send_keys", "error": str(e)}

    def read_control_text(self, title: str, control_locator: Optional[Union[str, Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Reads visible or edit text from a control or window surface.
        """
        conn = self.connect_window(title)
        if not conn.get("success"):
            running = ApplicationController.find_running_window(title)
            if running and running.get("pid"):
                try:
                    import pywinauto
                    pywinauto.keyboard.send_keys(text, with_spaces=True)
                    return {
                        "success": True,
                        "action": "type_text",
                        "target": title,
                        "typed_length": len(text)
                    }
                except Exception:
                    pass
            return conn

        win = self._active_window
        try:
            if control_locator:
                ctrl = self.find_element(win, control_locator)
                if ctrl and ctrl.exists():
                    if hasattr(ctrl, "iface_value") and ctrl.iface_value:
                        return {"success": True, "text": ctrl.iface_value.CurrentValue or ""}
                    if hasattr(ctrl, "window_text"):
                        return {"success": True, "text": ctrl.window_text()}

            # Search edit/document controls
            for desc in win.descendants():
                try:
                    ctype = getattr(desc.element_info, "control_type", "")
                    if ctype in ["Document", "Edit", "Text"]:
                        if hasattr(desc, "iface_value") and desc.iface_value:
                            val = desc.iface_value.CurrentValue
                            if val:
                                return {"success": True, "text": val}
                        if hasattr(desc, "window_text"):
                            val = desc.window_text()
                            if val:
                                return {"success": True, "text": val}
                except Exception:
                    continue

            return {"success": True, "text": win.window_text()}
        except Exception as e:
            return {"success": False, "error": str(e)}
