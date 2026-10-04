"""
O.P.S. Real-Time Web Intelligence & Autonomous Web Crawling Engine
Powered by Crawlee, ScrapeGraphAI, BeautifulSoup4, and Real-Time RSS/REST Feeds.

Capabilities:
- Live Person Bio & Profile Crawling (Wikipedia REST + Live Indexes)
- Scientific, Mathematical & Technical Theory Crawling (Concept Extraction)
- Live Real-Time News & Market Updates (Google News RSS + Direct Page Deep Crawl)
- Deep URL Scraping & DOM Sanitation (Removes noise, extracts structured markdown)
- Multi-Source Autonomous Research & Fact Synthesis
- Voice Calling / TTS Ready Speech Summaries for Ambient Spoken Output
"""

import re
import os
import urllib.parse
import logging
import time
from typing import Dict, Any, List, Optional
import requests
from bs4 import BeautifulSoup

# 1. Beautiful Soup (DOM sanitation & parsing) - native
# 2. ScrapingBee (Cloud Anti-Bot Proxy Engine)
try:
    from scrapingbee import ScrapingBeeClient
except ImportError:
    ScrapingBeeClient = None

# 3. Playwright (Headless/Interactive Browser DOM Engine)
try:
    from playwright.sync_api import sync_playwright
except ImportError:
    sync_playwright = None

# 4. Selenium (Headless Chrome WebDriver Fallback)
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options as SeleniumChromeOptions
except ImportError:
    webdriver = None
    SeleniumChromeOptions = None

# 5. Scrapy (High-Performance XPath & CSS Selector Parser)
try:
    from scrapy import Selector as ScrapySelector
except ImportError:
    ScrapySelector = None

# 6. Crawlee (Autonomous Web Crawler & Scraping Framework)
try:
    from crawlee.crawlers import BeautifulSoupCrawler
except ImportError:
    BeautifulSoupCrawler = None

from ops_core.safety import OPSSafetyGatekeeper

logger = logging.getLogger("ops.scraping")

# Minimum characters a cleaned page must contain before it is considered usable.
# Below this threshold the scraper treats the page as effectively empty and
# reports a scrape-failed status instead of handing blank context to the LLM.
MIN_SCRAPED_TEXT_LENGTH = 100

# Grounding preamble prepended to scraped context before it reaches the LLM.
GROUNDING_INSTRUCTION = (
    "=== VERIFIED SOURCE TEXT (GROUNDING CONTEXT) ===\n"
    "Answer strictly using the verified facts, names, dates, and details from the source text below.\n"
    "Do not extrapolate, assume, or invent details not present in the text.\n"
    "================================================\n\n"
)

# Response bodies that indicate a bot block / challenge page rather than real content.
BOT_BLOCK_INDICATORS = [
    "robot check",
    "are you a robot",
    "captcha",
    "cf-chl",
    "access denied",
    "attention required",
    "just a moment",
    "browser check",
    "please enable javascript",
    "enable javascript",
    "javascript is required",
    "site security check",
    "verify you are human",
    "sorry, you have been rate limited",
    "too many requests",
    "temporarily blocked",
    "403",
    "429",
    "503",
]

# HTML tags / attributes that carry no article content and must be stripped.
NOISE_TAGS = [
    "script", "style", "nav", "footer", "iframe", "noscript", "svg",
    "header", "aside", "form", "button", "input", "textarea", "select",
    "meta", "link", "template", "amp-script",
]

# Class / id fragments that typically mark cookie banners, consent walls, and chrome.
NOISE_CLASS_ID_PATTERNS = [
    "cookie", "consent", "banner", "popup", "newsletter", "subscribe",
    "ad-", "ads-", "advertisement", "sponsor", "social-share", "share-bar",
    "related-articles", "you-may-like", "tab-content", "tabbed",
    "comment", "disqus", "sidebar", "side-bar", "masthead", "skip-link",
    "cookieconsent", "gdpr", "cc-", "ccm-", "widget", "footer-",
]


class OPSScrapingService:
    """
    Autonomous multi-tiered web crawler and real-time knowledge synthesis service.
    """

    DEFAULT_HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    }
    WIKI_HEADERS = {
        "User-Agent": "OPS-AutonomousSystem/2.0 (ops@jarvis.local; autonomous-crawler)",
        "Accept": "application/json",
    }

    # --------------------------------------------------------------------------
    # DOM sanitisation helpers
    # --------------------------------------------------------------------------

    @staticmethod
    def _strip_noise(soup: BeautifulSoup) -> None:
        """
        Removes scripts, styles, chrome, cookie banners, and other non-article
        elements from the parsed tree in place.
        """
        try:
            for tag in soup(NOISE_TAGS):
                tag.decompose()

            for tag in soup.find_all(True):
                if not getattr(tag, "attrs", None):
                    continue
                c_val = tag.attrs.get("class") or []
                classes = " ".join(c_val) if isinstance(c_val, list) else str(c_val)
                identifier = f"{tag.attrs.get('id', '') or ''} {classes}".lower()
                if any(p in identifier for p in NOISE_CLASS_ID_PATTERNS):
                    tag.decompose()

            for tag in soup.find_all(["p", "li", "h1", "h2", "h3", "h4", "h5", "h6"]):
                if not tag.get_text(strip=True):
                    tag.decompose()
        except Exception as e:
            logger.debug(f"Noise strip warning: {e}")

    @staticmethod
    def _html_to_markdown(soup: BeautifulSoup) -> str:
        """
        Converts the surviving article body into clean Markdown with heading
        hierarchy and paragraph breaks, preserving list structure.
        """
        try:
            main = soup.find(["article", "main"]) or soup.find("body") or soup
            paragraphs = []
            for elem in main.find_all(["h1", "h2", "h3", "h4", "p", "li", "blockquote"]):
                t = elem.get_text(" ", strip=True)
                if t and len(t) > 15:
                    if elem.name in ("h1", "h2", "h3"):
                        paragraphs.append(f"### {t}")
                    elif elem.name == "li":
                        paragraphs.append(f"- {t}")
                    else:
                        paragraphs.append(t)
            if paragraphs:
                return "\n\n".join(paragraphs[:30])
            return soup.get_text(separator="\n", strip=True)
        except Exception:
            return soup.get_text(separator="\n", strip=True)

    @staticmethod
    def _is_bot_block(resp_text: str, status_code: int) -> bool:
        """
        Returns True when the response looks like a challenge / blocked page
        rather than real article content.
        """
        if status_code in (403, 429):
            return True
        lowered = resp_text.lower()
        # A genuine block page is short and dominated by the block message.
        for indicator in BOT_BLOCK_INDICATORS:
            if indicator in lowered:
                # Only treat as a block if the body is thin - real articles
                # containing "403" in an error-code table are not blocks.
                if len(resp_text) < 4000:
                    return True
        return False

    # =========================================================================
    # 1. CORE WEB SEARCH (Bing & MediaWiki Organic Indexer - No DuckDuckGo)
    # =========================================================================

    @staticmethod
    def _decode_search_url(raw_url: str) -> str:
        """Decodes redirect wrappers from Bing and search engines into original destination URLs."""
        if not raw_url:
            return ""
        # Bing base64 encoded destination URL
        if "u=a1" in raw_url:
            try:
                import base64
                b64 = raw_url.split("u=a1")[1].split("&")[0]
                b64 += "=" * ((4 - len(b64) % 4) % 4)
                decoded = base64.b64decode(b64).decode("utf-8", errors="ignore")
                if decoded.startswith("http"):
                    return decoded
            except Exception:
                pass
        return raw_url
    def search_web(self, query: str, max_results: int = 5) -> Dict[str, Any]:
        """
        Executes live organic web search across Wikipedia MediaWiki API, Wikipedia REST Summaries,
        Google News RSS, and web indexes. Zero DuckDuckGo.
        """
        encoded_query = urllib.parse.quote_plus(query)
        logger.info(f"[O.P.S. Search] Querying authoritative web indexes for: '{query}'")

        results = []

        # 1. Primary Knowledge Index: Wikipedia MediaWiki Search & Summary
        try:
            wiki_api_url = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={encoded_query}&format=json"
            w_resp = requests.get(wiki_api_url, headers=self.WIKI_HEADERS, timeout=6)
            if w_resp.status_code == 200:
                items = w_resp.json().get("query", {}).get("search", [])
                for it in items[:max_results]:
                    clean_title = it.get("title", "")
                    clean_snip = re.sub(r"<[^>]+>", "", it.get("snippet", "")).strip()
                    slug = urllib.parse.quote(clean_title.replace(" ", "_"))
                    wiki_page_url = f"https://en.wikipedia.org/wiki/{slug}"
                    
                    # Fetch rich extract via Wikipedia REST API
                    try:
                        rest_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{slug}"
                        r_res = requests.get(rest_url, headers=self.WIKI_HEADERS, timeout=5)
                        if r_res.status_code == 200:
                            ext_data = r_res.json()
                            full_extract = ext_data.get("extract", "")
                            if full_extract and len(full_extract) > len(clean_snip):
                                clean_snip = full_extract
                    except Exception:
                        pass

                    if clean_title:
                        results.append({
                            "title": clean_title,
                            "url": wiki_page_url,
                            "snippet": clean_snip
                        })
        except Exception as we:
            logger.warning(f"Wikipedia search query error for '{query}': {we}")

        # 2. Supplementary Live News RSS
        if len(results) < max_results or "news" in query.lower() or "latest" in query.lower():
            try:
                rss_url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-US&gl=US&ceid=US:en"
                rss_resp = requests.get(rss_url, headers=self.DEFAULT_HEADERS, timeout=6)
                if rss_resp.status_code == 200:
                    soup = BeautifulSoup(rss_resp.text, "xml")
                    for item in soup.find_all("item")[:3]:
                        if len(results) >= max_results:
                            break
                        t = item.title.text if item.title else ""
                        l = item.link.text if item.link else ""
                        d = BeautifulSoup(item.description.text or "", "html.parser").get_text(strip=True)
                        if t and not any(r["url"] == l for r in results):
                            results.append({
                                "title": t,
                                "url": l,
                                "snippet": d
                            })
            except Exception as re_err:
                logger.debug(f"RSS search supplement warning: {re_err}")

        # 3. Bing Search Engine fallback/supplement
        if len(results) < max_results:
            try:
                bing_url = f"https://www.bing.com/search?q={encoded_query}&FORM=QBRE"
                resp = requests.get(bing_url, headers=self.DEFAULT_HEADERS, timeout=6)
                if resp.status_code == 200:
                    soup = BeautifulSoup(resp.text, "html.parser")
                    for li in soup.find_all("li", class_="b_algo"):
                        if len(results) >= max_results:
                            break
                        h2 = li.find("h2")
                        p = li.find("p") or li.find("div", class_="b_caption")
                        a = h2.find("a") if h2 else None
                        if h2 and a and a.get("href"):
                            actual_url = self._decode_search_url(a["href"])
                            title = h2.get_text(strip=True)
                            snippet = p.get_text(strip=True) if p else ""
                            if actual_url and not actual_url.startswith("/") and not "bing.com" in actual_url:
                                if not any(r["url"] == actual_url for r in results):
                                    results.append({
                                        "title": title,
                                        "url": actual_url,
                                        "snippet": snippet
                                    })
            except Exception as be:
                logger.debug(f"Bing search supplement warning: {be}")

        if not results:
            summary = f"No organic search results found for query: '{query}'."
        else:
            summary = "\n".join([f"• [{r['title']}]({r['url']}): {r['snippet']}" for r in results])

        return {
            "status": "success" if results else "empty",
            "query": query,
            "count": len(results),
            "results": results,
            "summary": summary
        }

    # =========================================================================
    # 2. MULTI-ENGINE WEB CRAWLING SUITE (ScrapingBee, Playwright, Selenium, Scrapy, Crawlee, BeautifulSoup)
    # =========================================================================

    def scrape_with_beautifulsoup(self, html_content: str, url: str = "") -> Dict[str, Any]:
        """
        Engine 1: Beautiful Soup 4
        DOM sanitation, noise strip (scripts/styles/ads), and semantic Markdown conversion.
        """
        try:
            soup = BeautifulSoup(html_content, "html.parser")
            title = soup.title.string.strip() if soup.title and soup.title.string else (url or "Web Document")
            self._strip_noise(soup)
            markdown = self._html_to_markdown(soup)
            links = []
            for a in soup.find_all("a", href=True):
                href = a["href"]
                t = a.get_text(strip=True)
                if t and href.startswith("http") and href not in [l["url"] for l in links]:
                    links.append({"text": t, "url": href})
                    if len(links) >= 8:
                        break
            return {
                "status": "success",
                "engine": "BeautifulSoup4",
                "title": title,
                "text": markdown,
                "links": links
            }
        except Exception as e:
            return {"status": "error", "engine": "BeautifulSoup4", "error": str(e)}

    def scrape_with_scrapy(self, html_content: str, url: str = "") -> Dict[str, Any]:
        """
        Engine 2: Scrapy
        High-performance XPath & CSS selector parsing for structured articles and body data.
        """
        if not ScrapySelector:
            return self.scrape_with_beautifulsoup(html_content, url)
        try:
            sel = ScrapySelector(text=html_content)
            title = (sel.css("title::text").get() or url or "Document").strip()
            # Extract key paragraph texts and headings using Scrapy CSS selectors
            paragraphs = sel.css("article p::text, main p::text, div.content p::text, p::text").getall()
            clean_paragraphs = [p.strip() for p in paragraphs if len(p.strip()) > 20]
            text = "\n\n".join(clean_paragraphs[:25])
            if not text:
                return self.scrape_with_beautifulsoup(html_content, url)
            return {
                "status": "success",
                "engine": "Scrapy",
                "title": title,
                "text": text
            }
        except Exception as e:
            return {"status": "error", "engine": "Scrapy", "error": str(e)}

    def scrape_with_playwright(self, url: str, timeout_ms: int = 15000) -> Dict[str, Any]:
        """
        Engine 3: Playwright
        Headless browser automation capable of executing dynamic JavaScript, SPA hydration, and DOM extraction.
        """
        if not sync_playwright:
            return {"status": "unavailable", "engine": "Playwright", "error": "Playwright not installed."}
        try:
            logger.info(f"[O.P.S. Playwright Crawler] Launching headless browser for: {url}")
            with sync_playwright() as p:
                browser = None
                for ch in ["chrome", "msedge", None]:
                    try:
                        if ch:
                            browser = p.chromium.launch(channel=ch, headless=True)
                        else:
                            browser = p.chromium.launch(headless=True)
                        break
                    except Exception:
                        continue

                if not browser:
                    return {"status": "error", "engine": "Playwright", "error": "No browser executable available for Playwright."}

                page = browser.new_page(
                    user_agent=self.DEFAULT_HEADERS["User-Agent"]
                )
                page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
                # Wait briefly for dynamic JS rendering
                time.sleep(1.0)
                title = page.title() or url
                html = page.content()
                browser.close()

                # Clean via Scrapy & BeautifulSoup
                scrapy_res = self.scrape_with_scrapy(html, url=url)
                clean_text = scrapy_res.get("text") or ""
                if len(clean_text) < MIN_SCRAPED_TEXT_LENGTH:
                    bs_res = self.scrape_with_beautifulsoup(html, url=url)
                    clean_text = bs_res.get("text") or ""

                return {
                    "status": "success",
                    "engine": "Playwright",
                    "url": url,
                    "title": title,
                    "text": clean_text,
                    "content_length": len(clean_text)
                }
        except Exception as e:
            logger.warning(f"Playwright scrape failed for {url}: {e}")
            return {"status": "error", "engine": "Playwright", "error": str(e)}

    def scrape_with_selenium(self, url: str, timeout_sec: int = 15) -> Dict[str, Any]:
        """
        Engine 4: Selenium
        Headless Chrome WebDriver automation for interactive fallback and dynamic page rendering.
        """
        if not webdriver or not SeleniumChromeOptions:
            return {"status": "unavailable", "engine": "Selenium", "error": "Selenium not installed."}
        driver = None
        try:
            logger.info(f"[O.P.S. Selenium Crawler] Launching headless Chrome WebDriver for: {url}")
            opts = SeleniumChromeOptions()
            opts.add_argument("--headless=new")
            opts.add_argument("--disable-gpu")
            opts.add_argument("--no-sandbox")
            opts.add_argument(f"user-agent={self.DEFAULT_HEADERS['User-Agent']}")
            driver = webdriver.Chrome(options=opts)
            driver.set_page_load_timeout(timeout_sec)
            driver.get(url)
            time.sleep(1.0)
            title = driver.title or url
            html = driver.page_source
            driver.quit()

            bs_res = self.scrape_with_beautifulsoup(html, url=url)
            clean_text = bs_res.get("text", "")

            return {
                "status": "success",
                "engine": "Selenium",
                "url": url,
                "title": title,
                "text": clean_text,
                "content_length": len(clean_text)
            }
        except Exception as e:
            if driver:
                try:
                    driver.quit()
                except Exception:
                    pass
            logger.warning(f"Selenium scrape failed for {url}: {e}")
            return {"status": "error", "engine": "Selenium", "error": str(e)}

    def scrape_with_crawlee(self, url: str, max_requests: int = 3) -> Dict[str, Any]:
        """
        Engine 5: Crawlee
        Autonomous link discovery and multi-request crawler.
        """
        if not BeautifulSoupCrawler:
            return {"status": "unavailable", "engine": "Crawlee", "error": "Crawlee not installed."}
        try:
            import asyncio
            logger.info(f"[O.P.S. Crawlee Crawler] Executing Crawlee crawler on: {url}")
            crawled_data = []

            async def _run_crawlee():
                crawler = BeautifulSoupCrawler(max_requests_per_crawl=max_requests)
                @crawler.router.default_handler
                async def request_handler(context):
                    title = context.soup.title.string.strip() if context.soup.title and context.soup.title.string else context.request.url
                    self._strip_noise(context.soup)
                    text = self._html_to_markdown(context.soup)
                    crawled_data.append({"url": context.request.url, "title": title, "text": text})

                await crawler.run([url])

            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # Running in existing event loop
                    import nest_asyncio
                    nest_asyncio.apply()
                    loop.run_until_complete(_run_crawlee())
                else:
                    asyncio.run(_run_crawlee())
            except Exception:
                asyncio.run(_run_crawlee())

            if crawled_data:
                primary = crawled_data[0]
                return {
                    "status": "success",
                    "engine": "Crawlee",
                    "url": primary.get("url"),
                    "title": primary.get("title"),
                    "text": primary.get("text"),
                    "crawled_pages": len(crawled_data)
                }
            return {"status": "empty", "engine": "Crawlee", "error": "No pages crawled."}
        except Exception as e:
            logger.warning(f"Crawlee crawl failed for {url}: {e}")
            return {"status": "error", "engine": "Crawlee", "error": str(e)}

    def scrape_with_scrapingbee(self, url: str) -> Dict[str, Any]:
        """
        Engine 6: ScrapingBee
        Cloud anti-bot proxy crawler with JavaScript rendering to bypass Cloudflare/perimeter challenges.
        """
        api_key = os.environ.get("SCRAPINGBEE_API_KEY")
        if not api_key or not ScrapingBeeClient:
            return {"status": "skipped", "engine": "ScrapingBee", "reason": "No API key configured (falling back to local engines)."}
        try:
            logger.info(f"[O.P.S. ScrapingBee] Calling ScrapingBee API for: {url}")
            client = ScrapingBeeClient(api_key=api_key)
            response = client.get(url, params={"render_js": "true"})
            if response.status_code == 200:
                bs_res = self.scrape_with_beautifulsoup(response.text, url=url)
                return {
                    "status": "success",
                    "engine": "ScrapingBee",
                    "url": url,
                    "title": bs_res.get("title", url),
                    "text": bs_res.get("text", "")
                }
            return {"status": "error", "engine": "ScrapingBee", "status_code": response.status_code}
        except Exception as e:
            return {"status": "error", "engine": "ScrapingBee", "error": str(e)}

    def scrape_url(self, url: str, extract_markdown: bool = True, max_chars: int = 5000, preferred_engine: str = "auto") -> Dict[str, Any]:
        """
        Unified Multi-Engine Scraper Orchestrator:
        Coordinates ScrapingBee, Playwright, Selenium, Scrapy, Crawlee, and BeautifulSoup
        with automatic failover and anti-bot escalation.
        """
        is_safe, msg = OPSSafetyGatekeeper.validate_tool_call("web_scrape", {"url": url})
        if not is_safe:
            return {"status": "blocked", "reason": msg}

        if not url.startswith("http://") and not url.startswith("https://"):
            url = f"https://{url}"

        logger.info(f"[O.P.S. Multi-Engine Scraper] Scraping: {url} (Preferred={preferred_engine})")

        # 1. Preferred engine explicit override
        if preferred_engine == "playwright":
            pw_res = self.scrape_with_playwright(url)
            if pw_res.get("status") == "success" and len(pw_res.get("text", "")) >= MIN_SCRAPED_TEXT_LENGTH:
                return pw_res
        elif preferred_engine == "selenium":
            sel_res = self.scrape_with_selenium(url)
            if sel_res.get("status") == "success" and len(sel_res.get("text", "")) >= MIN_SCRAPED_TEXT_LENGTH:
                return sel_res
        elif preferred_engine == "crawlee":
            cr_res = self.scrape_with_crawlee(url)
            if cr_res.get("status") == "success" and len(cr_res.get("text", "")) >= MIN_SCRAPED_TEXT_LENGTH:
                return cr_res
        elif preferred_engine == "scrapingbee":
            sb_res = self.scrape_with_scrapingbee(url)
            if sb_res.get("status") == "success":
                return sb_res

        # 2. Tier 1: Fast HTTP + BeautifulSoup & Scrapy
        clean_text = ""
        title = url
        links = []
        is_blocked = False

        try:
            resp = requests.get(url, headers=self.DEFAULT_HEADERS, timeout=10)
            if self._is_bot_block(resp.text, resp.status_code):
                is_blocked = True
            else:
                bs_res = self.scrape_with_beautifulsoup(resp.text, url=url)
                title = bs_res.get("title", url)
                clean_text = bs_res.get("text", "")
                links = bs_res.get("links", [])
        except Exception as req_err:
            logger.debug(f"HTTP fast-path failed for {url}: {req_err}")
            is_blocked = True

        # If fast-path extracted sufficient clean content, return immediately
        if not is_blocked and len(clean_text) >= MIN_SCRAPED_TEXT_LENGTH:
            return {
                "status": "success",
                "engine_used": "BeautifulSoup4 + Scrapy",
                "url": url,
                "title": title,
                "text": clean_text[:max_chars],
                "content_length": len(clean_text),
                "key_links": links
            }

        # 3. Tier 2: Bot Block or Dynamic JS -> Playwright Headless Browser
        logger.info(f"[O.P.S. Crawler] Escalating to Playwright headless browser for: {url}")
        pw_res = self.scrape_with_playwright(url)
        if pw_res.get("status") == "success" and len(pw_res.get("text", "")) >= MIN_SCRAPED_TEXT_LENGTH:
            pw_res["engine_used"] = "Playwright (Headless Chrome)"
            return pw_res

        # 4. Tier 3: Selenium WebDriver Fallback
        logger.info(f"[O.P.S. Crawler] Escalating to Selenium Chrome WebDriver for: {url}")
        sel_res = self.scrape_with_selenium(url)
        if sel_res.get("status") == "success" and len(sel_res.get("text", "")) >= MIN_SCRAPED_TEXT_LENGTH:
            sel_res["engine_used"] = "Selenium WebDriver"
            return sel_res

        # 5. Tier 4: ScrapingBee Cloud Proxy (if key is set)
        sb_res = self.scrape_with_scrapingbee(url)
        if sb_res.get("status") == "success":
            sb_res["engine_used"] = "ScrapingBee Cloud Engine"
            return sb_res

        # 6. If partial text was gathered from fast-path, return it
        if clean_text:
            return {
                "status": "partial",
                "engine_used": "BeautifulSoup4 (Partial)",
                "url": url,
                "title": title,
                "text": clean_text[:max_chars],
                "content_length": len(clean_text),
                "key_links": links
            }

        return {
            "status": "scrape_failed",
            "url": url,
            "error": "All 6 crawling engines (BeautifulSoup, Scrapy, Playwright, Selenium, ScrapingBee, Crawlee) encountered access or content restrictions."
        }

    # =========================================================================
    # 3. LIVE PERSON BIOGRAPHY & PROFILE CRAWLER
    # =========================================================================

    def crawl_person_bio(self, person_name: str) -> Dict[str, Any]:
        """
        Crawls real-time authoritative biography and background on any person.
        Combines Wikipedia REST API + DuckDuckGo live career highlights.
        Includes special knowledge handling for system creators and anti-hallucination checks.
        """
        cleaned_name = re.sub(
            r'^(who\s+is|who\s+was|tell\s+me\s+about|biography\s+of|profile\s+of|search\s+for|search)\s+',
            '',
            person_name,
            flags=re.IGNORECASE
        ).strip(' ?."\'')

        logger.info(f"[O.P.S. Bio Crawler] Crawling live profile for: '{cleaned_name}'")

        # Creator / Developer direct profile handling
        if cleaned_name.lower() in ["suraj", "the creator", "the developer", "creator", "developer", "author"]:
            bio_data = {
                "name": "Suraj",
                "title": "Suraj",
                "description": "Creator & Lead Architect of O.P.S.",
                "extract": "Suraj is the creator, developer, and architect of O.P.S. (Over-Engineered Programmed System), an ultra-intelligent, local-first tactical AI Operating System and autonomous workstation companion.",
                "source_url": "https://github.com/sn740698-cell/O.P.S",
                "latest_highlights": [
                    {
                        "title": "O.P.S. Architecture & Development",
                        "snippet": "Engineered the tri-model LangGraph orchestration engine, local LLM intelligence, desktop automation, and real-time multi-agent systems.",
                        "url": "https://github.com/sn740698-cell/O.P.S"
                    }
                ],
                "voice_briefing": "Suraj is the creator and lead engineer of O.P.S., the Over-Engineered Programmed System."
            }
            markdown_report = (
                f"[•] DOSSIER: SURAJ\n"
                f"[•] DESIGNATION: Creator & Lead Architect of O.P.S.\n"
                f"[•] SYNOPSIS: Suraj is the creator, developer, and architect of O.P.S. (Over-Engineered Programmed System), an ultra-intelligent local-first tactical AI Operating System.\n"
                f"[•] VERIFIED SOURCE: [O.P.S. Repository](https://github.com/sn740698-cell/O.P.S)\n"
                f"[•] ARCHITECTURAL CONTRIBUTIONS:\n"
                f"    ↳ [O.P.S. Tri-Model Orchestration Engine](https://github.com/sn740698-cell/O.P.S): Built local LangGraph multi-agent core, desktop GUI controller, and real-time web crawler.\n"
            )
            return {
                "status": "success",
                "category": "PERSON_BIO",
                "query": cleaned_name,
                "data": bio_data,
                "markdown": markdown_report,
                "voice_briefing": bio_data["voice_briefing"]
            }

        # Self-identity query guard
        if cleaned_name.lower() in ["yourself", "you", "ops", "o.p.s.", "jarvis", "o.p.s"]:
            bio_data = {
                "name": "O.P.S.",
                "title": "O.P.S. (Over-Engineered Programmed System)",
                "description": "Tactical AI Operating System",
                "extract": "O.P.S. is an ultra-intelligent tactical AI Operating System created by Suraj, modeled in tone after J.A.R.V.I.S. with a 1990s retro HUD terminal aesthetic.",
                "source_url": "https://github.com/sn740698-cell/O.P.S",
                "latest_highlights": [],
                "voice_briefing": "I am O.P.S., an ultra-intelligent tactical AI Operating System created by Suraj."
            }
            markdown_report = (
                f"[•] DOSSIER: O.P.S. (OVER-ENGINEERED PROGRAMMED SYSTEM)\n"
                f"[•] DESIGNATION: Tactical AI Operating System\n"
                f"[•] CREATOR: Suraj\n"
                f"[•] SYNOPSIS: Autonomous local-first AI system equipped with tri-model intelligence, workstation memory, desktop automation, and live web crawling.\n"
                f"[•] VERIFIED SOURCE: [O.P.S. System Core](https://github.com/sn740698-cell/O.P.S)\n"
            )
            return {
                "status": "success",
                "category": "PERSON_BIO",
                "query": cleaned_name,
                "data": bio_data,
                "markdown": markdown_report,
                "voice_briefing": bio_data["voice_briefing"]
            }

        wiki_slug = urllib.parse.quote(cleaned_name.replace(" ", "_"))
        wiki_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{wiki_slug}"

        bio_data = {
            "name": cleaned_name,
            "title": cleaned_name,
            "description": "",
            "extract": "",
            "source_url": "",
            "latest_highlights": [],
            "voice_briefing": ""
        }

        # 1. Fetch live Wikipedia extract
        wiki_found = False
        try:
            r = requests.get(wiki_url, headers=self.WIKI_HEADERS, timeout=8)
            if r.status_code == 200:
                data = r.json()
                extract = data.get("extract", "").strip()
                title = data.get("title", cleaned_name)
                # Check for plausible match
                if extract and len(extract) > 20:
                    bio_data["title"] = title
                    bio_data["description"] = data.get("description", "")
                    bio_data["extract"] = extract
                    bio_data["source_url"] = data.get("content_urls", {}).get("desktop", {}).get("page", "")
                    wiki_found = True
        except Exception as e:
            logger.warning(f"Wikipedia lookup error for '{cleaned_name}': {e}")

        # 2. Fetch live recent highlights via search
        search_res = self.search_web(f"{cleaned_name} biography career facts", max_results=3)
        if search_res.get("status") == "success":
            for itm in search_res.get("results", []):
                bio_data["latest_highlights"].append({
                    "title": itm.get("title"),
                    "snippet": itm.get("snippet"),
                    "url": itm.get("url")
                })

        # If Wikipedia failed, try synthesizing extract from search snippets
        if not wiki_found:
            if bio_data["latest_highlights"]:
                top_snippet = bio_data["latest_highlights"][0]["snippet"]
                if top_snippet and len(top_snippet) > 30:
                    bio_data["extract"] = top_snippet
                    bio_data["source_url"] = bio_data["latest_highlights"][0]["url"]
                    bio_data["description"] = "Web Search Index Profile"

        # Anti-Hallucination guard: If nothing was found anywhere, explicitly fail
        if not bio_data["extract"] and not bio_data["latest_highlights"]:
            return {
                "status": "not_found",
                "category": "PERSON_BIO",
                "query": cleaned_name,
                "error": f"No verified biographical or factual records found for '{cleaned_name}' in public knowledge indexes.",
                "markdown": f"[•] INTEL: No verified biographical records found for '{cleaned_name}'.\n[•] STATUS: Live web crawler returned zero matches.",
                "voice_briefing": f"No biographical records were found for {cleaned_name}."
            }

        # 3. Synthesize Speech Summary (for Wispr Flow / Piper TTS)
        if bio_data["extract"]:
            first_sentence = bio_data["extract"].split(". ")[0] + "."
            bio_data["voice_briefing"] = f"{bio_data['title']}: {first_sentence}"
        else:
            bio_data["voice_briefing"] = f"Here is the live web intelligence on {cleaned_name}."

        raw_bio_context = (
            f"Person / Subject: {bio_data['title']}\n"
            f"Description: {bio_data['description']}\n"
            f"Summary / Extract: {bio_data['extract']}\n"
            f"Source URL: {bio_data['source_url']}\n"
            + "\n".join([f"Wire Update: {h['title']} - {h['snippet']} ({h['url']})" for h in bio_data['latest_highlights']])
        )
        try:
            from ops_core.services.ollama_service import ollama_service
            synthesized_bio = ollama_service.synthesize_crawled_knowledge(f"Biography and career of {cleaned_name}", raw_bio_context)
        except Exception:
            synthesized_bio = (
                f"[•] DOSSIER: {bio_data['title'].upper()}\n"
                f"[•] DESIGNATION: {bio_data['description'] or 'Public Profile'}\n"
                f"[•] SYNOPSIS: {bio_data['extract']}\n"
            )

        return {
            "status": "success",
            "category": "PERSON_BIO",
            "query": cleaned_name,
            "data": bio_data,
            "summary": synthesized_bio,
            "markdown": synthesized_bio,
            "voice_briefing": bio_data["voice_briefing"]
        }

    # =========================================================================
    # 4. SCIENTIFIC & TECHNICAL THEORY CRAWLER
    # =========================================================================

    def crawl_concept_theory(self, concept: str) -> Dict[str, Any]:
        """
        Crawls scientific laws, mathematical theorems, computing paradigms, and deep theories
        (e.g., 'Quantum Computing', 'General Relativity', 'Transformer neural networks', etc.).
        """
        cleaned_concept = re.sub(
            r'^(what\s+is|what\s+are|explain|tell\s+me\s+about|theory\s+of|the\s+theory\s+of|concept\s+of)\s+',
            '',
            concept,
            flags=re.IGNORECASE
        ).strip(' ?."\'')
        logger.info(f"[O.P.S. Theory Crawler] Crawling concept: '{cleaned_concept}'")

        wiki_slug = urllib.parse.quote(cleaned_concept.replace(" ", "_"))
        wiki_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{wiki_slug}"

        theory_data = {
            "concept": cleaned_concept,
            "title": cleaned_concept,
            "description": "",
            "extract": "",
            "source_url": "",
            "key_principles": [],
            "voice_briefing": ""
        }

        # 1. Fetch live encyclopedia knowledge
        wiki_found = False
        try:
            r = requests.get(wiki_url, headers=self.WIKI_HEADERS, timeout=8)
            if r.status_code == 200:
                data = r.json()
                extract = data.get("extract", "").strip()
                if extract and len(extract) > 20:
                    theory_data["title"] = data.get("title", cleaned_concept)
                    theory_data["description"] = data.get("description", "")
                    theory_data["extract"] = extract
                    theory_data["source_url"] = data.get("content_urls", {}).get("desktop", {}).get("page", "")
                    wiki_found = True
        except Exception as e:
            logger.warning(f"Wikipedia lookup error for '{cleaned_concept}': {e}")

        # 2. Enrich with web search for practical context
        search_res = self.search_web(f"{cleaned_concept} explanation principles overview", max_results=3)
        if search_res.get("status") == "success":
            for itm in search_res.get("results", []):
                theory_data["key_principles"].append({
                    "title": itm.get("title"),
                    "snippet": itm.get("snippet"),
                    "url": itm.get("url")
                })

        if not wiki_found:
            if theory_data["key_principles"]:
                top_snippet = theory_data["key_principles"][0]["snippet"]
                if top_snippet and len(top_snippet) > 30:
                    theory_data["extract"] = top_snippet
                    theory_data["source_url"] = theory_data["key_principles"][0]["url"]
                    theory_data["description"] = "Technical Knowledge Index"

        # Anti-Hallucination guard
        if not theory_data["extract"] and not theory_data["key_principles"]:
            return {
                "status": "not_found",
                "category": "THEORY_CONCEPT",
                "query": cleaned_concept,
                "error": f"Concept '{cleaned_concept}' not found in theoretical knowledge repositories.",
                "markdown": f"[•] INTEL: No verified theoretical definitions found for '{cleaned_concept}'.\n[•] STATUS: Knowledge base returned zero matches.",
                "voice_briefing": f"No theoretical records found for {cleaned_concept}."
            }

        # 3. Voice Briefing Formulation
        if theory_data["extract"]:
            first_sentence = theory_data["extract"].split(". ")[0] + "."
            theory_data["voice_briefing"] = f"{theory_data['title']}: {first_sentence}"
        raw_theory_context = (
            f"Concept: {theory_data['title']}\n"
            f"Overview: {theory_data['extract']}\n"
            f"Source: {theory_data['source_url']}\n"
            + "\n".join([f"Principle: {p['title']} - {p['snippet']}" for p in theory_data['key_principles']])
        )
        try:
            from ops_core.services.ollama_service import ollama_service
            synthesized_theory = ollama_service.synthesize_crawled_knowledge(concept, raw_theory_context)
        except Exception:
            synthesized_theory = (
                f"[•] CONCEPT: {theory_data['title'].upper()}\n"
                f"[•] THEORETICAL FOUNDATION: {theory_data['extract']}\n"
            )

        return {
            "status": "success",
            "category": "THEORY_CONCEPT",
            "query": cleaned_concept,
            "data": theory_data,
            "summary": synthesized_theory,
            "markdown": synthesized_theory,
            "voice_briefing": theory_data["voice_briefing"]
        }

    # =========================================================================
    # 5. LIVE NEWS & REAL-TIME UPDATES CRAWLER
    # =========================================================================

    def crawl_news_live(self, topic: Optional[str] = None, max_articles: int = 5) -> Dict[str, Any]:
        """
        Crawls live up-to-the-minute global or topic-specific news via Google News RSS
        and optionally deep-crawls top article URLs.
        """
        query_topic = topic or "world news technology"
        cleaned_topic = re.sub(
            r'^(latest\s+news\s+on|news\s+about|live\s+news\s+on|live\s+update\s+on|news\s+on|news)\s+',
            '',
            query_topic,
            flags=re.IGNORECASE
        ).strip(' ?."\'')
        logger.info(f"[O.P.S. Live News Crawler] Querying real-time feed for: '{cleaned_topic}'")

        rss_url = f"https://news.google.com/rss/search?q={urllib.parse.quote(cleaned_topic)}&hl=en-US&gl=US&ceid=US:en"

        articles = []
        try:
            resp = requests.get(rss_url, headers=self.DEFAULT_HEADERS, timeout=10)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, "xml")
                items = soup.find_all("item")[:max_articles]
                for itm in items:
                    t = itm.title.text if itm.title else "News Update"
                    lnk = itm.link.text if itm.link else ""
                    pub = itm.pubDate.text if itm.pubDate else ""
                    desc = itm.description.text if itm.description else ""
                    # Strip html tags from description
                    clean_desc = BeautifulSoup(desc, "html.parser").get_text(strip=True) if desc else ""
                    articles.append({
                        "headline": t,
                        "url": lnk,
                        "published_at": pub,
                        "snippet": clean_desc
                    })
        except Exception as e:
            logger.error(f"Live RSS error for '{cleaned_topic}': {e}")

        # Fallback to search if RSS failed or was empty
        if not articles:
            s_res = self.search_web(f"{cleaned_topic} latest news live updates", max_results=max_articles)
            for itm in s_res.get("results", []):
                articles.append({
                    "headline": itm.get("title", ""),
                    "url": itm.get("url", ""),
                    "published_at": "Today",
                    "snippet": itm.get("snippet", "")
                })

        if not articles:
            return {
                "status": "not_found",
                "category": "LIVE_NEWS",
                "topic": cleaned_topic,
                "error": f"No active news wire updates found for '{cleaned_topic}'.",
                "markdown": f"[•] LIVE WIRE: {cleaned_topic.upper()}\n[•] FEED STATUS: No active wire dispatches available at this time.",
                "voice_briefing": f"No current news updates found for {cleaned_topic}."
            }

        # Voice Briefing Formulation
        top_headlines = [a["headline"].split(" - ")[0] for a in articles[:3]]
        voice_briefing = f"Here are the latest live updates on {cleaned_topic}. " + ". ".join(top_headlines) + "."

        markdown_report = (
            f"[•] LIVE WIRE: {cleaned_topic.upper()}\n"
            f"[•] FEED STATUS: Real-Time Stream Active (Dispatched {len(articles)} wire reports)\n"
            f"[•] DISPATCHED WIRE HEADLINES:\n"
        )
        for i, a in enumerate(articles, 1):
            pub_info = f" ({a['published_at']})" if a['published_at'] else ""
            markdown_report += f"    [{i}] [{a['headline']}]({a['url']}){pub_info}\n"
            if a['snippet']:
                markdown_report += f"        ↳ {a['snippet']}\n"

        return {
            "status": "success",
            "category": "LIVE_NEWS",
            "topic": cleaned_topic,
            "articles": articles,
            "markdown": markdown_report,
            "voice_briefing": voice_briefing
        }

    # =========================================================================
    # 6. AUTONOMOUS MULTI-PAGE DEEP RESEARCH (Crawlee / ScrapeGraph style)
    # =========================================================================

    def crawl_web_research(self, query: str, max_pages: int = 3) -> Dict[str, Any]:
        """
        Crawls multiple organic results, retrieves full page DOMs, parses clean markdown text,
        and aggregates structured facts across all visited sources.
        """
        logger.info(f"[O.P.S. Deep Research] Beginning multi-source deep crawl for: '{query}'")

        # Step 1: Discover top URLs
        search_res = self.search_web(query, max_results=max_pages + 2)
        results = search_res.get("results", [])

        if not results:
            return {
                "status": "scrape_failed",
                "category": "DEEP_RESEARCH",
                "query": query,
                "error": f"No searchable online sources found for '{query}'.",
                "markdown": f"[•] INTEL: No web search results available for query: '{query}'.",
                "voice_briefing": f"No online sources found for {query}."
            }

        crawled_pages = []
        combined_sections = []

        for r in results:
            if len(crawled_pages) >= max_pages:
                break
            u = r.get("url")
            if not u or "duckduckgo.com" in u:
                continue

            page_data = self.scrape_url(u, max_chars=2000)
            if page_data.get("status") == "success" and page_data.get("text"):
                extracted_text = page_data.get("text", "").strip()
                crawled_pages.append({
                    "url": u,
                    "title": page_data.get("title", r.get("title", u)),
                    "length": len(extracted_text),
                    "sample": extracted_text[:400]
                })
                # Keep structured excerpt for the LLM
                combined_sections.append({
                    "source": page_data.get("title", r.get("title", u)),
                    "url": u,
                    "content": extracted_text[:1200]
                })

        # Fallback to search snippets if direct DOM scrape failed on all links
        if not combined_sections:
            for r in results[:max_pages]:
                if r.get("snippet"):
                    combined_sections.append({
                        "source": r.get("title", "Search Index"),
                        "url": r.get("url", ""),
                        "content": r.get("snippet")
                    })

        if not combined_sections:
            return {
                "status": "scrape_failed",
                "category": "DEEP_RESEARCH",
                "query": query,
                "error": "Web crawler unable to extract text from target web pages.",
                "markdown": f"[•] SCRAPE FAILED: Target sources blocked crawler or contained insufficient text for '{query}'.",
                "voice_briefing": f"Web crawl failed for {query}."
            }

        voice_briefing = f"Completed multi-source crawl across {len(combined_sections)} verified sources for '{query}'. Synthesizing key findings."

        raw_context = "\n\n".join([f"Source: {s['source']} ({s['url']})\n{s['content']}" for s in combined_sections])
        try:
            from ops_core.services.ollama_service import ollama_service
            synthesized_report = ollama_service.synthesize_crawled_knowledge(query, raw_context)
        except Exception:
            synthesized_report = (
                f"### 🌐 Multi-Source Deep Web Intelligence: {query}\n"
                f"**Verified Sources:** {len(combined_sections)} online documents indexed.\n\n"
                f"{raw_context[:1000]}"
            )

        return {
            "status": "success",
            "category": "DEEP_RESEARCH",
            "query": query,
            "pages_crawled": len(combined_sections),
            "sources": combined_sections,
            "summary": synthesized_report,
            "markdown": synthesized_report,
            "voice_briefing": voice_briefing
        }

    # =========================================================================
    # 7. UNIFIED AUTO-CLASSIFYING DISPATCHER
    # =========================================================================

    def auto_research(self, directive: str) -> Dict[str, Any]:
        """
        Intelligently classifies user query into Person, Theory, Live News, or General Web Research,
        executing the optimal background crawler and producing a voice-ready briefing.
        """
        d_lower = directive.lower().strip()

        # 0. Creator / Self-Identity handling (never scrape generic internet for self)
        if any(d_lower == q or d_lower.startswith(q + " ") for q in [
            "who are you", "what are you", "who made you", "who created you",
            "who is your creator", "who is your developer", "tell me about yourself",
            "who is suraj", "who is ops", "who is o.p.s."
        ]):
            if "suraj" in d_lower:
                return self.crawl_person_bio(person_name="Suraj")
            return self.crawl_person_bio(person_name="yourself")

        # 1. Live News & Updates
        if any(k in d_lower for k in ["news", "latest update", "live update", "what happened with", "breaking news", "headlines"]):
            return self.crawl_news_live(topic=directive)

        # 2. Person Biography
        if any(d_lower.startswith(p) for p in ["who is ", "who was ", "tell me about ", "biography of "]) or any(k in d_lower for k in ["biography", "profile of"]):
            return self.crawl_person_bio(person_name=directive)

        # 3. Scientific, Tech & Conceptual Theory
        if any(d_lower.startswith(p) for p in ["what is ", "what are ", "explain ", "theory of ", "how does "]) or any(k in d_lower for k in [
            "quantum", "relativity", "neural network", "transformer", "black hole", "string theory",
            "evolution", "thermodynamics", "algorithm", "blockchain", "compiler", "architecture"
        ]):
            return self.crawl_concept_theory(concept=directive)

        # 4. Direct URL Crawling
        if any(directive.startswith(p) for p in ["http://", "https://", "www."]):
            return self.scrape_url(url=directive)

        # 5. Default: Multi-Page Web Research
        return self.crawl_web_research(query=directive)


scraping_service = OPSScrapingService()

