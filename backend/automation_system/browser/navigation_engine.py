"""
O.P.S. 2.0 Browser Navigation Engine
Handles page navigation, back/forward history traversal, reload,
readiness checks, and cookie/dialog consent dismissals.
"""

import time
import logging
from typing import Dict, Any, Optional
from playwright.sync_api import Page, Response

logger = logging.getLogger("OPS.BrowserNavigation")


class NavigationEngine:
    """
    Executes resilient web navigation and history traversal.
    """

    @classmethod
    def navigate(
        cls,
        page: Page,
        url: str,
        wait_until: str = "domcontentloaded",
        timeout_ms: int = 25000
    ) -> Dict[str, Any]:
        """
        Navigates page to target URL with robust timeout and fallback.
        """
        t0 = time.time()
        target_url = url if url.startswith("http") else f"https://{url}"

        try:
            response: Optional[Response] = page.goto(
                target_url,
                wait_until=wait_until,
                timeout=timeout_ms
            )

            # Auto-dismiss common consent / cookie dialogs if present
            cls._dismiss_overlays(page)

            title = page.title()
            cur_url = page.url
            status = response.status if response else 200

            duration = round(time.time() - t0, 2)
            logger.info(f"Navigated to {cur_url} ('{title}') in {duration}s")

            return {
                "success": True,
                "action": "navigate",
                "requested_url": target_url,
                "current_url": cur_url,
                "page_title": title,
                "status_code": status,
                "duration_s": duration
            }
        except Exception as e:
            logger.error(f"Navigation to {target_url} failed: {e}")
            return {
                "success": False,
                "action": "navigate",
                "requested_url": target_url,
                "current_url": getattr(page, "url", ""),
                "error": str(e)
            }

    @classmethod
    def go_back(cls, page: Page, timeout_ms: int = 15000) -> Dict[str, Any]:
        """Navigates back in browser history."""
        t0 = time.time()
        try:
            page.go_back(wait_until="domcontentloaded", timeout=timeout_ms)
            time.sleep(0.5)
            return {
                "success": True,
                "action": "go_back",
                "current_url": page.url,
                "page_title": page.title(),
                "duration_s": round(time.time() - t0, 2)
            }
        except Exception as e:
            return {"success": False, "action": "go_back", "error": str(e)}

    @classmethod
    def go_forward(cls, page: Page, timeout_ms: int = 15000) -> Dict[str, Any]:
        """Navigates forward in browser history."""
        t0 = time.time()
        try:
            page.go_forward(wait_until="domcontentloaded", timeout=timeout_ms)
            time.sleep(0.5)
            return {
                "success": True,
                "action": "go_forward",
                "current_url": page.url,
                "page_title": page.title(),
                "duration_s": round(time.time() - t0, 2)
            }
        except Exception as e:
            return {"success": False, "action": "go_forward", "error": str(e)}

    @classmethod
    def reload(cls, page: Page, timeout_ms: int = 15000) -> Dict[str, Any]:
        """Reloads the current page."""
        t0 = time.time()
        try:
            page.reload(wait_until="domcontentloaded", timeout=timeout_ms)
            return {
                "success": True,
                "action": "reload",
                "current_url": page.url,
                "page_title": page.title(),
                "duration_s": round(time.time() - t0, 2)
            }
        except Exception as e:
            return {"success": False, "action": "reload", "error": str(e)}

    @classmethod
    def _dismiss_overlays(cls, page: Page):
        """Attempts to click 'Accept', 'Agree', 'Dismiss', or 'Not Now' dialogs."""
        common_buttons = [
            "button:has-text('Accept all')",
            "button:has-text('Reject all')",
            "button:has-text('I agree')",
            "button:has-text('Agree')",
            "button:has-text('Not now')",
            "button:has-text('Not Now')",
            "button[aria-label='Close']",
            "button[aria-label='Dismiss']",
            "yt-button-renderer:has-text('Reject all')",
            "yt-button-renderer:has-text('Accept all')"
        ]
        for sel in common_buttons:
            try:
                btn = page.locator(sel).first
                if btn.is_visible(timeout=500):
                    btn.click(timeout=1000)
                    time.sleep(0.3)
                    break
            except Exception:
                continue
