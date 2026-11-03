"""
O.P.S. 2.0 Browser Automation Executor
Technology: Playwright (Chromium / Firefox / WebKit)
Provides structured, resilient web automation:
- Robust role/label/text-based locators and auto-waits
- Navigation, form filling, dropdown selection, button clicking
- File downloads with filesystem verification
- Screenshot captures for empirical verification
- Strict credential and privacy protection (never leaks cookies, tokens, or passwords)
"""

import os
import time
import logging
from typing import Dict, Any, List, Optional
from automation_system.verification.verifier import AutomationVerifier

logger = logging.getLogger("OPS.BrowserExecutor")


class BrowserExecutor:
    """
    Executes browser operations via Playwright with auto-waits, accessible locators,
    file download tracking, and state verification.
    """

    def __init__(self, headless: bool = True):
        self.headless = headless
        self._playwright = None
        self._browser = None
        self._context = None
        self._page = None

    def _ensure_browser(self):
        """Initializes Playwright browser context if not already active."""
        if self._page is None or self._page.is_closed():
            from playwright.sync_api import sync_playwright
            self._playwright = sync_playwright().start()
            self._browser = self._playwright.chromium.launch(
                headless=self.headless,
                args=["--disable-blink-features=AutomationControlled", "--no-sandbox"]
            )
            self._context = self._browser.new_context(
                viewport={"width": 1280, "height": 800},
                accept_downloads=True,
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
            )
            self._page = self._context.new_page()

    def navigate(self, url: str, wait_until: str = "load", timeout_ms: int = 25000) -> Dict[str, Any]:
        """
        Navigates browser to target URL with reliable load wait.
        """
        t0 = time.time()
        try:
            self._ensure_browser()
            response = self._page.goto(url, wait_until=wait_until, timeout=timeout_ms)
            title = self._page.title()
            current_url = self._page.url
            status = response.status if response else 200

            duration = round(time.time() - t0, 2)
            return {
                "success": True,
                "action": "navigate",
                "requested_url": url,
                "current_url": current_url,
                "page_title": title,
                "status_code": status,
                "duration_s": duration,
                "verification": {
                    "verified": True,
                    "verification_type": "page_loaded",
                    "title": title,
                    "url": current_url
                }
            }
        except Exception as e:
            logger.error(f"Navigation to {url} failed: {e}")
            return {
                "success": False,
                "action": "navigate",
                "requested_url": url,
                "error": str(e)
            }

    def click(self, selector: str, name: Optional[str] = None, role: Optional[str] = None) -> Dict[str, Any]:
        """
        Clicks element using accessible role, text, or CSS selector with auto-wait.
        """
        try:
            self._ensure_browser()
            # 1. Accessible Role locator if provided
            if role and name:
                locator = self._page.get_by_role(role, name=name)
            elif name and not selector:
                locator = self._page.get_by_text(name, exact=False)
            else:
                # CSS / XPath / text selector
                locator = self._page.locator(selector).first

            locator.wait_for(state="visible", timeout=10000)
            locator.click(timeout=8000)

            return {
                "success": True,
                "action": "click",
                "target": name or selector,
                "current_url": self._page.url
            }
        except Exception as e:
            return {"success": False, "action": "click", "target": name or selector, "error": str(e)}

    def fill_form(self, selector_or_label: str, text: str, is_secret: bool = False) -> Dict[str, Any]:
        """
        Enters text into form field or input using accessible label, placeholder, or selector.
        Redacts secret values from logs to protect credentials.
        """
        try:
            self._ensure_browser()
            locator = None

            # Try by label
            try:
                l_cand = self._page.get_by_label(selector_or_label)
                if l_cand.count() > 0:
                    locator = l_cand.first
            except Exception:
                pass

            # Try by placeholder
            if locator is None:
                try:
                    p_cand = self._page.get_by_placeholder(selector_or_label)
                    if p_cand.count() > 0:
                        locator = p_cand.first
                except Exception:
                    pass

            # Try by name attribute or ID
            if locator is None and not any(ch in selector_or_label for ch in ["[", "#", ".", ">", ":", " "]):
                try:
                    name_cand = self._page.locator(f"[name='{selector_or_label}']")
                    if name_cand.count() > 0:
                        locator = name_cand.first
                except Exception:
                    pass
                if locator is None:
                    try:
                        id_cand = self._page.locator(f"#{selector_or_label}")
                        if id_cand.count() > 0:
                            locator = id_cand.first
                    except Exception:
                        pass

            # Fallback to direct locator
            if locator is None:
                locator = self._page.locator(selector_or_label).first

            locator.wait_for(state="visible", timeout=8000)
            locator.fill(text)

            log_val = "[PROTECTED_SECRET]" if is_secret else (text[:30] + "..." if len(text) > 30 else text)
            return {
                "success": True,
                "action": "fill_form",
                "field": selector_or_label,
                "input_preview": log_val
            }
        except Exception as e:
            return {"success": False, "action": "fill_form", "field": selector_or_label, "error": str(e)}

    def select_option(self, selector: str, value: str) -> Dict[str, Any]:
        """
        Selects an option from a dropdown element.
        """
        try:
            self._ensure_browser()
            locator = self._page.locator(selector).first
            locator.wait_for(state="visible", timeout=8000)
            res = locator.select_option(value=value)
            return {"success": True, "action": "select_option", "selected": res}
        except Exception as e:
            return {"success": False, "action": "select_option", "selector": selector, "error": str(e)}

    def download_file(self, trigger_selector: Optional[str] = None, direct_url: Optional[str] = None, target_dir: Optional[str] = None) -> Dict[str, Any]:
        """
        Tracks, initiates, and verifies a file download event via Playwright or direct HTTP.
        """
        t0 = time.time()
        downloads_folder = target_dir or os.path.expanduser("~/Downloads")
        os.makedirs(downloads_folder, exist_ok=True)

        try:
            self._ensure_browser()

            # Case A: Download initiated via click on page
            if trigger_selector:
                with self._page.expect_download(timeout=20000) as download_info:
                    self._page.locator(trigger_selector).first.click()
                download = download_info.value
                filename = download.suggested_filename
                dest_path = os.path.join(downloads_folder, filename)
                download.save_as(dest_path)
            
            # Case B: Download initiated via direct URL
            elif direct_url:
                parsed_name = os.path.basename(direct_url.split("?")[0]) or f"download_{int(time.time())}"
                dest_path = os.path.join(downloads_folder, parsed_name)
                resp = self._page.request.get(direct_url)
                if resp.ok:
                    with open(dest_path, "wb") as f:
                        f.write(resp.body())
                    filename = parsed_name
                else:
                    return {
                        "success": False,
                        "action": "download_file",
                        "error": f"Failed to download from {direct_url}: HTTP status {resp.status}"
                    }

            else:
                return {"success": False, "action": "download_file", "error": "Neither trigger_selector nor direct_url specified."}

            # Verification of downloaded file
            verif = AutomationVerifier.verify_file_exists(dest_path, min_size=1, timeout=5.0)
            return {
                "success": verif.get("verified", False),
                "action": "download_file",
                "filename": filename,
                "file_path": dest_path,
                "size_bytes": verif.get("size_bytes", 0),
                "duration_s": round(time.time() - t0, 2),
                "verification": verif
            }

        except Exception as e:
            logger.error(f"Download failed: {e}")
            return {"success": False, "action": "download_file", "error": str(e)}

    def capture_screenshot(self, output_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Captures a verification screenshot of the active browser viewport.
        """
        try:
            self._ensure_browser()
            path = output_path or os.path.join(os.path.expanduser("~"), f"ops_screenshot_{int(time.time())}.png")
            self._page.screenshot(path=path)
            return {
                "success": True,
                "action": "capture_screenshot",
                "screenshot_path": path,
                "verification": {"verified": os.path.exists(path)}
            }
        except Exception as e:
            return {"success": False, "action": "capture_screenshot", "error": str(e)}

    def close(self):
        """Cleans up Playwright resources."""
        try:
            if self._context:
                self._context.close()
            if self._browser:
                self._browser.close()
            if self._playwright:
                self._playwright.stop()
        except Exception:
            pass
        finally:
            self._page = None
            self._context = None
            self._browser = None
            self._playwright = None
