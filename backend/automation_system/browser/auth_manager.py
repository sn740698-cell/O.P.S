"""
O.P.S. 2.0 Browser Authentication & Boundary Awareness Engine
Detects login screens, authentication walls, CAPTCHAs, and 2FA barriers
across major websites (Google, YouTube, Spotify, Instagram, Cloudflare).
Pauses execution honestly and formats clear Cockpit guidance without leaking
or guessing user credentials.
"""

import logging
from typing import Dict, Any, Tuple
from playwright.sync_api import Page

logger = logging.getLogger("OPS.BrowserAuth")


class AuthenticationManager:
    """
    Detects security gates, login screens, and verification walls.
    """

    @classmethod
    def inspect_auth_barriers(cls, page: Page) -> Dict[str, Any]:
        """
        Inspects the active page for authentication boundaries or bot checks.
        Returns a dict indicating whether an auth barrier is present.
        """
        url = page.url.lower()

        # 1. Cloudflare / Bot Verification Check
        cf_detected = cls._detect_captcha(page)
        if cf_detected:
            return {
                "auth_required": True,
                "barrier_type": "CAPTCHA_CHALLENGE",
                "service": "Security Gate",
                "message": "A bot verification challenge (CAPTCHA / Cloudflare) is present. Please solve the challenge in the browser window, then continue.",
                "url": page.url
            }

        # 2. Google / YouTube Auth Check
        if "accounts.google.com/signin" in url or "accounts.google.com/v3/signin" in url:
            return {
                "auth_required": True,
                "barrier_type": "GOOGLE_LOGIN_WALL",
                "service": "Google",
                "message": "Google authentication is required. Please sign into your Google account in the browser window.",
                "url": page.url
            }

        # YouTube bot check
        if "youtube.com" in url:
            try:
                bot_text = page.locator("text='Sign in to confirm you’re not a bot'").first
                if bot_text.is_visible(timeout=500):
                    return {
                        "auth_required": True,
                        "barrier_type": "YOUTUBE_BOT_VERIFICATION",
                        "service": "YouTube",
                        "message": "YouTube requires account sign-in to verify the session. Please sign in in the browser window.",
                        "url": page.url
                    }
            except Exception:
                pass

        # 3. Spotify Login Barrier Check
        if "spotify.com" in url:
            if "accounts.spotify.com/login" in url or "accounts.spotify.com/authorize" in url:
                return {
                    "auth_required": True,
                    "barrier_type": "SPOTIFY_LOGIN_WALL",
                    "service": "Spotify",
                    "message": "Spotify requires an active account to stream full tracks. Please log into Spotify in the browser window.",
                    "url": page.url
                }

        # 4. Instagram Login Barrier Check
        if "instagram.com" in url:
            if "accounts/login" in url or "accounts/emailsignup" in url:
                return {
                    "auth_required": True,
                    "barrier_type": "INSTAGRAM_LOGIN_WALL",
                    "service": "Instagram",
                    "message": "Instagram requires an active account session to view this content. Please log in in the browser window.",
                    "url": page.url
                }

            # Check for Instagram login popup dialog
            try:
                login_modal = page.locator("div[role='dialog']:has-text('Log In')").first
                if login_modal.is_visible(timeout=500):
                    return {
                        "auth_required": True,
                        "barrier_type": "INSTAGRAM_MODAL_BARRIER",
                        "service": "Instagram",
                        "message": "Instagram surfaced a login dialog. Please log into your account in the browser window.",
                        "url": page.url
                    }
            except Exception:
                pass

        return {
            "auth_required": False,
            "barrier_type": "NONE",
            "service": "Open",
            "message": "No active authentication barrier detected.",
            "url": page.url
        }

    @classmethod
    def _detect_captcha(cls, page: Page) -> bool:
        """Checks for common CAPTCHA / Cloudflare turnstile frames."""
        try:
            cf_frames = [
                "iframe[src*='challenges.cloudflare.com']",
                "iframe[src*='recaptcha']",
                "iframe[src*='hcaptcha.com']",
                "div#turnstile-wrapper",
                "div.g-recaptcha"
            ]
            for sel in cf_frames:
                if page.locator(sel).first.is_visible(timeout=400):
                    return True
        except Exception:
            pass
        return False
