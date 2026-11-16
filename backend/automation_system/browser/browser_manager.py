"""
O.P.S. 2.0 Browser Manager & Session Persistence Engine
Technology: Playwright (Chromium Headed/Visible Engine)
Maintains persistent headed/visible browser sessions across conversation turns,
manages active tabs, and guarantees thread-safe execution via a dedicated worker thread.
"""

import os
import sys
import time
import queue
import logging
import threading
from typing import Dict, Optional, Tuple, Any, Callable, List
from playwright.sync_api import sync_playwright, Playwright, BrowserContext, Page

logger = logging.getLogger("OPS.BrowserManager")

# Persistent profile path in user home directory to avoid filesystem issues with special path characters
DEFAULT_USER_DATA_DIR = os.path.join(os.path.expanduser("~"), ".ops", "browser_profile")


class PlaywrightWorker:
    """
    Dedicated background worker thread running Playwright's sync_api event loop.
    All Playwright calls are dispatched to and executed sequentially on this thread.
    This eliminates cross-thread greenlet errors (greenlet.error: Cannot switch to a different thread)
    when Django handles requests across arbitrary worker threads.
    """

    def __init__(self, headless: bool = False, user_data_dir: Optional[str] = None):
        self.headless = headless
        self.user_data_dir = user_data_dir or DEFAULT_USER_DATA_DIR
        os.makedirs(self.user_data_dir, exist_ok=True)

        self._queue: queue.Queue = queue.Queue()
        self._thread = threading.Thread(target=self._run_loop, daemon=True, name="OPS-PlaywrightWorker")

        self.playwright: Optional[Playwright] = None
        self.context: Optional[BrowserContext] = None
        # session_id -> Page
        self.pages: Dict[str, Page] = {}
        self.last_active: Dict[str, float] = {}

        self._thread.start()

        # Wait for worker initialization
        ready_q: queue.Queue = queue.Queue()
        self._queue.put(("INIT", ready_q))
        status, err = ready_q.get(timeout=30)
        if status != "OK":
            raise RuntimeError(f"Playwright worker initialization failed: {err}")

    def _run_loop(self):
        """Worker thread main loop."""
        try:
            self.playwright = sync_playwright().start()
            self._launch_context()
        except Exception as e:
            logger.error(f"Failed to start Playwright worker: {e}", exc_info=True)

        while True:
            try:
                item = self._queue.get()
                if item is None:
                    break

                cmd, payload = item

                if cmd == "INIT":
                    ready_q = payload
                    if self.context:
                        ready_q.put(("OK", None))
                    else:
                        ready_q.put(("ERR", "Could not initialize persistent context."))

                elif cmd == "EXEC":
                    fn, args, kwargs, reply_q = payload
                    try:
                        res = fn(self, *args, **kwargs)
                        reply_q.put(("OK", res))
                    except Exception as e:
                        logger.error(f"Error executing Playwright command: {e}")
                        reply_q.put(("ERR", e))

                elif cmd == "STOP":
                    reply_q = payload
                    self._cleanup()
                    reply_q.put(("OK", None))
                    break

            except Exception as loop_err:
                logger.error(f"Unexpected error in Playwright worker loop: {loop_err}")

    def _launch_context(self):
        """Launches persistent Chromium browser context."""
        try:
            if not self.playwright:
                self.playwright = sync_playwright().start()

            args = [
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--start-maximized",
                "--disable-infobars",
                "--no-default-browser-check"
            ]

            self.context = self.playwright.chromium.launch_persistent_context(
                user_data_dir=self.user_data_dir,
                headless=self.headless,
                viewport=None,  # Matches window maximized bounds
                accept_downloads=True,
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
                args=args
            )
            logger.info(f"Playwright persistent context launched (headless={self.headless}, profile='{self.user_data_dir}')")
        except Exception as e:
            logger.error(f"Failed to launch persistent context: {e}", exc_info=True)
            self.context = None

    def _ensure_context(self):
        """Ensures context is alive, recreating if closed."""
        try:
            if not self.context or not self.context.browser or not self.context.browser.is_connected():
                logger.warning("Browser context was disconnected. Relaunching...")
                self._launch_context()
        except Exception:
            self._launch_context()

    def _cleanup(self):
        """Closes all pages, context, and stops Playwright."""
        try:
            if self.context:
                self.context.close()
        except Exception:
            pass
        finally:
            self.context = None
            self.pages.clear()

        try:
            if self.playwright:
                self.playwright.stop()
        except Exception:
            pass
        finally:
            self.playwright = None

    def execute(self, fn: Callable, *args, timeout: float = 60.0, **kwargs) -> Any:
        """Dispatches a function to run on the Playwright worker thread and returns the result."""
        if not self._thread.is_alive():
            raise RuntimeError("Playwright worker thread is not running.")

        reply_q: queue.Queue = queue.Queue()
        self._queue.put(("EXEC", (fn, args, kwargs, reply_q)))
        status, val = reply_q.get(timeout=timeout)
        if status == "ERR":
            raise val
        return val

    def stop(self):
        """Stops the worker thread cleanly."""
        if self._thread.is_alive():
            reply_q: queue.Queue = queue.Queue()
            self._queue.put(("STOP", reply_q))
            try:
                reply_q.get(timeout=10.0)
            except Exception:
                pass


class BrowserManager:
    """
    Singleton managing the PlaywrightWorker process, browser instance, and persistent contexts.
    Defaults to headed mode (headless=False) so operations are visible on the desktop.
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(BrowserManager, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self, headless: Optional[bool] = None):
        if self._initialized:
            return
        self._initialized = True

        if headless is not None:
            self.headless = headless
        else:
            env_val = os.getenv("OPS_BROWSER_HEADLESS", "false").lower()
            self.headless = env_val in ["1", "true", "yes"]

        self._worker: Optional[PlaywrightWorker] = None
        self._worker_lock = threading.Lock()

    def _ensure_worker(self) -> PlaywrightWorker:
        with self._worker_lock:
            if not self._worker or not self._worker._thread.is_alive():
                self._worker = PlaywrightWorker(headless=self.headless)
            return self._worker

    def execute(self, fn: Callable, *args, timeout: float = 60.0, **kwargs) -> Any:
        """Executes a function on the dedicated Playwright thread."""
        worker = self._ensure_worker()
        return worker.execute(fn, *args, timeout=timeout, **kwargs)

    def close(self):
        """Shuts down worker and browser."""
        with self._worker_lock:
            if self._worker:
                self._worker.stop()
                self._worker = None


class PageProxy:
    """
    Thread-safe proxy for a Playwright Page.
    Intercepts method calls and properties, routing them to the dedicated Playwright worker thread.
    Allows code in any Django or worker thread to treat Page as a normal synchronous object.
    """

    def __init__(self, browser_manager: BrowserManager, session_id: str):
        self._bm = browser_manager
        self._session_id = session_id or "default_session"

    def _get_page(self, w: PlaywrightWorker) -> Page:
        w._ensure_context()
        page = w.pages.get(self._session_id)
        if not page or page.is_closed():
            # If default context already has an open page, reuse first page for default_session
            if self._session_id == "default_session" and w.context.pages:
                page = w.context.pages[0]
            else:
                page = w.context.new_page()
            w.pages[self._session_id] = page
        w.last_active[self._session_id] = time.time()
        return page

    @property
    def url(self) -> str:
        return self._bm.execute(lambda w: getattr(self._get_page(w), "url", ""))

    def title(self) -> str:
        return self._bm.execute(lambda w: self._get_page(w).title())

    def is_closed(self) -> bool:
        return self._bm.execute(lambda w: self._get_page(w).is_closed())

    def goto(self, url: str, **kwargs) -> Any:
        return self._bm.execute(lambda w: self._get_page(w).goto(url, **kwargs))

    def reload(self, **kwargs) -> Any:
        return self._bm.execute(lambda w: self._get_page(w).reload(**kwargs))

    def go_back(self, **kwargs) -> Any:
        return self._bm.execute(lambda w: self._get_page(w).go_back(**kwargs))

    def go_forward(self, **kwargs) -> Any:
        return self._bm.execute(lambda w: self._get_page(w).go_forward(**kwargs))

    def click(self, selector: str, **kwargs) -> Any:
        return self._bm.execute(lambda w: self._get_page(w).click(selector, **kwargs))

    def fill(self, selector: str, value: str, **kwargs) -> Any:
        return self._bm.execute(lambda w: self._get_page(w).fill(selector, value, **kwargs))

    def type(self, selector: str, text: str, **kwargs) -> Any:
        return self._bm.execute(lambda w: self._get_page(w).type(selector, text, **kwargs))

    def press(self, selector: str, key: str, **kwargs) -> Any:
        return self._bm.execute(lambda w: self._get_page(w).press(selector, key, **kwargs))

    def evaluate(self, expression: str, arg: Any = None) -> Any:
        return self._bm.execute(lambda w: self._get_page(w).evaluate(expression, arg))

    def wait_for_selector(self, selector: str, **kwargs) -> Any:
        return self._bm.execute(lambda w: bool(self._get_page(w).wait_for_selector(selector, **kwargs)))

    def screenshot(self, **kwargs) -> Any:
        return self._bm.execute(lambda w: self._get_page(w).screenshot(**kwargs))

    def close(self):
        def _close(w):
            page = w.pages.pop(self._session_id, None)
            if page and not page.is_closed():
                page.close()
        return self._bm.execute(_close)


class BrowserSessionManager:
    """
    Singleton managing persistent browser contexts and pages per conversation_id.
    Maintains open pages across conversational turns so follow-up commands
    ('open the first result', 'search for another song', 'go back') execute on the live tab.
    Guarantees thread-safety across all Django request threads.
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
        self._browser_manager = BrowserManager()

    def get_or_create_page(self, conversation_id: str, headless: Optional[bool] = None) -> PageProxy:
        """
        Retrieves thread-safe PageProxy for conversation_id.
        All calls on PageProxy run on the dedicated worker thread.
        """
        cid = conversation_id or "default_session"
        return PageProxy(self._browser_manager, cid)

    def execute_on_page(
        self,
        conversation_id: str,
        fn: Callable[[Page], Any],
        timeout: float = 60.0,
        target_url: Optional[str] = None
    ) -> Any:
        """
        Executes a callable taking the real Playwright Page object directly inside
        the dedicated worker thread. Multi-tab aware: opens separate tabs for different
        domains (e.g. Google and GitHub each get their own tab without closing previous tabs),
        and switches focus to existing tabs when re-visiting the same site.
        """
        cid = conversation_id or "default_session"

        def _worker_action(w: PlaywrightWorker):
            import urllib.parse
            w._ensure_context()
            pages = [p for p in w.context.pages if not p.is_closed()]

            # Determine target domain if URL provided
            target_domain = ""
            if target_url:
                clean_target = target_url if target_url.startswith("http") else f"https://{target_url}"
                try:
                    parsed = urllib.parse.urlparse(clean_target)
                    target_domain = (parsed.netloc or "").lower().replace("www.", "")
                except Exception:
                    pass

            page = None

            # 1. If target domain is known, check if any open tab already matches
            if target_domain and pages:
                for p in pages:
                    try:
                        p_netloc = urllib.parse.urlparse(p.url).netloc.lower().replace("www.", "")
                        if target_domain in p_netloc or p_netloc in target_domain:
                            page = p
                            break
                    except Exception:
                        pass

            # 2. If no tab matched target domain
            if not page:
                curr_page = w.pages.get(cid)
                if curr_page and not curr_page.is_closed():
                    # If current tab is blank, reuse it for this navigation
                    if curr_page.url in ["about:blank", ""]:
                        page = curr_page
                    elif target_domain:
                        # Current tab is on a different domain -> OPEN IN A NEW TAB
                        page = w.context.new_page()
                    else:
                        page = curr_page
                elif pages:
                    # Reuse first page if blank, else create new page if target_domain requested
                    first_p = pages[0]
                    if first_p.url in ["about:blank", ""]:
                        page = first_p
                    elif target_domain:
                        page = w.context.new_page()
                    else:
                        page = pages[-1]
                else:
                    page = w.context.new_page()

            # Bring active page to front and register for session
            try:
                page.bring_to_front()
            except Exception:
                pass
            w.pages[cid] = page
            w.last_active[cid] = time.time()
            return fn(page)

        return self._browser_manager.execute(_worker_action, timeout=timeout)

    def get_active_page(self, conversation_id: str) -> Optional[PageProxy]:
        """Returns PageProxy if active page exists and is open."""
        cid = conversation_id or "default_session"

        def _check(w: PlaywrightWorker) -> bool:
            page = w.pages.get(cid)
            return bool(page and not page.is_closed())

        try:
            if self._browser_manager.execute(_check, timeout=5.0):
                return PageProxy(self._browser_manager, cid)
        except Exception:
            pass
        return None

    def close_session(self, conversation_id: str):
        """Closes page associated with conversation_id."""
        cid = conversation_id or "default_session"

        def _close(w: PlaywrightWorker):
            page = w.pages.pop(cid, None)
            if page and not page.is_closed():
                try:
                    page.close()
                except Exception:
                    pass
            w.last_active.pop(cid, None)

        try:
            self._browser_manager.execute(_close, timeout=10.0)
        except Exception as e:
            logger.warning(f"Error closing session '{cid}': {e}")

    def close_all(self):
        """Closes all pages and shuts down underlying browser."""
        self._browser_manager.close()
