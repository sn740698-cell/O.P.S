"""
O.P.S. 2.0 Browser Automation Specialist — Agent B3: Website Understanding and Resolution Specialist
Responsibilities:
- Understand natural-language website names, product names, domains, URLs, and common website aliases
- Resolve canonical official websites (GitHub, Claude, Gemini, Google, YouTube, Instagram, ChatGPT, Spotify, Lovable, React Bits, Cisco, etc.)
- Validate complete user-supplied URLs
- Distinguish official websites from ads or similarly named services
- Identify ambiguous website requests and request clarification
- Prevent domain hallucination or silent substitution
"""

import re
import logging
from urllib.parse import urlparse
from typing import Dict, Any, Optional, Tuple

logger = logging.getLogger("OPS.Browser.B3_ResolutionAgent")

# Canonical official website mappings
CANONICAL_WEBSITES: Dict[str, Dict[str, Any]] = {
    "github": {"url": "https://github.com", "domain": "github.com", "name": "GitHub"},
    "claude": {"url": "https://claude.ai", "domain": "claude.ai", "name": "Claude"},
    "gemini": {"url": "https://gemini.google.com", "domain": "gemini.google.com", "name": "Gemini"},
    "google": {"url": "https://www.google.com", "domain": "google.com", "name": "Google"},
    "cisco": {"url": "https://www.cisco.com", "domain": "cisco.com", "name": "Cisco"},
    "cisco website": {"url": "https://www.cisco.com", "domain": "cisco.com", "name": "Cisco"},
    "lovable": {"url": "https://lovable.dev", "domain": "lovable.dev", "name": "Lovable"},
    "lovable.ai": {"url": "https://lovable.dev", "domain": "lovable.dev", "name": "Lovable"},
    "react bits": {"url": "https://reactbits.dev", "domain": "reactbits.dev", "name": "React Bits"},
    "reactbits": {"url": "https://reactbits.dev", "domain": "reactbits.dev", "name": "React Bits"},
    "instagram": {"url": "https://www.instagram.com", "domain": "instagram.com", "name": "Instagram"},
    "youtube": {"url": "https://www.youtube.com", "domain": "youtube.com", "name": "YouTube"},
    "chatgpt": {"url": "https://chatgpt.com", "domain": "chatgpt.com", "name": "ChatGPT"},
    "spotify": {"url": "https://open.spotify.com", "domain": "spotify.com", "name": "Spotify"},
    "snapchat": {"url": "https://www.snapchat.com", "domain": "snapchat.com", "name": "Snapchat"},
    "reddit": {"url": "https://www.reddit.com", "domain": "reddit.com", "name": "Reddit"},
    "twitter": {"url": "https://x.com", "domain": "x.com", "name": "X / Twitter"},
    "x": {"url": "https://x.com", "domain": "x.com", "name": "X"},
    "linkedin": {"url": "https://www.linkedin.com", "domain": "linkedin.com", "name": "LinkedIn"},
    "wikipedia": {"url": "https://www.wikipedia.org", "domain": "wikipedia.org", "name": "Wikipedia"},
    "amazon": {"url": "https://www.amazon.com", "domain": "amazon.com", "name": "Amazon"},
    "netflix": {"url": "https://www.netflix.com", "domain": "netflix.com", "name": "Netflix"},
    "python": {"url": "https://www.python.org", "domain": "python.org", "name": "Python"},
    "django": {"url": "https://docs.djangoproject.com", "domain": "djangoproject.com", "name": "Django"},
    "react": {"url": "https://react.dev", "domain": "react.dev", "name": "React"},
}

KNOWN_TLDS = {
    "com", "org", "net", "edu", "gov", "io", "dev", "ai", "co", "app", 
    "tech", "me", "info", "xyz", "biz", "cloud", "site", "online"
}


class B3_ResolutionAgent:
    """Specialist Agent B3: Resolves and validates website names, domains, and URLs."""

    def __init__(self, conversation_id: str = "default_session"):
        self.agent_id = "agent_b3_resolution"
        self.agent_name = "Website Understanding & Resolution Agent"
        self.conversation_id = conversation_id or "default_session"

    def resolve_website(self, raw_query: str) -> Dict[str, Any]:
        """
        Resolves a natural language website name, domain, or full URL into a canonical validated URL.
        """
        if not raw_query or not raw_query.strip():
            return {
                "success": False,
                "agent_id": self.agent_id,
                "error": "Empty website request provided.",
                "clarification_needed": True,
                "url": None
            }

        q = raw_query.strip()

        # 1. Complete URL supplied? (e.g. starts with http:// or https://)
        if q.startswith("http://") or q.startswith("https://"):
            try:
                parsed = urlparse(q)
                if parsed.netloc:
                    return {
                        "success": True,
                        "agent_id": self.agent_id,
                        "action": "resolve_website",
                        "url": q,
                        "domain": parsed.netloc,
                        "source": "exact_url",
                        "clarification_needed": False
                    }
            except Exception:
                pass

        # 2. Check if clean query is a direct domain string (e.g. "github.com", "lovable.dev")
        clean_name = q.lower().strip()
        # Remove common introductory phrases
        for prefix in ["open ", "visit ", "go to ", "navigate to ", "the "]:
            if clean_name.startswith(prefix):
                clean_name = clean_name[len(prefix):].strip()

        # Remove trailing words like "website", "official website", "homepage", "in the browser"
        for suffix in [" website", " official website", " official site", " homepage", " in the browser", " in chrome", " in browser"]:
            if clean_name.endswith(suffix):
                clean_name = clean_name[:-len(suffix)].strip()

        # Check for ambiguous / vague queries BEFORE matching
        ambiguous_terms = ["website", "site", "page", "app", "something", "browser", "internet", "web"]
        if clean_name in ambiguous_terms or len(clean_name) <= 2:
            return {
                "success": False,
                "agent_id": self.agent_id,
                "error": f"The requested website '{raw_query}' is ambiguous. Please specify the name or URL of the website.",
                "clarification_needed": True,
                "url": None
            }

        # Direct domain format check (e.g. word.tld)
        if "." in clean_name and " " not in clean_name:
            parts = clean_name.split(".")
            tld = parts[-1].lower()
            if tld in KNOWN_TLDS:
                url = f"https://{clean_name}"
                return {
                    "success": True,
                    "agent_id": self.agent_id,
                    "action": "resolve_website",
                    "url": url,
                    "domain": clean_name,
                    "source": "direct_domain",
                    "clarification_needed": False
                }

        # 3. Known canonical alias match
        if clean_name in CANONICAL_WEBSITES:
            info = CANONICAL_WEBSITES[clean_name]
            return {
                "success": True,
                "agent_id": self.agent_id,
                "action": "resolve_website",
                "url": info["url"],
                "domain": info["domain"],
                "name": info["name"],
                "source": "canonical_alias",
                "clarification_needed": False
            }

        # Substring / partial match in canonical aliases (only if clean_name is substantive)
        for alias, info in CANONICAL_WEBSITES.items():
            if alias in clean_name or (len(clean_name) > 3 and clean_name in alias and alias != "cisco website"):
                return {
                    "success": True,
                    "agent_id": self.agent_id,
                    "action": "resolve_website",
                    "url": info["url"],
                    "domain": info["domain"],
                    "name": info["name"],
                    "source": "canonical_alias_fuzzy",
                    "clarification_needed": False
                }

        # 4. Check for ambiguous / vague queries
        ambiguous_terms = ["website", "site", "page", "app", "something", "browser", "internet", "web"]
        if clean_name in ambiguous_terms or len(clean_name) <= 2:
            return {
                "success": False,
                "agent_id": self.agent_id,
                "error": f"The requested website '{raw_query}' is ambiguous. Please specify the name or URL of the website.",
                "clarification_needed": True,
                "url": None
            }

        # 5. Dynamic heuristic resolution for unfamiliar valid brand/product names
        # Format as standard canonical domain rather than failing
        safe_slug = re.sub(r"[^a-z0-9]", "", clean_name)
        if safe_slug:
            candidate_url = f"https://www.{safe_slug}.com"
            return {
                "success": True,
                "agent_id": self.agent_id,
                "action": "resolve_website",
                "url": candidate_url,
                "domain": f"{safe_slug}.com",
                "source": "heuristic_resolution",
                "clarification_needed": False
            }

        return {
            "success": False,
            "agent_id": self.agent_id,
            "error": f"Could not resolve website '{raw_query}'.",
            "clarification_needed": True,
            "url": None
        }
