"""
O.P.S. 2.0 Browser Tab Manager
Technology: Playwright
Manages multiple browser tabs per conversation session:
- Listing open tabs (titles and URLs)
- Switching between tabs by index or title
- Opening new tabs and closing specific tabs
- Seamless active tab reuse and crash recovery
"""

import logging
from typing import Dict, Any, List, Optional
from playwright.sync_api import Page, BrowserContext
from automation_system.browser.browser_manager import BrowserSessionManager, PlaywrightWorker

logger = logging.getLogger("OPS.BrowserTabManager")


class TabManager:
    """
    Manages browser tab lifecycle for a conversation session.
    """

    def __init__(self, conversation_id: str):
        self.conversation_id = conversation_id or "default_session"
        self._session_mgr = BrowserSessionManager()

    def list_tabs(self) -> List[Dict[str, Any]]:
        """Returns structured metadata for all open tabs in this session context."""
        def _list(w: PlaywrightWorker) -> List[Dict[str, Any]]:
            w._ensure_context()
            tabs = []
            for i, p in enumerate(w.context.pages):
                try:
                    tabs.append({
                        "index": i,
                        "url": p.url,
                        "title": p.title(),
                        "is_active": (w.pages.get(self.conversation_id) == p)
                    })
                except Exception:
                    pass
            return tabs

        return self._session_mgr._browser_manager.execute(_list, timeout=10.0)

    def new_tab(self, url: Optional[str] = None) -> Dict[str, Any]:
        """Opens a new tab in the session context, optionally navigating to url."""
        def _new(w: PlaywrightWorker) -> Dict[str, Any]:
            w._ensure_context()
            page = w.context.new_page()
            w.pages[self.conversation_id] = page
            if url:
                target = url if url.startswith("http") else f"https://{url}"
                page.goto(target, wait_until="domcontentloaded", timeout=25000)
            return {
                "success": True,
                "action": "new_tab",
                "tab_count": len(w.context.pages),
                "url": page.url,
                "title": page.title()
            }

        return self._session_mgr._browser_manager.execute(_new, timeout=35.0)

    def switch_tab(self, index: int) -> Dict[str, Any]:
        """Switches the active conversation page to the specified tab index."""
        def _switch(w: PlaywrightWorker) -> Dict[str, Any]:
            w._ensure_context()
            pages = w.context.pages
            if 0 <= index < len(pages):
                target_page = pages[index]
                target_page.bring_to_front()
                w.pages[self.conversation_id] = target_page
                return {
                    "success": True,
                    "action": "switch_tab",
                    "active_index": index,
                    "url": target_page.url,
                    "title": target_page.title()
                }
            return {
                "success": False,
                "action": "switch_tab",
                "error": f"Tab index {index} out of bounds (open tabs: {len(pages)})"
            }

        return self._session_mgr._browser_manager.execute(_switch, timeout=10.0)

    def close_current_tab(self) -> Dict[str, Any]:
        """Closes the current active tab and falls back to previous tab if available."""
        def _close(w: PlaywrightWorker) -> Dict[str, Any]:
            w._ensure_context()
            curr = w.pages.get(self.conversation_id)
            if curr and not curr.is_closed():
                curr.close()

            # Select remaining open page or create a fresh one
            remaining = [p for p in w.context.pages if not p.is_closed()]
            if remaining:
                w.pages[self.conversation_id] = remaining[-1]
                remaining[-1].bring_to_front()
            else:
                w.pages[self.conversation_id] = w.context.new_page()

            active = w.pages[self.conversation_id]
            return {
                "success": True,
                "action": "close_tab",
                "remaining_tabs": len(w.context.pages),
                "active_url": active.url
            }

        return self._session_mgr._browser_manager.execute(_close, timeout=10.0)

    def close_tab(self, target: Any) -> Dict[str, Any]:
        """Closes a specific tab matching an index (int) or title/url substring (str)."""
        def _close_spec(w: PlaywrightWorker) -> Dict[str, Any]:
            w._ensure_context()
            pages = [p for p in w.context.pages if not p.is_closed()]
            target_page = None

            if isinstance(target, int) or (isinstance(target, str) and target.isdigit()):
                idx = int(target)
                if 0 <= idx < len(pages):
                    target_page = pages[idx]
            elif isinstance(target, str) and target:
                t_low = target.lower()
                for p in pages:
                    try:
                        if t_low in p.url.lower() or t_low in p.title().lower():
                            target_page = p
                            break
                    except Exception:
                        pass

            if not target_page:
                return {"success": False, "action": "close_tab", "error": f"Tab matching '{target}' was not found among {len(pages)} open tabs."}

            closed_url = target_page.url
            target_page.close()

            # Ensure active page is valid
            remaining = [p for p in w.context.pages if not p.is_closed()]
            if remaining:
                w.pages[self.conversation_id] = remaining[-1]
                remaining[-1].bring_to_front()
            else:
                w.pages[self.conversation_id] = w.context.new_page()

            return {
                "success": True,
                "action": "close_tab",
                "closed_target": target,
                "closed_url": closed_url,
                "remaining_tabs": len(remaining),
                "active_url": w.pages[self.conversation_id].url
            }

        return self._session_mgr._browser_manager.execute(_close_spec, timeout=10.0)
