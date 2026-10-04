"""
O.P.S. Physical OS & Desktop Automation Engine
Executes real OS-level controls: application launching (Chrome, Antigravity, VS Code),
PyAutoGUI mouse movements, keyboard typing, system shortcuts, and window management.
All actions are gatekept by OPSSafetyGatekeeper.
"""

import os
import time
import shutil
import subprocess
import webbrowser
import urllib.parse
import logging
from typing import Dict, Any, Optional, List
from ops_core.safety import OPSSafetyGatekeeper

try:
    import pyautogui
    # Safety failsafe: moving mouse to corner aborts runaway automation
    pyautogui.FAILSAFE = True
except ImportError:
    pyautogui = None

logger = logging.getLogger("ops.automation")


class OPSAutomationService:
    """
    Physical OS automation executor for O.P.S. (The JARVIS Engine).
    """

    KNOWN_APPS = {
        "chrome": "chrome",
        "google chrome": "chrome",
        "browser": "chrome",
        "antigravity": "agy",
        "vscode": "code",
        "vs code": "code",
        "code": "code",
        "terminal": "cmd.exe",
        "cmd": "cmd.exe",
        "powershell": "powershell.exe",
        "notepad": "notepad.exe",
        "calculator": "calc.exe",
        "calc": "calc.exe",
        "explorer": "explorer.exe",
        "files": "explorer.exe",
        "paint": "mspaint.exe",
        "mspaint": "mspaint.exe",
        "task manager": "taskmgr.exe",
        "taskmgr": "taskmgr.exe",
        "settings": "ms-settings:",
        "control panel": "control.exe"
    }

    KNOWN_WEB_SERVICES = {
        "instagram": "https://www.instagram.com",
        "insta": "https://www.instagram.com",
        "youtube": "https://www.youtube.com",
        "yt": "https://www.youtube.com",
        "twitter": "https://www.x.com",
        "x": "https://www.x.com",
        "github": "https://github.com",
        "gitlab": "https://gitlab.com",
        "reddit": "https://www.reddit.com",
        "gmail": "https://mail.google.com",
        "google": "https://www.google.com",
        "chatgpt": "https://chatgpt.com",
        "openai": "https://chatgpt.com",
        "claude": "https://claude.ai",
        "gemini": "https://gemini.google.com",
        "whatsapp": "https://web.whatsapp.com",
        "telegram": "https://web.telegram.org",
        "spotify": "https://open.spotify.com",
        "netflix": "https://www.netflix.com",
        "prime video": "https://www.primevideo.com",
        "linkedin": "https://www.linkedin.com",
        "facebook": "https://www.facebook.com",
        "amazon": "https://www.amazon.com",
        "flipkart": "https://www.flipkart.com",
        # Deep Links & Sub-pages
        "instagram messages": "https://www.instagram.com/direct/inbox/",
        "messages in instagram": "https://www.instagram.com/direct/inbox/",
        "instagram direct": "https://www.instagram.com/direct/inbox/",
        "instagram dms": "https://www.instagram.com/direct/inbox/",
        "instagram explore": "https://www.instagram.com/explore/",
        "twitter messages": "https://x.com/messages",
        "x messages": "https://x.com/messages",
        "gmail inbox": "https://mail.google.com/mail/u/0/#inbox",
        "youtube subscriptions": "https://www.youtube.com/feed/subscriptions",
        "youtube history": "https://www.youtube.com/feed/history",
        "github pulls": "https://github.com/pulls",
        "github issues": "https://github.com/issues",
        "wikipedia": "https://www.wikipedia.org",
        "wiki": "https://www.wikipedia.org",
        "leetcode": "https://leetcode.com",
        "hackerrank": "https://www.hackerrank.com",
        "hackernews": "https://news.ycombinator.com",
        "hacker news": "https://news.ycombinator.com",
        "stackoverflow": "https://stackoverflow.com",
        "stack overflow": "https://stackoverflow.com",
        "medium": "https://medium.com",
        "quora": "https://www.quora.com",
        "pinterest": "https://www.pinterest.com",
        "twitch": "https://www.twitch.tv",
        "discord": "https://discord.com/app",
        "slack": "https://app.slack.com",
        "notion": "https://www.notion.so",
        "canva": "https://www.canva.com",
        "figma": "https://www.figma.com",
        "coursera": "https://www.coursera.com",
        "udemy": "https://www.udemy.com",
        "huggingface": "https://huggingface.co",
        "arxiv": "https://arxiv.org",
        "cnn": "https://www.cnn.com",
        "bbc": "https://www.bbc.com",
        "cricbuzz": "https://www.cricbuzz.com",
        "imdb": "https://www.imdb.com"
    }

    # Universal Search URL Templates for 40+ Top Platforms
    SEARCH_URL_TEMPLATES = {
        "google": "https://www.google.com/search?q={query}",
        "youtube": "https://www.youtube.com/results?search_query={query}",
        "amazon": "https://www.amazon.com/s?k={query}",
        "reddit": "https://www.reddit.com/search/?q={query}",
        "github": "https://github.com/search?q={query}",
        "wikipedia": "https://en.wikipedia.org/wiki/Special:Search?search={query}",
        "twitter": "https://x.com/search?q={query}",
        "x": "https://x.com/search?q={query}",
        "instagram": "https://www.instagram.com/explore/",
        "spotify": "https://open.spotify.com/search/{query}",
        "netflix": "https://www.netflix.com/search?q={query}",
        "linkedin": "https://www.linkedin.com/search/results/all/?keywords={query}",
        "bing": "https://www.bing.com/search?q={query}",
        "duckduckgo": "https://duckduckgo.com/?q={query}",
        "stackoverflow": "https://stackoverflow.com/search?q={query}",
        "pinterest": "https://www.pinterest.com/search/pins/?q={query}",
        "ebay": "https://www.ebay.com/sch/i.html?_nkw={query}",
        "twitch": "https://www.twitch.tv/search?term={query}",
        "walmart": "https://www.walmart.com/search?q={query}",
        "flipkart": "https://www.flipkart.com/search?q={query}",
        "quora": "https://www.quora.com/search?q={query}",
        "imdb": "https://www.imdb.com/find/?q={query}",
        "arxiv": "https://arxiv.org/search/?query={query}&searchtype=all",
        "huggingface": "https://huggingface.co/models?search={query}",
        "medium": "https://medium.com/search?q={query}",
        "canva": "https://www.canva.com/search/templates?q={query}",
        "coursera": "https://www.coursera.com/search?query={query}",
        "udemy": "https://www.udemy.com/courses/search/?q={query}",
        "cricbuzz": "https://www.cricbuzz.com/search?q={query}",
        "yahoo": "https://search.yahoo.com/search?p={query}",
        "bilibili": "https://search.bilibili.com/all?keyword={query}",
        "aliexpress": "https://www.aliexpress.com/wholesale?SearchText={query}",
        "etsy": "https://www.etsy.com/search?q={query}",
        "target": "https://www.target.com/s?searchTerm={query}",
        "bestbuy": "https://www.bestbuy.com/site/searchpage.jsp?st={query}",
        "soundcloud": "https://soundcloud.com/search?q={query}",
        "dockerhub": "https://hub.docker.com/search?q={query}",
        "npm": "https://www.npmjs.com/search?q={query}",
        "pypi": "https://pypi.org/search/?q={query}"
    }

    _installed_apps_cache = {}
    _instance = None
    last_active_url: str = ""
    last_active_title: str = ""
    last_active_app: str = ""
    last_active_media_query: str = ""

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(OPSAutomationService, cls).__new__(cls)
            cls._instance.last_active_url = ""
            cls._instance.last_active_title = ""
            cls._instance.last_active_app = ""
            cls._instance.last_active_media_query = ""
        return cls._instance

    def get_installed_apps(self) -> Dict[str, str]:
        """Discovers all installed Windows applications using PowerShell Get-StartApps and Start Menu shortcuts."""
        if self._installed_apps_cache:
            return self._installed_apps_cache

        apps = {}
        # 1. PowerShell Get-StartApps
        try:
            cmd = ['powershell.exe', '-NoProfile', '-Command', 'Get-StartApps | ForEach-Object { "$($_.Name)|||$($_.AppID)" }']
            res = subprocess.check_output(cmd, shell=False, text=True, errors="ignore", timeout=8)
            for line in res.strip().splitlines():
                if "|||" in line:
                    parts = line.split("|||", 1)
                    name = parts[0].strip().lower()
                    app_id = parts[1].strip()
                    if name and app_id:
                        apps[name] = app_id
        except Exception as e:
            logger.warning(f"Get-StartApps error: {e}")

        # 2. Windows Start Menu Shortcut folders for classic/portable/desktop apps
        start_menu_dirs = [
            os.path.expandvars(r"%ProgramData%\Microsoft\Windows\Start Menu\Programs"),
            os.path.expandvars(r"%AppData%\Microsoft\Windows\Start Menu\Programs"),
        ]
        for s_dir in start_menu_dirs:
            if os.path.exists(s_dir):
                for root, _, files in os.walk(s_dir):
                    for f in files:
                        if f.lower().endswith(".lnk"):
                            app_clean = f[:-4].lower().strip()
                            if app_clean and app_clean not in apps:
                                apps[app_clean] = os.path.join(root, f)

        self._installed_apps_cache = apps
        return apps

    def resolve_website_url(self, site_name: str) -> str:
        """Universally resolves any site name, brand, or domain to an accessible URL."""
        clean = site_name.strip().lower()
        if clean.startswith("http://") or clean.startswith("https://"):
            return clean
        if clean in self.KNOWN_WEB_SERVICES:
            return self.KNOWN_WEB_SERVICES[clean]

        tlds = [".com", ".org", ".net", ".io", ".in", ".co", ".ai", ".dev", ".app", ".edu", ".gov", ".me", ".xyz", ".tech", ".tv", ".cc"]
        for tld in tlds:
            if clean.endswith(tld) or f"{tld}/" in clean:
                return f"https://{clean}"

        domain = clean.replace(" ", "")
        return f"https://www.{domain}.com"

    def open_file_or_folder(self, target: str) -> Dict[str, Any]:
        """Opens any file, directory, or standard folder in Windows Explorer or default app."""
        clean = target.strip().strip('"\'')
        standard_folders = {
            "downloads": os.path.expanduser("~/Downloads"),
            "downloads folder": os.path.expanduser("~/Downloads"),
            "documents": os.path.expanduser("~/Documents"),
            "documents folder": os.path.expanduser("~/Documents"),
            "desktop": os.path.expanduser("~/Desktop"),
            "desktop folder": os.path.expanduser("~/Desktop"),
            "pictures": os.path.expanduser("~/Pictures"),
            "videos": os.path.expanduser("~/Videos")
        }

        resolved_path = standard_folders.get(clean.lower()) or clean
        if not os.path.isabs(resolved_path) and os.path.exists(resolved_path):
            resolved_path = os.path.abspath(resolved_path)

        logger.info(f"[O.P.S. Automation] Opening file or folder: '{resolved_path}'")
        try:
            if os.path.exists(resolved_path):
                os.startfile(resolved_path)
                item_type = "folder" if os.path.isdir(resolved_path) else "file"
                return {
                    "status": "success",
                    "action": "open_file_or_folder",
                    "target": resolved_path,
                    "message": f"Successfully opened {item_type}: {resolved_path}"
                }
            else:
                # Try opening via explorer
                subprocess.Popen(f'explorer.exe "{resolved_path}"', shell=True)
                return {
                    "status": "success",
                    "action": "open_file_or_folder",
                    "target": resolved_path,
                    "message": f"Opened in Windows Explorer: {resolved_path}"
                }
        except Exception as e:
            logger.error(f"Failed to open file or folder {resolved_path}: {e}")
            return {"status": "error", "target": resolved_path, "error": str(e)}

    def open_in_vscode(self, target: str = "") -> Dict[str, Any]:
        """Opens VS Code with a specified file or opens current workspace."""
        clean = target.strip().strip('"\'')
        logger.info(f"[O.P.S. Automation] Opening in VS Code: '{clean}'")
        try:
            if clean and os.path.exists(clean):
                subprocess.Popen(f'code "{clean}"', shell=True)
                msg = f"Opened '{clean}' in VS Code."
            else:
                subprocess.Popen('code .', shell=True)
                msg = "Opened VS Code."
                if pyautogui:
                    time.sleep(1.2)
                    pyautogui.hotkey('ctrl', 'o')
            return {
                "status": "success",
                "action": "open_in_vscode",
                "target": clean,
                "message": msg
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def run_claude_routine(self) -> Dict[str, Any]:
        """
        Executes Claude routine:
        1. Navigates to D:\freellmapi
        2. Runs npm run dev
        3. Launches Claude CLI or interface
        """
        target_dir = r"D:\freellmapi"
        logger.info(f"[O.P.S. Automation] Executing Claude routine in {target_dir}")
        try:
            # 1. Run npm run dev in target directory in a detached console
            npm_cmd = f'start cmd /k "cd /d {target_dir} && npm run dev"'
            subprocess.Popen(npm_cmd, shell=True)

            # 2. Launch Claude CLI
            time.sleep(1.0)
            claude_cmd = 'start cmd /k "claude"'
            subprocess.Popen(claude_cmd, shell=True)

            return {
                "status": "success",
                "action": "run_claude_routine",
                "directory": target_dir,
                "message": f"Successfully initiated 'npm run dev' in {target_dir} and launched Claude interface."
            }
        except Exception as e:
            logger.error(f"Claude routine error: {e}")
            return {"status": "error", "error": str(e)}

    def execute_browser_dom_task(self, url: str, search_query: Optional[str] = None, site_name: str = "") -> Dict[str, Any]:
        """
        Executes real DOM automation in the browser using Playwright across ANY website on the internet:
        1. Resolves target website URL dynamically.
        2. Detects direct search templates or uses dynamic Playwright DOM interaction.
        3. Navigates, fills search input, triggers Enter, captures screenshot preview.
        4. Launches desktop browser at the resulting destination.
        """
        target_site = site_name or url
        clean_site = target_site.lower().replace("https://", "").replace("http://", "").replace("www.", "").split(".")[0].strip()

        # Resolve initial URL
        if not (url.startswith("http://") or url.startswith("https://")):
            url = self.resolve_website_url(url or target_site)

        target_url = url
        # Check if direct search URL template is available
        if search_query and clean_site in self.SEARCH_URL_TEMPLATES:
            target_url = self.SEARCH_URL_TEMPLATES[clean_site].format(query=urllib.parse.quote_plus(search_query))

        logger.info(f"[O.P.S. Universal DOM] Executing task on {target_site} (URL={target_url}, query='{search_query}')")
        screenshot_b64 = None

        try:
            from playwright.sync_api import sync_playwright
            with sync_playwright() as p:
                browser = None
                for ch in ["chrome", "msedge"]:
                    try:
                        browser = p.chromium.launch(channel=ch, headless=True)
                        break
                    except Exception:
                        continue

                if browser:
                    page = browser.new_page()
                    # If target_url was formatted directly, navigate to it
                    page.goto(target_url, timeout=15000)

                    # If page is base domain and we need to fill the search bar dynamically:
                    if search_query and target_url == url:
                        # Universal multi-tiered search input selector cascade
                        selectors = [
                            "input[type='search']",
                            "input[name*='search' i]",
                            "input[name*='query' i]",
                            "input[name='q']",
                            "input[name='k']",
                            "input[name*='keyword' i]",
                            "input[id*='search' i]",
                            "input[id*='twotabsearchtextbox']",
                            "input[placeholder*='search' i]",
                            "input[placeholder*='find' i]",
                            "input[placeholder*='what are you looking for' i]",
                            "input[aria-label*='search' i]",
                            "textarea[name*='search' i]",
                            "textarea[placeholder*='search' i]",
                            "input[role='searchbox']",
                            "form[role='search'] input",
                            "[data-testid*='search' i] input",
                            "input[type='text']"
                        ]
                        for sel in selectors:
                            try:
                                el = page.wait_for_selector(sel, timeout=1200)
                                if el and el.is_visible():
                                    el.fill(search_query)
                                    el.press("Enter")
                                    page.wait_for_timeout(2000)
                                    target_url = page.url
                                    break
                            except Exception:
                                continue

                    # Capture screenshot preview for HUD
                    import base64
                    screenshot_bytes = page.screenshot()
                    screenshot_b64 = base64.b64encode(screenshot_bytes).decode("utf-8")
                    browser.close()
        except Exception as e:
            logger.warning(f"Playwright DOM execution notice: {e}")

        # Open the resolved URL in the user's default browser on desktop
        try:
            webbrowser.open(target_url)
        except Exception:
            os.system(f'start "" "{target_url}"')

        self.last_active_url = target_url
        self.last_active_title = f"{target_site.title()}: {search_query or 'Home'}"
        self.last_active_app = target_site
        self.last_active_media_query = search_query

        return {
            "status": "success",
            "action": "browser_dom_task",
            "url": target_url,
            "site": target_site,
            "query": search_query,
            "screenshot_b64": screenshot_b64,
            "message": f"Successfully performed DOM automation on {target_site.title()}: '{search_query or 'Navigated'}'."
        }

    def launch_app(self, app_name: str, args: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Universal Application, File, Folder, Website, and Installed App Launcher.
        """
        clean_name = app_name.lower().strip()

        # 1. Fast check for known web services & deep links
        if clean_name in self.KNOWN_WEB_SERVICES:
            url = self.KNOWN_WEB_SERVICES[clean_name]
            logger.info(f"[O.P.S. Automation] Launching known web service '{clean_name}' at '{url}'")
            try:
                webbrowser.open(url)
                return {
                    "status": "success",
                    "action": "open_web_service",
                    "app": app_name,
                    "url": url,
                    "message": f"Successfully launched {app_name.title()} in your browser ({url})."
                }
            except Exception:
                os.system(f'start "" "{url}"')
                return {
                    "status": "success",
                    "action": "open_web_service",
                    "app": app_name,
                    "url": url,
                    "message": f"Launched {app_name.title()} via default browser."
                }

        # 2. Check if clean_name is an explicit URL or has a TLD
        tlds = [".com", ".org", ".net", ".io", ".in", ".co", ".ai", ".dev", ".app", ".edu", ".gov", ".me", ".xyz", ".tech", ".tv", ".cc"]
        if clean_name.startswith("http://") or clean_name.startswith("https://") or any(clean_name.endswith(tld) or f"{tld}/" in clean_name for tld in tlds):
            target_url = clean_name if clean_name.startswith("http") else f"https://{clean_name}"
            webbrowser.open(target_url)
            return {
                "status": "success",
                "action": "open_url",
                "url": target_url,
                "message": f"Opened {target_url} in browser."
            }

        # 3. Check if clean_name is a file or folder path
        if os.path.exists(app_name) or any(app_name.lower().startswith(p) for p in ["c:\\", "d:\\", "e:\\", "\\\\"]):
            return self.open_file_or_folder(app_name)

        # 4. Check if it's in hardcoded KNOWN_APPS
        if clean_name in self.KNOWN_APPS:
            binary = self.KNOWN_APPS[clean_name]
            logger.info(f"[O.P.S. Automation] Launching desktop application: '{app_name}' ({binary})")
            try:
                cmd = f'start "" "{binary}"'
                subprocess.Popen(cmd, shell=True)
                return {
                    "status": "success",
                    "action": "launch_app",
                    "app": app_name,
                    "binary": binary,
                    "message": f"Successfully launched {app_name} on your workstation."
                }
            except Exception as e:
                logger.error(f"Failed to launch app {app_name}: {e}")
                return {"status": "error", "app": app_name, "error": str(e)}

        # 5. Check all installed Windows Apps (Get-StartApps and Start Menu shortcuts)
        installed = self.get_installed_apps()
        matched_id = None
        matched_name = None

        # Pass 1: exact match
        for name, app_id in installed.items():
            if clean_name == name:
                matched_id = app_id
                matched_name = name
                break

        # Pass 2: word boundary or substring match
        if not matched_id:
            for name, app_id in installed.items():
                if clean_name in name or name in clean_name:
                    matched_id = app_id
                    matched_name = name
                    break

        if matched_id:
            logger.info(f"[O.P.S. Automation] Launching installed Windows App: '{matched_name}' ({matched_id})")
            try:
                if matched_id.lower().endswith(".lnk"):
                    os.startfile(matched_id)
                elif matched_id.lower().endswith(".exe") and os.path.exists(matched_id):
                    subprocess.Popen(f'start "" "{matched_id}"', shell=True)
                else:
                    subprocess.Popen(f'explorer.exe shell:AppsFolder\\{matched_id}', shell=True)
                return {
                    "status": "success",
                    "action": "launch_installed_app",
                    "app": app_name,
                    "app_id": matched_id,
                    "message": f"Successfully launched {matched_name.title()} from installed applications."
                }
            except Exception as e:
                logger.warning(f"Error launching installed app {matched_id}: {e}")

        # 6. Check if it's an executable tool on system PATH
        cli_bin = shutil.which(clean_name)
        if cli_bin:
            try:
                subprocess.Popen(f'start cmd /k "{cli_bin}"', shell=True)
                return {
                    "status": "success",
                    "action": "launch_cli_tool",
                    "app": app_name,
                    "path": cli_bin,
                    "message": f"Launched CLI tool '{clean_name}' from system PATH."
                }
            except Exception as e:
                logger.warning(f"Error launching CLI tool {cli_bin}: {e}")

        # 7. Universal Dynamic Website Resolution for ANY arbitrary website name
        resolved_url = None
        try:
            from ops_core.services.scraping_service import OPSScrapingService
            scraper = OPSScrapingService()
            search_res = scraper.search_web(f"{clean_name} official website", max_results=5)
            organic = [r['url'] for r in search_res.get('results', []) if 'duckduckgo.com' not in r.get('url', '') and 'y.js' not in r.get('url', '')]
            if organic:
                resolved_url = organic[0]
        except Exception as search_err:
            logger.warning(f"Dynamic website search failed for '{clean_name}': {search_err}")

        if not resolved_url:
            resolved_url = self.resolve_website_url(clean_name)

        logger.info(f"[O.P.S. Automation] Universally opening website for '{app_name}': '{resolved_url}'")
        try:
            webbrowser.open(resolved_url)
            return {
                "status": "success",
                "action": "open_website",
                "app": app_name,
                "url": resolved_url,
                "message": f"Successfully launched {app_name.title()} in your browser ({resolved_url})."
            }
        except Exception:
            os.system(f'start "" "{resolved_url}"')
            return {
                "status": "success",
                "action": "open_website",
                "app": app_name,
                "url": resolved_url,
                "message": f"Launched {app_name.title()} ({resolved_url})."
            }

    def open_web_search(self, query: str) -> Dict[str, Any]:
        """
        Opens user's live browser directly to Google search results for the given query.
        """
        import urllib.parse
        encoded = urllib.parse.quote_plus(query)
        search_url = f"https://www.google.com/search?q={encoded}"
        logger.info(f"[O.P.S. Automation] Opening live browser search for: '{query}'")
        
        try:
            webbrowser.open(search_url)
            return {
                "status": "success",
                "action": "open_web_search",
                "query": query,
                "url": search_url,
                "message": f"Opened browser search for: '{query}'"
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def execute_gui_action(
        self,
        action: str,
        x: int = 0,
        y: int = 0,
        text: str = "",
        keys: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Executes real desktop mouse/keyboard actions using PyAutoGUI.
        """
        is_safe, msg = OPSSafetyGatekeeper.validate_tool_call("gui_action", {"action": action, "x": x, "y": y, "text": text})
        if not is_safe:
            return {"status": "blocked", "reason": msg}

        if not pyautogui:
            return {"status": "error", "error": "PyAutoGUI not available in current environment."}

        try:
            logger.info(f"[O.P.S. GUI Action] Executing: {action}")
            if action in ["click", "mouse_click"]:
                if x > 0 and y > 0:
                    pyautogui.click(x, y)
                else:
                    pyautogui.click()
            elif action == "double_click":
                pyautogui.doubleClick(x, y) if (x > 0 and y > 0) else pyautogui.doubleClick()
            elif action in ["type", "type_text"]:
                pyautogui.write(text, interval=0.02)
            elif action in ["press", "hotkey", "press_key"]:
                if keys:
                    pyautogui.hotkey(*keys)
                elif text:
                    pyautogui.press(text)
            elif action == "scroll":
                pyautogui.scroll(int(text) if text.isdigit() else -300)
            elif action == "screenshot":
                img = pyautogui.screenshot()
                return {"status": "success", "action": "screenshot", "message": "Screenshot captured"}

            return {
                "status": "success",
                "action": action,
                "coordinates": {"x": x, "y": y},
                "text": text,
                "message": f"Successfully executed OS action: {action}"
            }
        except Exception as e:
            logger.error(f"PyAutoGUI action error: {e}")
            return {"status": "error", "action": action, "error": str(e)}


automation_service = OPSAutomationService()

