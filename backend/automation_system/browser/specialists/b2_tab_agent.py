"""
O.P.S. 2.0 Browser Automation Specialist — Agent B2: Tab Management Agent
Responsibilities:
- Create new tabs, switch tabs, close tabs
- Track tab IDs, titles, and active URLs
- Prevent unnecessary duplicate tabs
- Recover from closed or invalid tab handles
"""

import logging
from typing import Dict, Any, List, Optional
from automation_system.browser.browser_manager import BrowserSessionManager
from automation_system.browser.tab_manager import TabManager

logger = logging.getLogger("OPS.Browser.B2_TabAgent")


class B2_TabAgent:
    """Specialist Agent B2: Manages browser tabs, multi-tab contexts, and switching."""

    def __init__(self, conversation_id: str = "default_session"):
        self.agent_id = "agent_b2_tab"
        self.agent_name = "Tab Management Agent"
        self.conversation_id = conversation_id or "default_session"
        self.manager = BrowserSessionManager()
        self.tab_mgr = TabManager(self.conversation_id)

    def new_tab(self, url: Optional[str] = None) -> Dict[str, Any]:
        """Creates a new tab and navigates if URL provided."""
        try:
            res = self.tab_mgr.new_tab(url=url)
            res["agent_id"] = self.agent_id
            return res
        except Exception as e:
            logger.error(f"new_tab failed: {e}")
            return {"success": False, "agent_id": self.agent_id, "error": str(e)}

    def switch_tab(self, tab_target: Any) -> Dict[str, Any]:
        """Switches active tab to index (int) or matching title/url (str)."""
        try:
            if isinstance(tab_target, str) and not tab_target.isdigit():
                # Resolve by title or url
                tabs_res = self.list_tabs()
                if tabs_res.get("success"):
                    t_low = tab_target.lower()
                    for t in tabs_res.get("tabs", []):
                        if t_low in t.get("url", "").lower() or t_low in t.get("title", "").lower():
                            res = self.tab_mgr.switch_tab(t.get("index", 0))
                            res["agent_id"] = self.agent_id
                            res["matched_target"] = tab_target
                            return res
                return {"success": False, "agent_id": self.agent_id, "error": f"Tab matching '{tab_target}' not found."}

            idx = int(tab_target)
            res = self.tab_mgr.switch_tab(idx)
            res["agent_id"] = self.agent_id
            return res
        except Exception as e:
            return {"success": False, "agent_id": self.agent_id, "error": str(e)}

    def close_current_tab(self) -> Dict[str, Any]:
        """Closes the current active tab."""
        try:
            res = self.tab_mgr.close_current_tab()
            res["agent_id"] = self.agent_id
            return res
        except Exception as e:
            return {"success": False, "agent_id": self.agent_id, "error": str(e)}

    def close_tab(self, target: Any = None) -> Dict[str, Any]:
        """Closes a specific tab matching index (int) or title/url (str). If None, closes current."""
        try:
            if target is None:
                return self.close_current_tab()
            res = self.tab_mgr.close_tab(target)
            res["agent_id"] = self.agent_id
            return res
        except Exception as e:
            return {"success": False, "agent_id": self.agent_id, "error": str(e)}

    def list_tabs(self) -> Dict[str, Any]:
        """Lists all open tabs with titles, URLs, and active status."""
        try:
            tabs = self.tab_mgr.list_tabs()
            return {"success": True, "agent_id": self.agent_id, "tabs": tabs, "count": len(tabs)}
        except Exception as e:
            return {"success": False, "agent_id": self.agent_id, "error": str(e), "tabs": []}

    def get_or_create_tab(self, target_url: str) -> Dict[str, Any]:
        """Reuses existing tab if matching domain is open, otherwise creates new tab."""
        tabs_res = self.list_tabs()
        if tabs_res.get("success"):
            tabs = tabs_res.get("tabs", [])
            from urllib.parse import urlparse
            target_domain = urlparse(target_url).netloc.lower()
            for t in tabs:
                t_domain = urlparse(t.get("url", "")).netloc.lower()
                if target_domain and target_domain in t_domain:
                    self.switch_tab(t.get("index", 0))
                    return {
                        "success": True,
                        "agent_id": self.agent_id,
                        "action": "reused_tab",
                        "tab_index": t.get("index"),
                        "url": t.get("url")
                    }
        # Otherwise create new tab
        return self.new_tab(url=target_url)
