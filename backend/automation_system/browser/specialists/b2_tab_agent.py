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

    def switch_tab(self, tab_index: int) -> Dict[str, Any]:
        """Switches active tab to index."""
        try:
            res = self.tab_mgr.switch_tab(tab_index)
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
