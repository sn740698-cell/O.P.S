"""
O.P.S. 2.0 Desktop Automation Engine — Module 1: Application Controller
Resolves, launches, detects, focuses, and gracefully closes Windows applications.
Supports multi-tier resolution (PATH, Registry App Paths, Program Files, Start Menu),
running instance detection, foreground activation, and safe closure with unsaved-changes detection.
"""

import os
import sys
import time
import shutil
import logging
import winreg
import ctypes
import subprocess
from typing import Dict, Any, List, Optional, Tuple
import psutil

logger = logging.getLogger("OPS.Desktop.ApplicationController")

# Canonical aliases and standard Windows executables
CANONICAL_APP_ALIASES: Dict[str, Dict[str, Any]] = {
    "notepad": {"exe": "notepad.exe", "title": "Notepad", "category": "editor"},
    "vs code": {"exe": "code", "title": "Visual Studio Code", "category": "ide"},
    "vscode": {"exe": "code", "title": "Visual Studio Code", "category": "ide"},
    "code": {"exe": "code", "title": "Visual Studio Code", "category": "ide"},
    "visual studio code": {"exe": "code", "title": "Visual Studio Code", "category": "ide"},
    "calculator": {"exe": "calc.exe", "title": "Calculator", "category": "utility"},
    "calc": {"exe": "calc.exe", "title": "Calculator", "category": "utility"},
    "file explorer": {"exe": "explorer.exe", "title": "File Explorer", "category": "system"},
    "explorer": {"exe": "explorer.exe", "title": "File Explorer", "category": "system"},
    "paint": {"exe": "mspaint.exe", "title": "Paint", "category": "graphics"},
    "mspaint": {"exe": "mspaint.exe", "title": "Paint", "category": "graphics"},
    "cmd": {"exe": "cmd.exe", "title": "Command Prompt", "category": "terminal"},
    "command prompt": {"exe": "cmd.exe", "title": "Command Prompt", "category": "terminal"},
    "powershell": {"exe": "powershell.exe", "title": "Windows PowerShell", "category": "terminal"},
    "windows terminal": {"exe": "wt.exe", "title": "Terminal", "category": "terminal"},
    "terminal": {"exe": "wt.exe", "title": "Terminal", "category": "terminal"},
    "wt": {"exe": "wt.exe", "title": "Terminal", "category": "terminal"},
    "chrome": {"exe": "chrome.exe", "title": "Google Chrome", "category": "browser"},
    "google chrome": {"exe": "chrome.exe", "title": "Google Chrome", "category": "browser"},
    "edge": {"exe": "msedge.exe", "title": "Microsoft Edge", "category": "browser"},
    "microsoft edge": {"exe": "msedge.exe", "title": "Microsoft Edge", "category": "browser"},
    "word": {"exe": "WINWORD.EXE", "title": "Word", "category": "office"},
    "excel": {"exe": "EXCEL.EXE", "title": "Excel", "category": "office"},
    "powerpoint": {"exe": "POWERPNT.EXE", "title": "PowerPoint", "category": "office"},
    "spotify": {"exe": "spotify.exe", "title": "Spotify", "category": "media"},
    "vlc": {"exe": "vlc.exe", "title": "VLC media player", "category": "media"},
}


def ensure_desktop_access() -> bool:
    """
    Ensures current thread is attached to the interactive Windows user desktop.
    Critical when running from services, worker threads, or subshells.
    """
    if sys.platform != "win32":
        return False
    try:
        user32 = ctypes.windll.user32
        hinput = user32.OpenInputDesktop(0, False, 0x0100)  # DESKTOP_SWITCHDESKTOP / READOBJECTS
        if hinput:
            user32.SetThreadDesktop(hinput)
            return True
    except Exception as e:
        logger.debug(f"Desktop attach notice: {e}")
    return False


class ApplicationController:
    """
    Controller responsible for application resolution, instance detection,
    lifecycle management, foreground focusing, and safe closure.
    """

    def __init__(self, default_backend: str = "uia"):
        self.default_backend = default_backend
        ensure_desktop_access()

    @classmethod
    def resolve_application(cls, app_name: str) -> Optional[str]:
        """
        Resolves an application name to an absolute executable path or runnable command.
        Resolution tiers:
        1. Existing path on disk
        2. PATH lookup (shutil.which)
        3. Canonical alias mapping
        4. Windows Registry App Paths (HKLM & HKCU)
        5. Common Program Files & LocalAppData paths
        6. Start Menu shortcuts
        """
        if not app_name:
            return None

        clean_name = app_name.strip().strip('"\'')
        lower_name = clean_name.lower()

        # 1. Direct path check
        if os.path.exists(clean_name) and os.path.isfile(clean_name):
            return os.path.abspath(clean_name)

        # 2. Canonical alias lookup
        alias_info = CANONICAL_APP_ALIASES.get(lower_name)
        target_name = alias_info["exe"] if alias_info else clean_name

        # 3. PATH check (with and without .exe)
        found = shutil.which(target_name)
        if found:
            return found
        if not target_name.lower().endswith(".exe"):
            found = shutil.which(f"{target_name}.exe")
            if found:
                return found

        # 4. Windows Registry App Paths
        names_to_try = [target_name]
        if not target_name.lower().endswith(".exe"):
            names_to_try.append(f"{target_name}.exe")
        if target_name != clean_name:
            names_to_try.append(clean_name)
            if not clean_name.lower().endswith(".exe"):
                names_to_try.append(f"{clean_name}.exe")

        for root_key in (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE):
            for candidate in names_to_try:
                try:
                    sub_key = f"SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\App Paths\\{candidate}"
                    with winreg.OpenKey(root_key, sub_key) as k:
                        val, _ = winreg.QueryValueEx(k, "")
                        if val and os.path.exists(val):
                            return val
                except OSError:
                    continue

        # 5. Standard installation folders (shallow scan, max depth 2)
        standard_dirs = [
            os.environ.get("ProgramFiles", r"C:\Program Files"),
            os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)"),
            os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs"),
            os.path.join(os.environ.get("LOCALAPPDATA", ""), "Microsoft", "WindowsApps"),
            os.environ.get("APPDATA", ""),
        ]

        for base_dir in standard_dirs:
            if not base_dir or not os.path.exists(base_dir):
                continue
            for candidate in names_to_try:
                # Direct check
                cand_path = os.path.join(base_dir, candidate)
                if os.path.exists(cand_path):
                    return cand_path

            # Shallow check of immediate subdirectories only
            try:
                with os.scandir(base_dir) as entries:
                    for entry in entries:
                        if entry.is_dir(follow_symlinks=False):
                            for candidate in names_to_try:
                                cand_sub = os.path.join(entry.path, candidate)
                                if os.path.exists(cand_sub):
                                    return cand_sub
                                cand_sub2 = os.path.join(entry.path, "Application", candidate)
                                if os.path.exists(cand_sub2):
                                    return cand_sub2
            except Exception:
                continue

        # 6. Start Menu shortcuts
        start_menu_dirs = [
            os.path.expandvars(r"%APPDATA%\Microsoft\Windows\Start Menu\Programs"),
            os.path.expandvars(r"%ProgramData%\Microsoft\Windows\Start Menu\Programs"),
        ]
        for sm_dir in start_menu_dirs:
            if not os.path.exists(sm_dir):
                continue
            try:
                for root, _, files in os.walk(sm_dir):
                    for f in files:
                        if f.lower().endswith(".lnk") and lower_name in f.lower():
                            return os.path.join(root, f)
            except Exception:
                continue

        return None

    @classmethod
    def get_expected_title(cls, app_name: str) -> str:
        """
        Returns expected window title for an application name or alias.
        """
        lower = app_name.lower().strip()
        if lower in CANONICAL_APP_ALIASES:
            return CANONICAL_APP_ALIASES[lower]["title"]
        # Strip extension if present
        base = os.path.splitext(os.path.basename(app_name))[0]
        return base.capitalize()

    @classmethod
    def find_running_window(cls, app_name_or_title: str) -> Optional[Dict[str, Any]]:
        """
        Searches for an open window matching the application name or expected title.
        Returns handle, title, and process ID if found.
        """
        ensure_desktop_access()
        expected = cls.get_expected_title(app_name_or_title).lower()
        alias = app_name_or_title.lower().strip()

        # Method 1: EnumWindows via Win32 ctypes
        matching_windows = []
        user32 = ctypes.windll.user32

        def enum_cb(hwnd, lparam):
            if user32.IsWindowVisible(hwnd):
                length = user32.GetWindowTextLengthW(hwnd)
                if length > 0:
                    buff = ctypes.create_unicode_buffer(length + 1)
                    user32.GetWindowTextW(hwnd, buff, length + 1)
                    title = buff.value
                    t_lower = title.lower()
                    if expected in t_lower or alias in t_lower:
                        pid = ctypes.c_ulong()
                        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
                        matching_windows.append({"hwnd": hwnd, "title": title, "pid": pid.value})
            return True

        WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
        try:
            user32.EnumWindows(WNDENUMPROC(enum_cb), 0)
        except Exception as e:
            logger.debug(f"EnumWindows error: {e}")

        # Method 1b: Interactive default desktop windows (WinSta0\\Default)
        if not matching_windows:
            try:
                import win32service, win32gui, win32con
                hdesk = win32service.OpenDesktop("default", 0, False, win32con.GENERIC_READ)
                def _dcb(hwnd, _):
                    if win32gui.IsWindowVisible(hwnd):
                        t = win32gui.GetWindowText(hwnd)
                        t_lower = t.lower()
                        if expected in t_lower or alias in t_lower:
                            pid = ctypes.c_ulong()
                            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
                            matching_windows.append({"hwnd": hwnd, "title": t, "pid": pid.value})
                win32gui.EnumDesktopWindows(int(hdesk), _dcb, None)
            except Exception as e_desk:
                logger.debug(f"EnumDesktopWindows notice: {e_desk}")

        if matching_windows:
            return matching_windows[0]

        # Method 2: Process check via psutil
        try:
            target_proc_names = [alias, f"{alias}.exe"]
            if alias in CANONICAL_APP_ALIASES:
                target_proc_names.append(CANONICAL_APP_ALIASES[alias]["exe"].lower())

            for proc in psutil.process_iter(["pid", "name"]):
                try:
                    pname = (proc.info["name"] or "").lower()
                    if any(t in pname for t in target_proc_names):
                        return {"hwnd": None, "title": proc.info["name"], "pid": proc.info["pid"]}
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except Exception:
            pass

        return None

    @classmethod
    def bring_to_front(cls, hwnd: int) -> bool:
        """
        Brings window to foreground using Win32 ShowWindow and SetForegroundWindow.
        """
        if not hwnd:
            return False
        try:
            user32 = ctypes.windll.user32
            # 9 = SW_RESTORE, 1 = SW_SHOWNORMAL
            user32.ShowWindow(hwnd, 9)
            time.sleep(0.1)
            user32.SetForegroundWindow(hwnd)
            time.sleep(0.2)
            return True
        except Exception as e:
            logger.warning(f"Failed to bring window {hwnd} to foreground: {e}")
            return False

    def launch(
        self,
        app_name: str,
        path: Optional[str] = None,
        args: Optional[List[str]] = None,
        reuse_existing: bool = True
    ) -> Dict[str, Any]:
        """
        Launches an application or brings an existing instance to the front.
        - Resolves target via 6-tier lookup.
        - Checks if already running; if so and reuse_existing=True, focuses existing window.
        - Otherwise starts process and verifies window appearance.
        """
        t0 = time.time()
        ensure_desktop_access()

        # 1. Resolve executable or command
        resolved_exe = path or self.resolve_application(app_name)
        if not resolved_exe:
            # Check if app_name is an existing system command that doesn't need path (like 'calc.exe' or 'notepad.exe')
            if app_name.lower().endswith(".exe"):
                resolved_exe = app_name
            else:
                return {
                    "success": False,
                    "status": "not_found",
                    "action": "launch_app",
                    "app_name": app_name,
                    "error": f"Application '{app_name}' was not found on this system. Checked PATH, Registry, Program Files, and Start Menu."
                }

        # 2. Check if instance is already running
        if reuse_existing:
            running = self.find_running_window(app_name)
            if running:
                hwnd = running.get("hwnd")
                if hwnd:
                    self.bring_to_front(hwnd)
                return {
                    "success": True,
                    "status": "already_running",
                    "action": "brought_to_front",
                    "app_name": app_name,
                    "executable": resolved_exe,
                    "window_title": running.get("title"),
                    "hwnd": hwnd,
                    "pid": running.get("pid"),
                    "message": f"Application '{app_name}' is already running. Brought window to front."
                }

        # 3. Launch process
        cmd_args = args or []
        try:
            if app_name.lower() in ["notepad", "notepad.exe"]:
                try:
                    subprocess.Popen("explorer.exe shell:AppsFolder\\Microsoft.WindowsNotepad_8wekyb3d8bbwe!App")
                except Exception:
                    subprocess.Popen([resolved_exe] + cmd_args)
            elif resolved_exe.lower().endswith(".lnk"):
                os.startfile(resolved_exe)
            elif resolved_exe.lower().endswith(".cmd") or resolved_exe.lower().endswith(".bat"):
                subprocess.Popen([resolved_exe] + cmd_args, shell=True)
            else:
                subprocess.Popen([resolved_exe] + cmd_args)

            # Wait briefly and verify window
            time.sleep(1.0)
            expected_title = self.get_expected_title(app_name)
            
            # Poll up to 6 seconds for window to appear
            launched_window = None
            for _ in range(12):
                running = self.find_running_window(app_name)
                if running and running.get("hwnd"):
                    launched_window = running
                    self.bring_to_front(running["hwnd"])
                    break
                time.sleep(0.5)

            duration = round(time.time() - t0, 2)
            return {
                "success": True,
                "status": "launched",
                "action": "launch_app",
                "app_name": app_name,
                "executable": resolved_exe,
                "window_title": launched_window.get("title") if launched_window else expected_title,
                "hwnd": launched_window.get("hwnd") if launched_window else None,
                "pid": launched_window.get("pid") if launched_window else None,
                "duration_s": duration
            }

        except Exception as e:
            logger.error(f"Failed to launch application '{app_name}': {e}")
            return {
                "success": False,
                "status": "failed",
                "action": "launch_app",
                "app_name": app_name,
                "executable": resolved_exe,
                "error": str(e)
            }

    def close(
        self,
        app_name_or_title: str,
        force: bool = False,
        timeout: float = 4.0
    ) -> Dict[str, Any]:
        """
        Gracefully closes an application window.
        Detects confirmation / unsaved-changes dialogs and prevents data loss.
        """
        ensure_desktop_access()
        running = self.find_running_window(app_name_or_title)
        if not running:
            return {
                "success": True,
                "status": "not_running",
                "action": "close_app",
                "app_name": app_name_or_title,
                "message": f"Application '{app_name_or_title}' is not currently running."
            }

        hwnd = running.get("hwnd")
        pid = running.get("pid")

        # 1. If we have a window handle, inspect for unsaved changes or prompt dialogs
        user32 = ctypes.windll.user32
        WM_CLOSE = 0x0010

        if hwnd:
            # Check for modal child dialogs
            modal_dlg = []
            def enum_child_cb(child_hwnd, lparam):
                if user32.IsWindowVisible(child_hwnd):
                    length = user32.GetWindowTextLengthW(child_hwnd)
                    if length > 0:
                        buff = ctypes.create_unicode_buffer(length + 1)
                        user32.GetWindowTextW(child_hwnd, buff, length + 1)
                        t = buff.value.lower()
                        if any(w in t for w in ["save", "confirm", "unsaved", "changes"]):
                            modal_dlg.append((child_hwnd, buff.value))
                return True

            CHILDWNDENUM = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
            try:
                user32.EnumChildWindows(hwnd, CHILDWNDENUM(enum_child_cb), 0)
            except Exception:
                pass

            if modal_dlg and not force:
                return {
                    "success": False,
                    "status": "unsaved_changes",
                    "action": "close_app",
                    "app_name": app_name_or_title,
                    "prompt_user": True,
                    "dialog": modal_dlg[0][1],
                    "error": f"Application '{app_name_or_title}' has unsaved changes or a confirmation dialog ({modal_dlg[0][1]})."
                }

            # Send graceful close message
            user32.PostMessageW(hwnd, WM_CLOSE, 0, 0)

            # Wait and check if window is closed
            t_end = time.time() + timeout
            while time.time() < t_end:
                time.sleep(0.3)
                if not user32.IsWindow(hwnd) or not user32.IsWindowVisible(hwnd):
                    return {
                        "success": True,
                        "status": "closed_gracefully",
                        "action": "close_app",
                        "app_name": app_name_or_title,
                        "window_title": running.get("title")
                    }

        # 2. If still running or no hwnd, check process termination if force=True
        if pid:
            try:
                proc = psutil.Process(pid)
                if proc.is_running():
                    if force:
                        proc.terminate()
                        proc.wait(timeout=2.0)
                        return {
                            "success": True,
                            "status": "terminated_forced",
                            "action": "close_app",
                            "app_name": app_name_or_title,
                            "pid": pid
                        }
                    else:
                        return {
                            "success": False,
                            "status": "close_pending",
                            "action": "close_app",
                            "app_name": app_name_or_title,
                            "error": f"Application '{app_name_or_title}' did not close within {timeout}s. Specify force=True to terminate."
                        }
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                return {
                    "success": True,
                    "status": "closed",
                    "action": "close_app",
                    "app_name": app_name_or_title
                }

        return {
            "success": True,
            "status": "closed",
            "action": "close_app",
            "app_name": app_name_or_title
        }
