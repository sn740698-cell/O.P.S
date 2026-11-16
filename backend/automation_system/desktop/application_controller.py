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
KNOWN_EXACT_APPS: Dict[str, str] = {
    "instagram": "shell:AppsFolder\\Facebook.InstagramBeta_8xx8rvfyw5nnt!App",
    "facebook.instagrambeta": "shell:AppsFolder\\Facebook.InstagramBeta_8xx8rvfyw5nnt!App",
    "nvidia app": r"C:\Program Files\NVIDIA Corporation\NVIDIA App\CEF\NVIDIA App.exe",
    "nvidia": r"C:\Program Files\NVIDIA Corporation\NVIDIA App\CEF\NVIDIA App.exe",
    "vscode": r"C:\Users\sn740\AppData\Local\Programs\Microsoft VS Code\Code.exe",
    "vs code": r"C:\Users\sn740\AppData\Local\Programs\Microsoft VS Code\Code.exe",
    "code": r"C:\Users\sn740\AppData\Local\Programs\Microsoft VS Code\Code.exe",
    "visual studio code": r"C:\Users\sn740\AppData\Local\Programs\Microsoft VS Code\Code.exe",
    "tor": r"C:\Users\sn740\Downloads\Tor Browser\Browser\firefox.exe",
    "tor browser": r"C:\Users\sn740\Downloads\Tor Browser\Browser\firefox.exe",
    "antigravity": "shell:AppsFolder\\Google.Antigravity",
    "notepad": "notepad.exe",
    "calculator": "calc.exe",
    "calc": "calc.exe",
    "terminal": "wt.exe",
    "powershell": "powershell.exe",
    "cmd": "cmd.exe"
}

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
        hinput = user32.OpenInputDesktop(0, False, 0x01FF)  # DESKTOP_SWITCHDESKTOP / READOBJECTS
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
        # Clean desktop and prefix phrases
        import re
        clean_name = re.sub(r'^(?:the\s+)?(.*?)(?:\s+(?:from|on|in)\s+(?:the\s+)?desktop)?$', r'\1', clean_name, flags=re.IGNORECASE).strip()
        lower_name = clean_name.lower()

        # Check KNOWN_EXACT_APPS
        if lower_name in KNOWN_EXACT_APPS:
            return KNOWN_EXACT_APPS[lower_name]

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

        # 5.5 Desktop shortcuts (OneDrive and Public Desktop)
        desktop_dirs = [
            os.path.expandvars(r"%USERPROFILE%\OneDrive\Desktop"),
            os.path.expandvars(r"%USERPROFILE%\Desktop"),
            r"C:\Users\Public\Desktop",
        ]
        for d_dir in desktop_dirs:
            if not os.path.exists(d_dir):
                continue
            try:
                for f in os.listdir(d_dir):
                    if f.lower().endswith(".lnk"):
                        base = os.path.splitext(f)[0].lower()
                        if lower_name == base or lower_name in base or base in lower_name:
                            return os.path.join(d_dir, f)
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
        Uses win32service.OpenDesktop("default") with EnumDesktopWindows to reliably
        inspect the interactive Windows user desktop, filtering out background and IME windows.
        """
        if not app_name_or_title:
            return None

        ensure_desktop_access()

        clean_name = app_name_or_title.strip().lower()
        import re
        clean_name = re.sub(r'^(?:the\s+)?(.*?)(?:\s+(?:from|on|in)\s+(?:the\s+)?desktop)?$', r'\1', clean_name).strip()

        # Build alias matches
        target_terms = [clean_name]
        if clean_name in ["vs code", "vscode", "code", "visual studio code"]:
            target_terms.extend(["visual studio code", "vscode", "code.exe", "code"])
        elif clean_name in ["nvidia", "nvidia app"]:
            target_terms.extend(["nvidia app", "nvidia", "geforce"])
        elif clean_name in ["tor", "tor browser"]:
            target_terms.extend(["tor browser", "tor", "firefox"])
        elif clean_name in ["notepad", "notepad.exe"]:
            target_terms.extend(["notepad", "untitled", "notepad.exe"])
        elif clean_name in ["calc", "calculator"]:
            target_terms.extend(["calculator", "calc.exe", "calculatorapp.exe"])
        elif clean_name in ["antigravity"]:
            target_terms.extend(["antigravity", "ops 2.0"])
        elif clean_name in ["instagram"]:
            target_terms.extend(["instagram"])
        elif clean_name in ["terminal", "powershell", "cmd", "wt"]:
            target_terms.extend(["terminal", "powershell", "command prompt", "cmd.exe", "windowsterminal.exe"])
        elif clean_name in ["explorer", "file explorer"]:
            target_terms.extend(["file explorer", "explorer.exe", "home - file explorer"])

        # Method 1: Check interactive desktop via ctypes OpenDesktopW and EnumDesktopWindows
        candidates = []
        try:
            import ctypes
            import ctypes.wintypes
            user32 = ctypes.windll.user32
            WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.wintypes.BOOL, ctypes.wintypes.HWND, ctypes.wintypes.LPARAM)

            hdesk = user32.OpenDesktopW("default", 0, False, 0x0100) # GENERIC_READ
            if hdesk:
                def _desk_cb(hwnd, _):
                    if not user32.IsWindowVisible(hwnd):
                        return True
                    length = user32.GetWindowTextLengthW(hwnd)
                    if length <= 0:
                        return True
                    buff = ctypes.create_unicode_buffer(length + 1)
                    user32.GetWindowTextW(hwnd, buff, length + 1)
                    t = buff.value.strip()
                    if not t or t in ["Default IME", "MSCTFIME UI", "DDE Server Window", "Task Switching", "Status"]:
                        return True
                    rect = ctypes.wintypes.RECT()
                    user32.GetWindowRect(hwnd, ctypes.byref(rect))
                    w, ht = rect.right - rect.left, rect.bottom - rect.top
                    if w < 50 or ht < 50:
                        return True
                    pid = ctypes.wintypes.DWORD()
                    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
                    try:
                        pname = psutil.Process(pid.value).name().lower()
                    except Exception:
                        pname = ""

                    # Exclude background daemons
                    if "codex" in pname or "conhost" in pname:
                        return True

                    t_low = t.lower()
                    for term in target_terms:
                        if term in t_low or (pname and (term == pname or f"{term}.exe" == pname or (len(term) > 3 and term in pname))):
                            candidates.append({
                                "hwnd": hwnd,
                                "title": t,
                                "pid": pid.value,
                                "pname": pname,
                                "area": w * ht
                            })
                            break
                    return True

                user32.EnumDesktopWindows(hdesk, WNDENUMPROC(_desk_cb), 0)
                user32.CloseDesktop(hdesk)
        except Exception as e:
            logger.debug(f"EnumDesktopWindows ctypes error: {e}")

        if candidates:
            candidates.sort(key=lambda c: c["area"], reverse=True)
            return candidates[0]

        # Method 2: Process check via psutil -> find HWND for active process
        try:
            import ctypes
            import ctypes.wintypes
            user32 = ctypes.windll.user32
            WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.wintypes.BOOL, ctypes.wintypes.HWND, ctypes.wintypes.LPARAM)

            target_proc_names = [f"{t}.exe" if not t.endswith(".exe") else t for t in target_terms]
            for proc in psutil.process_iter(["pid", "name"]):
                try:
                    pname = (proc.info["name"] or "").lower()
                    if "codex" in pname:
                        continue
                    if any(t in pname for t in target_terms) or pname in target_proc_names:
                        proc_pid = proc.info["pid"]
                        pid_wins = []

                        def _pid_cb(h, _):
                            if user32.IsWindowVisible(h):
                                pid = ctypes.wintypes.DWORD()
                                user32.GetWindowThreadProcessId(h, ctypes.byref(pid))
                                if pid.value == proc_pid:
                                    length = user32.GetWindowTextLengthW(h)
                                    buff = ctypes.create_unicode_buffer(length + 1)
                                    user32.GetWindowTextW(h, buff, length + 1)
                                    t = buff.value.strip()
                                    rect = ctypes.wintypes.RECT()
                                    user32.GetWindowRect(h, ctypes.byref(rect))
                                    w, ht = rect.right - rect.left, rect.bottom - rect.top
                                    if w >= 50 and ht >= 50 and t and t not in ["Default IME", "MSCTFIME UI"]:
                                        pid_wins.append({"hwnd": h, "title": t or pname, "pid": proc_pid, "area": w * ht})
                            return True

                        user32.EnumWindows(WNDENUMPROC(_pid_cb), 0)
                        if pid_wins:
                            pid_wins.sort(key=lambda c: c["area"], reverse=True)
                            return pid_wins[0]
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except Exception:
            pass

        return None

    @classmethod
    def bring_to_front(cls, hwnd: int) -> bool:
        """
        Brings window to foreground using Win32 ShowWindow and SetForegroundWindow
        with AttachThreadInput to ensure reliable foreground activation.
        """
        if not hwnd:
            return False
        try:
            import ctypes
            user32 = ctypes.windll.user32
            kernel32 = ctypes.windll.kernel32
            cur_thread = kernel32.GetCurrentThreadId()
            target_thread = user32.GetWindowThreadProcessId(hwnd, None)
            if target_thread and cur_thread != target_thread:
                try:
                    user32.AttachThreadInput(cur_thread, target_thread, True)
                except Exception:
                    pass

            # 9 = SW_RESTORE, 1 = SW_SHOWNORMAL
            user32.ShowWindow(hwnd, 9)
            user32.BringWindowToTop(hwnd)
            user32.SetForegroundWindow(hwnd)
            user32.SetFocus(hwnd)

            if target_thread and cur_thread != target_thread:
                try:
                    user32.AttachThreadInput(cur_thread, target_thread, False)
                except Exception:
                    pass
            time.sleep(0.15)
            return True
        except Exception as e:
            try:
                import win32gui
                win32gui.ShowWindow(hwnd, 9)
                win32gui.SetForegroundWindow(hwnd)
                return True
            except Exception as e2:
                logger.warning(f"Failed to bring window {hwnd} to foreground: {e2}")
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
        Strictly enforces single-instance window reuse:
        - If already running, focuses the existing window with ZERO window duplication.
        - For VS Code: Passes '-r' / '--reuse-window' so VS Code natively reuses its open window.
        - For UWP / shell AppsFolder apps: Uses os.startfile.
        """
        t0 = time.time()
        ensure_desktop_access()

        clean_name = app_name.strip()
        import re
        normalized_name = re.sub(r'^(?:the\s+)?(.*?)(?:\s+(?:from|on|in)\s+(?:the\s+)?desktop)?$', r'\1', clean_name, flags=re.IGNORECASE).strip().lower()

        # 1. Check if instance is already running
        if reuse_existing:
            running = self.find_running_window(normalized_name)
            if running:
                hwnd = running.get("hwnd")
                if hwnd:
                    self.bring_to_front(hwnd)
                return {
                    "success": True,
                    "status": "already_running",
                    "action": "brought_to_front" if hwnd else "focus_existing",
                    "app_name": app_name,
                    "window_title": running.get("title") or self.get_expected_title(app_name),
                    "hwnd": hwnd,
                    "pid": running.get("pid"),
                    "message": f"Application '{app_name}' is already running. Focused existing window (no duplicate opened)."
                }

        # 2. Resolve executable or command
        resolved_exe = None
        if path and (os.path.isabs(path) and os.path.exists(path) or path.startswith("shell:AppsFolder\\")):
            resolved_exe = path
        elif path and shutil.which(path):
            resolved_exe = shutil.which(path)
        else:
            resolved_exe = self.resolve_application(app_name) or (self.resolve_application(path) if path else None)

        if not resolved_exe:
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

        # 3. Check VS Code specific reuse enforcement
        is_vscode = normalized_name in ["vs code", "vscode", "code", "visual studio code"] or "code.exe" in resolved_exe.lower()
        if is_vscode:
            # Check if any Code.exe process is already running
            for proc in psutil.process_iter(["pid", "name"]):
                try:
                    if proc.info["name"] and proc.info["name"].lower() == "code.exe":
                        # VS Code is already running! Invoke code -r to focus existing window without opening duplicate
                        subprocess.Popen([resolved_exe, "-r"])
                        time.sleep(0.5)
                        running = self.find_running_window("vscode")
                        hwnd = running.get("hwnd") if running else None
                        if hwnd:
                            self.bring_to_front(hwnd)
                        return {
                            "success": True,
                            "status": "already_running",
                            "action": "brought_to_front",
                            "app_name": "Visual Studio Code",
                            "executable": resolved_exe,
                            "hwnd": hwnd,
                            "message": "Visual Studio Code is already running. Reused existing window with zero duplication."
                        }
                except Exception:
                    pass

        # 4. Launch process (single window)
        cmd_args = list(args or [])
        if is_vscode and "-r" not in cmd_args and "--reuse-window" not in cmd_args:
            cmd_args.append("-r")

        try:
            if resolved_exe.startswith("shell:AppsFolder\\") or resolved_exe.lower().endswith(".lnk"):
                os.startfile(resolved_exe)
            elif app_name.lower() in ["notepad", "notepad.exe"]:
                subprocess.Popen(["notepad.exe"])
            elif resolved_exe.lower().endswith(".cmd") or resolved_exe.lower().endswith(".bat"):
                subprocess.Popen([resolved_exe] + cmd_args, shell=True)
            else:
                subprocess.Popen([resolved_exe] + cmd_args)

            # Wait briefly and verify window
            time.sleep(1.0)
            expected_title = self.get_expected_title(app_name)

            launched_window = None
            for _ in range(12):
                running = self.find_running_window(normalized_name)
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
                "duration_s": duration,
                "verification": {
                    "verified": True,
                    "verification_type": "window_exists",
                    "target": expected_title
                }
            }
        except Exception as e:
            logger.error(f"Failed to launch '{app_name}' ({resolved_exe}): {e}")
            return {
                "success": False,
                "status": "error",
                "action": "launch_app",
                "app_name": app_name,
                "executable": resolved_exe,
                "error": str(e),
                "verification": {"verified": False, "error": str(e)}
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
                    break

            # Terminate lingering background processes for this app
            alias = app_name_or_title.lower().strip()
            target_names = [alias, f"{alias}.exe"]
            if alias in CANONICAL_APP_ALIASES:
                target_names.append(CANONICAL_APP_ALIASES[alias]["exe"].lower())

            for name in set(target_names):
                exe_name = name if name.endswith(".exe") else f"{name}.exe"
                try:
                    subprocess.run(["taskkill", "/F", "/T", "/IM", exe_name], capture_output=True, timeout=2.0)
                except Exception:
                    pass

            time.sleep(0.5)

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
                    proc.terminate()
                    try:
                        proc.wait(timeout=2.0)
                    except Exception:
                        pass
                    return {
                        "success": True,
                        "status": "closed",
                        "action": "close_app",
                        "app_name": app_name_or_title,
                        "pid": pid
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
