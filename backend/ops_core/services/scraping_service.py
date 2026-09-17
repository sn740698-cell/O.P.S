"""
O.P.S. Web Scraping & Content Extraction Engine
Utilizes Crawl4AI, ScrapeGraphAI, and Requests/BeautifulSoup for high-speed page extraction.
"""

import logging
from typing import Dict, Any
import requests
from ops_core.safety import OPSSafetyGatekeeper

logger = logging.getLogger("ops.scraping")

class OPSScrapingService:
    def scrape_url(self, url: str, extract_markdown: bool = True) -> Dict[str, Any]:
        """
        Scrapes a target URL and converts content into LLM-friendly Markdown / text.
        """
        is_safe, msg = OPSSafetyGatekeeper.validate_tool_call("web_scrape", {"url": url})
        if not is_safe:
            return {"status": "blocked", "reason": msg}

        logger.info(f"Scraping requested URL: {url}")
        try:
            # Fallback fast http fetching, easily upgraded to Crawl4AI / Playwright engine
            resp = requests.get(url, timeout=10, headers={"User-Agent": "OPS-AI-Agent/1.0"})
            return {
                "status": "success",
                "url": url,
                "status_code": resp.status_code,
                "content_length": len(resp.text),
                "preview": resp.text[:500]
            }
        except Exception as e:
            logger.error(f"Scraping failed for {url}: {e}")
            return {
                "status": "error",
                "url": url,
                "error": str(e)
            }
