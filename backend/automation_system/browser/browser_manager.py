"""
O.P.S. 2.0 Browser Manager & Session Persistence Engine
Technology: Playwright
Maintains persistent headed/visible browser sessions across conversation turns,
manages active tabs, and handles graceful lifecycle cleanup.
"""

import os
import time
import logging
import threading
from typing import Dict, Optional, Tuple, Any
from playwright.sync_api import sync_playwright, Playwright, Browser, BrowserContext, Page

logger = logging.getLogger("OPS.BrowserManager")


class BrowserManager:
    """
    Manages Playwright process, browser instance, and contexts.
    Defaults to headed mode (headless=False) so operations are visible on the desktop.
    """

    def __init__(self, headless: Optional[bool] = None):
        if headless is not None:
            self.headless = headless
        else:
            # Default to visible/headed unless explicitly overridden by environment variable
            env_val = os.getenv("OPS_BROWSER_HEADLESS", "false").lower()
            self.headless = env_val in ["1", "true", "yes"]

        self._playwright: Optional[Playwright] = None
        self._browser: Optional[Browser] = None

    def start(self) -> Browser:
        """Starts Playwright and launches Chromium."""
        if not self._playwright:
            self._playwright = sync_playwright().start()
        if not self._browser or not self._browser.is_connected():
            self._browser = self._playwright.chromium.launch(
                headless=self.headless,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                    "--start-maximized"
                ]
            )
            logger.info(f"Launched Chromium (headless={self.headless})")
        return self._browser

    def new_context_and_page(self) -> Tuple[BrowserContext, Page]:
        """Creates a fresh context and primary page."""
        browser = self.start()
        context = browser.new_context(
            viewport=None,  # Allows maximized window matching display
            accept_downloads=True,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        return context, page

    def close(self):
        """Closes browser and Playwright."""
        try:
            if self._browser and self._browser.is_connected():
                self._browser.close()
        except Exception as e:
            logger.warning(f"Error closing browser: {e}")
        finally:
            self._browser = None

        try:
            if self._playwright:
                self._playwright.stop()
        except Exception as e:
            logger.warning(f"Error stopping playwright: {e}")
        finally:
            self._playwright = None


class BrowserSessionManager:
    """
    Singleton managing persistent browser contexts and pages per conversation_id.
    Maintains open pages across conversational turns so follow-up commands
    ('open the first result', 'search for another song', 'go back') execute on the live tab.
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(BrowserSessionManager, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._browser_manager: Optional[BrowserManager] = None
        # conversation_id -> {"context": BrowserContext, "page": Page, "last_active": float}
        self._sessions: Dict[str, Dict[str, Any]] = {}
        self._session_lock = threading.Lock()

    def _ensure_browser_manager(self, headless: Optional[bool] = None) -> BrowserManager:
        if not self._browser_manager:
            self._browser_manager = BrowserManager(headless=headless)
        return self._browser_manager

    def get_or_create_page(self, conversation_id: str, headless: Optional[bool] = None) -> Page:
        """
        Retrieves active Page for conversation_id or initializes a new one.
        Ensures page is alive; if closed, recreates it seamlessly.
        """
        cid = conversation_id or "default_session"
        with self._session_lock:
            bm = self._ensure_browser_manager(headless=headless)

            session = self._sessions.get(cid)
            if session:
                page: Page = session.get("page")
                if page and not page.is_closed():
                    try:
                        # Test if page is still responsive
                        _ = page.url
                        session["last_active"] = time.time()
                        return page
                    except Exception:
                        logger.info(f"Existing page for {cid} was disconnected, recreating.")

            # Create new context and page for this conversation session
            context, page = bm.new_context_and_page()
            self._sessions[cid] = {
                "context": context,
                "page": page,
                "last_active": time.time()
            }
            logger.info(f"Initialized persistent browser page for session '{cid}'.")
            return page

    def get_active_page(self, conversation_id: str) -> Optional[Page]:
        """Returns existing page if open without auto-creating."""
        cid = conversation_id or "default_session"
        with self._session_lock:
            session = self._sessions.get(cid)
            if session:
                page = session.get("page")
                if page and not page.is_closed():
                    return page
            return None

    def close_session(self, conversation_id: str):
        """Closes browser context associated with a specific conversation."""
        cid = conversation_id or "default_session"
        with self._session_lock:
            session = self._sessions.pop(cid, None)
            if session:
                try:
                    ctx: BrowserContext = session.get("context")
                    if ctx:
                        ctx.close()
                    logger.info(f"Closed browser session '{cid}'.")
                except Exception as e:
                    logger.warning(f"Error closing context for '{cid}': {e}")

    def close_all(self):
        """Closes all sessions and underlying browser."""
        with self._session_lock:
            for cid, session in list(self._sessions.items()):
                try:
                    ctx = session.get("context")
                    if ctx:
                        ctx.close()
                except Exception:
                    pass
            self._sessions.clear()

            if self._browser_manager:
                self._browser_manager.close()
                self._browser_manager = None
            logger.info("Closed all active browser sessions.")
