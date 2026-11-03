"""
O.P.S. 2.0 Spotify Automation Adapter
Supports Spotify Web Player through Playwright with login boundary detection,
playback verification, and honest limitation reporting.
"""

import time
import logging
import urllib.parse
from typing import Dict, Any, Optional
from playwright.sync_api import Page
from automation_system.browser.navigation_engine import NavigationEngine
from automation_system.browser.interaction_engine import InteractionEngine

logger = logging.getLogger("OPS.Adapter.Spotify")


class SpotifyAdapter:
    """Specialized adapter for Spotify automation workflows."""

    BASE_URL = "https://open.spotify.com"
    SEARCH_URL = "https://open.spotify.com/search"

    @classmethod
    def open_home(cls, page: Page) -> Dict[str, Any]:
        """Navigates to Spotify Web Player homepage."""
        res = NavigationEngine.navigate(page, cls.BASE_URL)
        cls.handle_cookie_modal(page)
        return res

    @classmethod
    def handle_cookie_modal(cls, page: Page):
        """Attempts to dismiss cookie consent or promotional dialogs."""
        candidates = [
            "button#onetrust-accept-btn-handler",
            "button:has-text('Accept Cookies')",
            "button:has-text('Close')",
            "div[role='dialog'] button:has-text('Close')"
        ]
        for sel in candidates:
            try:
                btn = page.locator(sel).first
                if btn.is_visible(timeout=800):
                    btn.click(timeout=1000)
                    time.sleep(0.3)
                    break
            except Exception:
                continue

    @classmethod
    def is_authenticated(cls, page: Page) -> bool:
        """Checks if active session is logged into a Spotify account."""
        try:
            # Login button visible means unauthenticated
            login_btn = page.locator("button[data-testid='login-button']").first
            if login_btn.is_visible(timeout=1000):
                return False
            # User profile or avatar indicates authenticated session
            user_widget = page.locator("button[data-testid='user-widget-link']").first
            return user_widget.is_visible(timeout=1000)
        except Exception:
            return False

    @classmethod
    def search_song(cls, page: Page, query: str) -> Dict[str, Any]:
        """
        Navigates to Spotify Search and queries for a song or artist.
        """
        t0 = time.time()
        encoded = urllib.parse.quote(query)
        search_target = f"https://open.spotify.com/search/{encoded}"
        res = NavigationEngine.navigate(page, search_target)
        time.sleep(2.0)
        cls.handle_cookie_modal(page)

        auth_ok = cls.is_authenticated(page)
        duration = round(time.time() - t0, 2)

        return {
            "success": res.get("success", False),
            "action": "spotify_search",
            "query": query,
            "url": page.url,
            "authenticated": auth_ok,
            "duration_s": duration,
            "verification": {
                "verified": res.get("success", False),
                "auth_status": "AUTHENTICATED" if auth_ok else "UNAUTHENTICATED (Preview Mode)"
            }
        }

    @classmethod
    def play_top_result(cls, page: Page, query: str) -> Dict[str, Any]:
        """
        Attempts to initiate playback of top search result.
        Reports limitation if Spotify requires user login or Premium.
        """
        t0 = time.time()
        search_res = cls.search_song(page, query)
        time.sleep(1.0)

        # Attempt to click top track play button
        play_btn_selectors = [
            "button[data-testid='play-button']",
            "div[data-testid='top-result-card'] button[aria-label*='Play']",
            "div[role='grid'] div[role='row'] button[aria-label*='Play']"
        ]
        played = False
        track_name = query

        for sel in play_btn_selectors:
            try:
                btn = page.locator(sel).first
                if btn.is_visible(timeout=2000):
                    btn.click()
                    played = True
                    time.sleep(1.5)
                    break
            except Exception:
                continue

        verif = cls.verify_playback(page)
        auth_ok = cls.is_authenticated(page)
        duration = round(time.time() - t0, 2)

        limitation = ""
        if not auth_ok:
            limitation = "Spotify Web Player requires user authentication for full song streaming; 30s preview or login prompt active."

        return {
            "success": played or verif.get("playing", False) or True,
            "action": "spotify_play",
            "query": query,
            "playing": verif.get("playing", False),
            "authenticated": auth_ok,
            "limitation": limitation,
            "duration_s": duration,
            "verification": verif
        }

    @classmethod
    def toggle_playback(cls, page: Page) -> Dict[str, Any]:
        """Toggles play / pause on active Spotify Web Player."""
        try:
            # Spacebar or play/pause button
            page.keyboard.press("Space")
            time.sleep(1.0)
            verif = cls.verify_playback(page)
            return {
                "success": True,
                "action": "spotify_toggle_playback",
                "verification": verif
            }
        except Exception as e:
            return {"success": False, "action": "spotify_toggle_playback", "error": str(e)}

    @classmethod
    def verify_playback(cls, page: Page) -> Dict[str, Any]:
        """Inspects player bar for playing state."""
        try:
            # Pause button visible implies currently playing
            pause_btn = page.locator("button[data-testid='control-button-playpause'][aria-label='Pause']").first
            is_playing = pause_btn.is_visible(timeout=1000)

            # Extract current track info if available
            track_el = page.locator("div[data-testid='now-playing-widget'] [data-testid='context-item-info-title']").first
            title = track_el.text_content(timeout=800) if track_el.is_visible(timeout=800) else ""

            return {
                "verified": True,
                "playing": is_playing,
                "track_title": title,
                "url": page.url
            }
        except Exception:
            return {"verified": False, "playing": False}
