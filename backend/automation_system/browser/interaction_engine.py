"""
O.P.S. 2.0 Browser Interaction Engine
Executes element clicks, form typing, list result selections,
scrolling, and keyboard actions with accessible role locators and auto-waits.
"""

import time
import logging
from typing import Dict, Any, Optional
from playwright.sync_api import Page, Locator

logger = logging.getLogger("OPS.BrowserInteraction")


class InteractionEngine:
    """
    Executes resilient DOM interactions and element activations.
    """

    @classmethod
    def click(
        cls,
        page: Page,
        selector: Optional[str] = None,
        name: Optional[str] = None,
        role: Optional[str] = None,
        timeout_ms: int = 10000
    ) -> Dict[str, Any]:
        """
        Clicks element using accessible role, text, or CSS selector with auto-wait.
        """
        t0 = time.time()
        try:
            locator: Optional[Locator] = None
            desc = ""

            if role and name:
                locator = page.get_by_role(role, name=name).first
                desc = f"role='{role}', name='{name}'"
            elif name and not selector:
                locator = page.get_by_text(name, exact=False).first
                desc = f"text='{name}'"
            elif selector:
                locator = page.locator(selector).first
                desc = f"selector='{selector}'"
            else:
                return {"success": False, "action": "click", "error": "No locator target specified."}

            locator.scroll_into_view_if_needed(timeout=timeout_ms)
            locator.click(timeout=timeout_ms)

            # Brief pause for DOM reactions
            time.sleep(0.8)

            duration = round(time.time() - t0, 2)
            return {
                "success": True,
                "action": "click",
                "target": desc,
                "current_url": page.url,
                "page_title": page.title(),
                "duration_s": duration
            }
        except Exception as e:
            logger.error(f"Click failed on {desc if 'desc' in locals() else selector}: {e}")
            return {
                "success": False,
                "action": "click",
                "error": str(e)
            }

    @classmethod
    def click_first_result(cls, page: Page, timeout_ms: int = 15000) -> Dict[str, Any]:
        """
        Intelligently clicks the first primary search result on current page
        (YouTube video, Google organic link, etc.).
        """
        t0 = time.time()
        cur_url = page.url.lower()

        # YouTube First Video Result Locators
        if "youtube.com" in cur_url:
            yt_selectors = [
                "ytd-video-renderer #video-title",
                "ytd-video-renderer a#thumbnail",
                "ytd-item-section-renderer ytd-video-renderer h3 a",
                "a#video-title"
            ]
            for sel in yt_selectors:
                try:
                    loc = page.locator(sel).first
                    if loc.is_visible(timeout=2000):
                        title_text = loc.inner_text() or "YouTube Video"
                        loc.click(timeout=timeout_ms)
                        time.sleep(1.5)
                        return {
                            "success": True,
                            "action": "click_first_result",
                            "site": "YouTube",
                            "clicked_title": title_text,
                            "current_url": page.url,
                            "page_title": page.title(),
                            "duration_s": round(time.time() - t0, 2)
                        }
                except Exception:
                    continue

        # Google First Organic Link
        elif "google.com" in cur_url:
            google_selectors = [
                "#search a h3",
                "#rso a h3",
                "div.g a h3",
                "#search a"
            ]
            for sel in google_selectors:
                try:
                    loc = page.locator(sel).first
                    if loc.is_visible(timeout=2000):
                        title_text = loc.inner_text() or "Google Search Result"
                        loc.click(timeout=timeout_ms)
                        time.sleep(1.5)
                        return {
                            "success": True,
                            "action": "click_first_result",
                            "site": "Google",
                            "clicked_title": title_text,
                            "current_url": page.url,
                            "page_title": page.title(),
                            "duration_s": round(time.time() - t0, 2)
                        }
                except Exception:
                    continue

        # Generic First Article or Link with Heading
        generic_selectors = [
            "article a",
            "main a h2",
            "main a h3",
            "main a",
            "div.results a",
            ".search-results a"
        ]
        for sel in generic_selectors:
            try:
                loc = page.locator(sel).first
                if loc.is_visible(timeout=2000):
                    title_text = loc.inner_text() or "Result"
                    loc.click(timeout=timeout_ms)
                    time.sleep(1.0)
                    return {
                        "success": True,
                        "action": "click_first_result",
                        "site": "Generic",
                        "clicked_title": title_text,
                        "current_url": page.url,
                        "page_title": page.title(),
                        "duration_s": round(time.time() - t0, 2)
                    }
            except Exception:
                continue

        return {
            "success": False,
            "action": "click_first_result",
            "error": "Could not identify first result on current page."
        }

    @classmethod
    def fill_form(
        cls,
        page: Page,
        selector_or_label: str,
        text: str,
        is_secret: bool = False,
        timeout_ms: int = 8000
    ) -> Dict[str, Any]:
        """Fills input with auto-label detection."""
        t0 = time.time()
        try:
            # 1. Accessible label
            try:
                loc = page.get_by_label(selector_or_label, exact=False).first
                if loc.is_visible(timeout=1000):
                    loc.fill(text, timeout=timeout_ms)
                    return {
                        "success": True,
                        "action": "fill_form",
                        "field": selector_or_label,
                        "is_secret": is_secret,
                        "duration_s": round(time.time() - t0, 2)
                    }
            except Exception:
                pass

            # 2. Selector
            loc = page.locator(selector_or_label).first
            loc.fill(text, timeout=timeout_ms)
            return {
                "success": True,
                "action": "fill_form",
                "field": selector_or_label,
                "is_secret": is_secret,
                "duration_s": round(time.time() - t0, 2)
            }
        except Exception as e:
            return {"success": False, "action": "fill_form", "field": selector_or_label, "error": str(e)}

    @classmethod
    def scroll(cls, page: Page, direction: str = "down", amount: int = 500) -> Dict[str, Any]:
        """Scrolls current page."""
        delta = amount if direction == "down" else -amount
        page.evaluate(f"window.scrollBy(0, {delta})")
        time.sleep(0.3)
        return {"success": True, "action": "scroll", "direction": direction, "amount": amount}

    @classmethod
    def press_key(cls, page: Page, key: str = "Enter") -> Dict[str, Any]:
        """Sends keyboard key to page."""
        page.keyboard.press(key)
        time.sleep(0.3)
        return {"success": True, "action": "press_key", "key": key}
