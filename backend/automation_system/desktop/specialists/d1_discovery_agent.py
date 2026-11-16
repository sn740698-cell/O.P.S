"""
O.P.S. 2.0 Desktop Automation Specialist — Agent D1: Application Discovery Specialist
Responsibilities:
- Discover applications actually installed on the user's Windows computer
- Inspect Start Menu shortcuts, Windows App Paths registry, Microsoft Store / WindowsApps, Program Files, and PATH
- Support URI launch mechanisms (e.g. spotify:, whatsapp:, calculator:, etc.)
- Accurately determine whether an application is installed vs. unavailable
- Distinguish between opening an installed desktop application vs opening a website
- If desktop app is not installed (e.g. Instagram, Snapchat), report limitation accurately and offer web alternative
"""

import os
import sys
import shutil
import winreg
import logging
from typing import Dict, Any, Optional, Tuple, List

from automation_system.desktop.application_controller import ApplicationController, CANONICAL_APP_ALIASES

logger = logging.getLogger("OPS.Desktop.D1_DiscoveryAgent")

# Well-known web equivalents for popular desktop services
WEB_EQUIVALENTS: Dict[str, str] = {
    "instagram": "https://www.instagram.com",
    "snapchat": "https://www.snapchat.com",
    "whatsapp": "https://web.whatsapp.com",
    "chatgpt": "https://chatgpt.com",
    "spotify": "https://open.spotify.com",
    "claude": "https://claude.ai",
    "gemini": "https://gemini.google.com",
    "slack": "https://slack.com",
    "discord": "https://discord.com",
    "notion": "https://www.notion.so",
    "github": "https://github.com",
}

# Known Windows URI launch schemes
KNOWN_APP_URIS: Dict[str, str] = {
    "calculator": "calculator:",
    "calc": "calculator:",
    "spotify": "spotify:",
    "whatsapp": "whatsapp:",
    "paint": "ms-paint:",
    "mspaint": "ms-paint:",
    "settings": "ms-settings:",
}


class D1_DiscoveryAgent:
    """Specialist Agent D1: Discovers and verifies installed native desktop applications."""

    def __init__(self):
        self.agent_id = "agent_d1_discovery"
        self.agent_name = "Application Discovery Specialist"
        self._app_cache: Dict[str, Optional[str]] = {}

    def discover_application(self, app_name: str) -> Dict[str, Any]:
        """
        Discovers whether an application is installed on this system.
        Returns:
            {
                "installed": bool,
                "app_name": str,
                "resolved_path": Optional[str],
                "launch_type": "executable" | "uri" | "shortcut" | "not_installed",
                "web_alternative_url": Optional[str],
                "message": str
            }
        """
        if not app_name or not app_name.strip():
            return {
                "installed": False,
                "app_name": app_name,
                "resolved_path": None,
                "launch_type": "not_installed",
                "web_alternative_url": None,
                "message": "Empty application name provided."
            }

        clean = app_name.strip().strip('"\'')
        lower = clean.lower()

        # 1. Resolve via ApplicationController multi-tier lookup
        resolved_path = ApplicationController.resolve_application(clean)

        # 2. Check known URI launch capability if path not found
        uri_scheme = None
        if not resolved_path:
            uri_scheme = KNOWN_APP_URIS.get(lower)

        # 3. Check WindowsApps Microsoft Store packages explicitly
        if not resolved_path:
            local_appdata = os.environ.get("LOCALAPPDATA", "")
            windows_apps = os.path.join(local_appdata, "Microsoft", "WindowsApps")
            if os.path.exists(windows_apps):
                try:
                    for f in os.listdir(windows_apps):
                        if lower in f.lower() and f.lower().endswith(".exe"):
                            resolved_path = os.path.join(windows_apps, f)
                            break
                except Exception:
                    pass

        # 4. Check Start Menu shortcuts for partial matches
        if not resolved_path:
            resolved_path = self._scan_start_menu(lower)

        # 5. Check Registry Uninstall Keys for installed applications
        if not resolved_path:
            resolved_path = self._check_uninstall_registry(lower)

        web_alt = WEB_EQUIVALENTS.get(lower)

        if resolved_path or uri_scheme:
            return {
                "installed": True,
                "app_name": clean,
                "resolved_path": resolved_path,
                "launch_type": "executable" if resolved_path else "uri",
                "uri_scheme": uri_scheme,
                "web_alternative_url": web_alt,
                "message": f"Application '{clean}' is installed at: {resolved_path or uri_scheme}"
            }
        else:
            msg = f"Application '{clean}' is not installed on this computer."
            if web_alt:
                msg += f" However, its official web application is available at: {web_alt}. Would you like to open it in your browser instead?"
            return {
                "installed": False,
                "app_name": clean,
                "resolved_path": None,
                "launch_type": "not_installed",
                "web_alternative_url": web_alt,
                "message": msg
            }

    def _scan_start_menu(self, app_lower: str) -> Optional[str]:
        """Scans Start Menu folders for exact or partial shortcut match."""
        start_menu_dirs = [
            os.path.expandvars(r"%APPDATA%\Microsoft\Windows\Start Menu\Programs"),
            os.path.expandvars(r"%ProgramData%\Microsoft\Windows\Start Menu\Programs"),
        ]
        for base in start_menu_dirs:
            if not os.path.exists(base):
                continue
            try:
                for root, _, files in os.walk(base):
                    for f in files:
                        if f.lower().endswith(".lnk") and app_lower in f.lower():
                            return os.path.join(root, f)
            except Exception:
                continue
        return None

    def _check_uninstall_registry(self, app_lower: str) -> Optional[str]:
        """Inspects Windows Uninstall registry keys to locate application install paths."""
        keys = [
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
            (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
        ]
        for root, sub in keys:
            try:
                with winreg.OpenKey(root, sub) as key:
                    count, _, _ = winreg.QueryInfoKey(key)
                    for i in range(count):
                        try:
                            sub_name = winreg.EnumKey(key, i)
                            with winreg.OpenKey(key, sub_name) as subk:
                                disp, _ = winreg.QueryValueEx(subk, "DisplayName")
                                if disp and app_lower in disp.lower():
                                    try:
                                        loc, _ = winreg.QueryValueEx(subk, "InstallLocation")
                                        if loc and os.path.exists(loc):
                                            return loc
                                    except OSError:
                                        pass
                        except OSError:
                            continue
            except OSError:
                continue
        return None
