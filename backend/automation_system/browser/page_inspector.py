"""
O.P.S. 2.0 Browser Page Inspector & Content Extractor
Extracts structured, concise summaries of the active browser viewport:
- Current URL and page title
- Prominent headings (H1, H2)
- Interactive buttons and inputs
- Login / authentication state
- Clean text preview (bounded to prevent context bloat)
"""

import logging
from typing import Dict, Any, List
from playwright.sync_api import Page
from automation_system.browser.auth_manager import AuthenticationManager

logger = logging.getLogger("OPS.BrowserPageInspector")


class PageInspector:
    """
    Produces structured summaries of active browser pages for decision-making.
    """

    @classmethod
    def inspect(cls, page: Page, max_text_chars: int = 1500) -> Dict[str, Any]:
        """
        Extracts structured page metadata without overloading context.
        """
        try:
            url = page.url
            title = page.title()

            # 1. Auth Boundary Check
            auth_info = AuthenticationManager.inspect_auth_barriers(page)

            # 2. Extract Headings
            headings: List[str] = []
            try:
                h_locs = page.locator("h1, h2")
                count = min(h_locs.count(), 6)
                for i in range(count):
                    txt = h_locs.nth(i).text_content() or ""
                    if txt.strip():
                        headings.append(txt.strip())
            except Exception:
                pass

            # 3. Extract Interactive Elements (Buttons & Inputs)
            buttons: List[str] = []
            try:
                b_locs = page.locator("button, a[role='button']")
                b_count = min(b_locs.count(), 8)
                for i in range(b_count):
                    txt = b_locs.nth(i).inner_text() or b_locs.nth(i).get_attribute("aria-label") or ""
                    clean = " ".join(txt.split()).strip()
                    if clean and len(clean) < 40 and clean not in buttons:
                        buttons.append(clean)
            except Exception:
                pass

            inputs: List[Dict[str, str]] = []
            try:
                inp_locs = page.locator("input:not([type='hidden']), textarea")
                inp_count = min(inp_locs.count(), 5)
                for i in range(inp_count):
                    el = inp_locs.nth(i)
                    p_hold = el.get_attribute("placeholder") or ""
                    name = el.get_attribute("name") or el.get_attribute("aria-label") or ""
                    i_type = el.get_attribute("type") or "text"
                    inputs.append({"type": i_type, "name": name, "placeholder": p_hold})
            except Exception:
                pass

            # 4. Text Preview
            text_preview = ""
            try:
                body_txt = page.locator("body").inner_text() or ""
                clean_lines = [line.strip() for line in body_txt.split("\n") if line.strip()]
                text_preview = " ".join(clean_lines)[:max_text_chars]
            except Exception:
                pass

            return {
                "success": True,
                "url": url,
                "title": title,
                "auth_state": auth_info,
                "headings": headings,
                "interactive_buttons": buttons[:6],
                "form_inputs": inputs,
                "text_preview": text_preview
            }

        except Exception as e:
            logger.error(f"Page inspection failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "url": getattr(page, "url", "")
            }
