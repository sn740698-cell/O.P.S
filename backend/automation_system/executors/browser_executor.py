"""
O.P.S. 2.0 Browser Automation Executor
Technology: Playwright (Chromium Headed/Visible Engine via BrowserSessionManager)
Provides unified execution of web tasks with:
- Persistent browser contexts and shared tab management across conversation turns
- Robust accessible locators, auto-waits, and condition-based waiting
- Full website adapters: Google, YouTube, Spotify, Instagram, and general websites
- Verification of actual DOM state and observable outcomes
- Authentication barrier awareness and honest limitation reporting
"""

import os
import time
import logging
from typing import Dict, Any, List, Optional
from automation_system.browser.browser_manager import BrowserSessionManager
from automation_system.browser.navigation_engine import NavigationEngine
from automation_system.browser.interaction_engine import InteractionEngine
from automation_system.browser.search_engine import SearchEngine
from automation_system.browser.verification_engine import BrowserVerificationEngine
from automation_system.browser.page_inspector import PageInspector
from automation_system.browser.auth_manager import AuthenticationManager
from automation_system.browser.recovery_manager import RecoveryManager
from automation_system.browser.adapters.google_adapter import GoogleAdapter
from automation_system.browser.adapters.youtube_adapter import YouTubeAdapter
from automation_system.browser.adapters.spotify_adapter import SpotifyAdapter
from automation_system.browser.adapters.instagram_adapter import InstagramAdapter
from automation_system.verification.verifier import AutomationVerifier

logger = logging.getLogger("OPS.BrowserExecutor")


class BrowserExecutor:
    """
    High-level facade for executing browser automation directives
    using the persistent O.P.S. Browser Automation Core Library.
    """

    def __init__(self, headless: Optional[bool] = None, conversation_id: str = "default_session"):
        self.conversation_id = conversation_id or "default_session"
        self._session_mgr = BrowserSessionManager()
        self.headless = headless

    def _execute(self, fn, timeout: float = 45.0, target_url: Optional[str] = None) -> Dict[str, Any]:
        """Runs a callable taking `page` inside the Playwright worker thread with multi-tab awareness."""
        try:
            return self._session_mgr.execute_on_page(self.conversation_id, fn, timeout=timeout, target_url=target_url)
        except Exception as e:
            logger.error(f"Browser action exception: {e}")
            return {"success": False, "error": str(e)}

    # -------------------------------------------------------------------------
    # Core Navigation & Inspection
    # -------------------------------------------------------------------------

    def navigate(self, url: str) -> Dict[str, Any]:
        """Navigates to URL and verifies state."""
        def _nav(page):
            res = NavigationEngine.navigate(page, url=url)
            if res.get("success", False):
                res["verification"] = BrowserVerificationEngine.verify_page_state(page)
            return res
        return self._execute(_nav, target_url=url)

    def go_back(self) -> Dict[str, Any]:
        """Navigates back in browser history."""
        return self._execute(lambda p: NavigationEngine.go_back(p))

    def go_forward(self) -> Dict[str, Any]:
        """Navigates forward in browser history."""
        return self._execute(lambda p: NavigationEngine.go_forward(p))

    def reload(self) -> Dict[str, Any]:
        """Reloads current page."""
        return self._execute(lambda p: NavigationEngine.reload(p))

    def inspect_page(self) -> Dict[str, Any]:
        """Extracts structured summary of active page."""
        return self._execute(lambda p: PageInspector.inspect(p))

    # -------------------------------------------------------------------------
    # Element Interaction
    # -------------------------------------------------------------------------

    def click(
        self,
        selector: Optional[str] = None,
        name: Optional[str] = None,
        role: Optional[str] = None
    ) -> Dict[str, Any]:
        """Clicks element by accessible role, text, or selector."""
        return self._execute(lambda p: InteractionEngine.click(p, selector=selector, name=name, role=role))

    def click_first_result(self) -> Dict[str, Any]:
        """Clicks first organic search result."""
        return self._execute(lambda p: InteractionEngine.click_first_result(p))

    def search(self, query: str, selector: Optional[str] = None) -> Dict[str, Any]:
        """Executes search on active page."""
        return self._execute(lambda p: SearchEngine.execute_search(p, query=query, custom_selector=selector))

    def fill_form(
        self,
        selector_or_label: str,
        text: str,
        is_secret: bool = False
    ) -> Dict[str, Any]:
        """Enters text into form input with accessible locator fallbacks."""
        return self._execute(lambda p: InteractionEngine.fill_form(
            p, selector_or_label=selector_or_label, text=text, is_secret=is_secret
        ))

    def capture_screenshot(self, output_path: Optional[str] = None) -> Dict[str, Any]:
        """Captures verification screenshot."""
        def _shot(page):
            path = output_path or os.path.join(os.path.expanduser("~"), f"ops_screenshot_{int(time.time())}.png")
            page.screenshot(path=path)
            return {
                "success": os.path.exists(path),
                "action": "capture_screenshot",
                "screenshot_path": path,
                "verification": {"verified": os.path.exists(path)}
            }
        return self._execute(_shot)

    # -------------------------------------------------------------------------
    # Specialized Adapters
    # -------------------------------------------------------------------------

    # Google
    def google_search(self, query: str) -> Dict[str, Any]:
        return self._execute(lambda p: GoogleAdapter.search(p, query=query), target_url="https://www.google.com")

    def google_click_top(self) -> Dict[str, Any]:
        return self._execute(lambda p: GoogleAdapter.click_top_result(p))

    def google_inspect_results(self, max_results: int = 5) -> Dict[str, Any]:
        return self._execute(lambda p: GoogleAdapter.inspect_results(p, max_items=max_results))

    def google_extract_content(self) -> Dict[str, Any]:
        return self._execute(lambda p: GoogleAdapter.extract_page_content(p))

    # YouTube
    def youtube_search(self, query: str) -> Dict[str, Any]:
        return self._execute(lambda p: YouTubeAdapter.search_song_or_video(p, query=query), target_url="https://www.youtube.com")

    def youtube_search_and_play(self, query: str) -> Dict[str, Any]:
        return self._execute(lambda p: YouTubeAdapter.execute_full_search_and_play(p, query=query), target_url="https://www.youtube.com")

    def youtube_click_first(self) -> Dict[str, Any]:
        return self._execute(lambda p: YouTubeAdapter.click_first_video(p), target_url="https://www.youtube.com")

    def youtube_pause(self) -> Dict[str, Any]:
        return self._execute(lambda p: YouTubeAdapter.pause_playback(p), target_url="https://www.youtube.com")

    def youtube_resume(self) -> Dict[str, Any]:
        return self._execute(lambda p: YouTubeAdapter.resume_playback(p), target_url="https://www.youtube.com")

    def youtube_stop(self) -> Dict[str, Any]:
        return self._execute(lambda p: YouTubeAdapter.stop_playback(p))

    # Spotify
    def spotify_search(self, query: str) -> Dict[str, Any]:
        return self._execute(lambda p: SpotifyAdapter.search_song(p, query=query))

    def spotify_play(self, query: str) -> Dict[str, Any]:
        return self._execute(lambda p: SpotifyAdapter.play_top_result(p, query=query))

    # Instagram
    def instagram_open(self) -> Dict[str, Any]:
        return self._execute(lambda p: InstagramAdapter.open_home(p), target_url="https://www.instagram.com")

    def instagram_reels(self) -> Dict[str, Any]:
        return self._execute(lambda p: InstagramAdapter.navigate_reels(p))

    def instagram_dms(self) -> Dict[str, Any]:
        return self._execute(lambda p: InstagramAdapter.navigate_dms(p))

    def instagram_open_conversation(self, contact_name: str) -> Dict[str, Any]:
        return self._execute(lambda p: InstagramAdapter.open_conversation(p, contact_name=contact_name))

    def instagram_read_messages(self, max_messages: int = 5) -> Dict[str, Any]:
        return self._execute(lambda p: InstagramAdapter.read_visible_messages(p, max_messages=max_messages))

    # -------------------------------------------------------------------------
    # Web Prompter & Form Submitter (ChatGPT, Claude, GitHub, etc.)
    # -------------------------------------------------------------------------
    def web_prompt_and_submit(self, url: str, prompt: str, submit: bool = True) -> Dict[str, Any]:
        """
        Navigates or switches to a web service (e.g. ChatGPT, Claude, GitHub),
        locates the main prompt/search input, types the text, and optionally submits.
        """
        def _prompt(page):
            current_url = page.url.lower() if page.url else ""
            target_domain = url.split("//")[-1].split("/")[0].lower()
            if target_domain not in current_url:
                page.goto(url, wait_until="domcontentloaded", timeout=30000)
                page.wait_for_timeout(1500)

            # Check if GitHub or general site has a search activation button first
            if "github.com" in current_url:
                try:
                    for search_trigger in [
                        "button.header-search-button",
                        "[data-target='qbsearch-input.inputButtonText']",
                        "button[aria-label*='Search' i]"
                    ]:
                        btn = page.locator(search_trigger).first
                        if btn.is_visible(timeout=800):
                            btn.click()
                            page.wait_for_timeout(400)
                            break
                except Exception:
                    pass

            selectors = [
                "#prompt-textarea",
                "input#query-builder-test",
                "input[name='query-builder-test']",
                "div[contenteditable='true'][aria-label*='prompt' i]",
                "div[contenteditable='true'][aria-label*='message' i]",
                "div[contenteditable='true']",
                "textarea[placeholder*='message' i]",
                "textarea[placeholder*='ask' i]",
                "textarea[placeholder*='prompt' i]",
                "textarea",
                "input[placeholder*='search' i]",
                "input[aria-label*='search' i]",
                "input[name='q']",
                "input[type='text']",
                "[role='textbox']"
            ]

            target_el = None
            for sel in selectors:
                try:
                    locator = page.locator(sel).first
                    if locator.is_visible(timeout=1000):
                        target_el = locator
                        break
                except Exception:
                    continue

            if not target_el and any("github.com" in u for u in [url.lower(), page.url.lower()]):
                # Direct search URL fallback for GitHub
                import urllib.parse
                search_url = f"https://github.com/search?q={urllib.parse.quote(prompt)}"
                page.goto(search_url, wait_until="domcontentloaded", timeout=20000)
                return {
                    "success": True,
                    "action": "web_prompt_and_submit",
                    "url": search_url,
                    "prompt": prompt,
                    "submitted": True
                }

            if not target_el:
                return {
                    "success": False,
                    "action": "web_prompt_and_submit",
                    "error": f"Prompt or search input field could not be found on {url}."
                }

            target_el.click()
            page.wait_for_timeout(200)
            target_el.fill(prompt)
            page.wait_for_timeout(300)
            if submit:
                target_el.press("Enter")
                page.wait_for_timeout(800)

            return {
                "success": True,
                "action": "web_prompt_and_submit",
                "url": url,
                "prompt": prompt,
                "submitted": submit
            }

        return self._execute(_prompt, target_url=url)

    # -------------------------------------------------------------------------
    # Lifecycle
    # -------------------------------------------------------------------------

    def close(self):
        """Closes active session tab."""
        self._session_mgr.close_session(self.conversation_id)
