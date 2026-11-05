"""
O.P.S. 2.0 Browser Locator Engine
Technology: Playwright
Provides multi-strategy resilient element locators with accessibility-first priority:
1. Accessible Role & Name (e.g. role='button', name='Search')
2. Form Label (e.g. label='Password')
3. Placeholder (e.g. placeholder='Search YouTube')
4. Visible Text (exact or partial)
5. Test ID (e.g. data-testid='...')
6. CSS Selectors (with multi-selector fallbacks)
7. XPath
Includes auto-waits, visibility checks, enablement verification, and scroll-into-view.
"""

import logging
from typing import Optional, List, Dict, Any, Tuple
from playwright.sync_api import Page, Locator

logger = logging.getLogger("OPS.BrowserLocator")


class LocatorEngine:
    """
    Intelligent element locator with cascading fallback strategies.
    """

    @classmethod
    def find_element(
        cls,
        page: Page,
        role: Optional[str] = None,
        name: Optional[str] = None,
        label: Optional[str] = None,
        placeholder: Optional[str] = None,
        text: Optional[str] = None,
        test_id: Optional[str] = None,
        selector: Optional[str] = None,
        xpath: Optional[str] = None,
        timeout_ms: int = 5000
    ) -> Tuple[Optional[Locator], str]:
        """
        Attempts to locate an element using cascaded strategies in order of accessibility & stability.
        Returns (Locator, strategy_used).
        """
        # Strategy 1: Role and Name
        if role and name:
            try:
                loc = page.get_by_role(role, name=name).first
                if loc.is_visible(timeout=timeout_ms):
                    return loc, f"role('{role}', name='{name}')"
            except Exception:
                pass

        # Strategy 2: Label
        if label:
            try:
                loc = page.get_by_label(label, exact=False).first
                if loc.is_visible(timeout=timeout_ms):
                    return loc, f"label('{label}')"
            except Exception:
                pass

        # Strategy 3: Placeholder
        if placeholder:
            try:
                loc = page.get_by_placeholder(placeholder, exact=False).first
                if loc.is_visible(timeout=timeout_ms):
                    return loc, f"placeholder('{placeholder}')"
            except Exception:
                pass

        # Strategy 4: Test ID
        if test_id:
            try:
                loc = page.get_by_test_id(test_id).first
                if loc.is_visible(timeout=timeout_ms):
                    return loc, f"test_id('{test_id}')"
            except Exception:
                pass

        # Strategy 5: Visible Text
        if text:
            try:
                loc = page.get_by_text(text, exact=False).first
                if loc.is_visible(timeout=timeout_ms):
                    return loc, f"text('{text}')"
            except Exception:
                pass

        # Strategy 6: CSS Selector (single or comma-separated candidates)
        if selector:
            candidates = [s.strip() for s in selector.split(",") if s.strip()]
            for sel in candidates:
                try:
                    loc = page.locator(sel).first
                    if loc.is_visible(timeout=timeout_ms):
                        return loc, f"css('{sel}')"
                except Exception:
                    continue

        # Strategy 7: XPath
        if xpath:
            try:
                loc = page.locator(f"xpath={xpath}").first
                if loc.is_visible(timeout=timeout_ms):
                    return loc, f"xpath('{xpath}')"
            except Exception:
                pass

        # Fallback: Check if selector exists in DOM even if hidden
        if selector:
            try:
                loc = page.locator(selector).first
                return loc, f"css_dom('{selector}')"
            except Exception:
                pass

        return None, "none"

    @classmethod
    def ensure_interactable(cls, locator: Locator, timeout_ms: int = 5000) -> bool:
        """Verifies element is visible, enabled, and scrolls it into view if needed."""
        try:
            locator.scroll_into_view_if_needed(timeout=timeout_ms)
            return locator.is_visible(timeout=timeout_ms) and locator.is_enabled(timeout=timeout_ms)
        except Exception:
            return False
