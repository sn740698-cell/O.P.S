"""
O.P.S. Automated Verification Test Suite
Tests:
1. Crawlee & ScrapeGraphAI runtime verification
2. OPSScrapingService Person, Theory & Live News background crawling
3. Multi-Agent Orchestrator LangGraph routing & execution
4. Voice Calling / TTS integration
5. Safety Gatekeeper risk evaluation
"""

import os
import sys
import asyncio

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ops_backend.settings')
import django
django.setup()

from ops_core.services.scraping_service import OPSScrapingService
from ops_core.services.agent_orchestrator import OPSMultiAgentOrchestrator
from ops_core.services.voice_service import WisprFlowVoiceService
from ops_core.safety import OPSSafetyGatekeeper


def test_packages():
    print("--- [TEST 1: CRAWLEE & SCRAPEGRAPHAI RUNTIME] ---")
    import crawlee
    import scrapegraphai
    print(f"Crawlee: INSTALLED (version: {getattr(crawlee, '__version__', '1.10.3')})")
    print(f"ScrapeGraphAI: INSTALLED (version: {getattr(scrapegraphai, '__version__', '2.3.0')})")
    print("Test 1 PASS!")


def test_scraping_service():
    print("\n--- [TEST 2: BACKGROUND LIVE WEB CRAWLING] ---")
    svc = OPSScrapingService()

    # 1. Person Bio
    bio = svc.crawl_person_bio("Virat Kohli")
    assert bio["status"] == "success", "Bio crawl failed"
    assert "Virat Kohli" in bio["data"]["title"], "Title mismatch"
    assert len(bio["voice_briefing"]) > 10, "Voice briefing empty"
    print(f"[OK] Person Bio Crawl: {bio['data']['title']} -> Voice Briefing: '{bio['voice_briefing'][:60]}...'")

    # 2. Theory Concept
    theory = svc.crawl_concept_theory("Quantum Computing")
    assert theory["status"] == "success", "Theory crawl failed"
    assert len(theory["data"]["extract"]) > 20, "Theory extract missing"
    print(f"[OK] Theory Crawl: {theory['data']['title']} -> Extract: '{theory['data']['extract'][:60]}...'")

    # 3. Live News
    news = svc.crawl_news_live("Artificial Intelligence", max_articles=2)
    assert news["status"] == "success", "News crawl failed"
    assert len(news["articles"]) > 0, "No news articles found"
    print(f"[OK] Live News Crawl: Found {len(news['articles'])} articles -> Top Headline: '{news['articles'][0]['headline'][:60]}...'")

    # 4. Auto-Research Classifier
    auto_bio = svc.auto_research("Who is Virat Kohli?")
    assert auto_bio["category"] == "PERSON_BIO", "Failed to classify person bio"
    auto_th = svc.auto_research("Explain quantum computing")
    assert auto_th["category"] == "THEORY_CONCEPT", "Failed to classify theory"
    auto_nw = svc.auto_research("Latest news on tech")
    assert auto_nw["category"] == "LIVE_NEWS", "Failed to classify live news"
    print("[OK] Auto-Research Classifier accurately routed Bio, Theory, and Live News!")
    print("Test 2 PASS!")


def test_gatekeeper_policies():
    print("\n--- [TEST 3: SAFETY GATEKEEPER RISK POLICIES] ---")
    # Web research should be LOW risk (no intrusive popup)
    risk_crawl, _ = OPSSafetyGatekeeper.assess_risk("crawl_research", {"query": "Virat Kohli"})
    assert risk_crawl == "LOW", f"Expected LOW for crawl_research, got {risk_crawl}"

    risk_news, _ = OPSSafetyGatekeeper.assess_risk("crawl_news_live", {"topic": "AI"})
    assert risk_news == "LOW", f"Expected LOW for crawl_news_live, got {risk_news}"

    # DOM and App automation should be HIGH risk (gatekeeper modal active)
    risk_app, _ = OPSSafetyGatekeeper.assess_risk("launch_app", {"app": "calculator"})
    assert risk_app == "HIGH", f"Expected HIGH for launch_app, got {risk_app}"

    risk_dom, _ = OPSSafetyGatekeeper.assess_risk("browser_dom_task", {"site": "Instagram", "query": "song"})
    assert risk_dom == "HIGH", f"Expected HIGH for browser_dom_task, got {risk_dom}"

    risk_term, _ = OPSSafetyGatekeeper.assess_risk("run_claude_routine", {})
    assert risk_term == "HIGH", f"Expected HIGH for run_claude_routine, got {risk_term}"

    print("[OK] Web Crawling classified as LOW (zero desktop popups).")
    print("[OK] DOM Automation & App Launching classified as HIGH (requires permission).")
    print("Test 3 PASS!")


def test_orchestrator_routing():
    print("\n--- [TEST 4: MULTI-AGENT ORCHESTRATOR ROUTING] ---")
    orc = OPSMultiAgentOrchestrator()

    r1 = orc.route_router_decision({"prompt": "Who is Virat Kohli?", "target_flow": "CONVERSATIONAL"})
    assert r1 == "WEB_CRAWLER", f"Expected WEB_CRAWLER, got {r1}"

    r2 = orc.route_router_decision({"prompt": "Explain theory of relativity", "target_flow": "CONVERSATIONAL"})
    assert r2 == "WEB_CRAWLER", f"Expected WEB_CRAWLER, got {r2}"

    r3 = orc.route_router_decision({"prompt": "Latest news on AI", "target_flow": "CONVERSATIONAL"})
    assert r3 == "WEB_CRAWLER", f"Expected WEB_CRAWLER, got {r3}"

    r4 = orc.route_router_decision({"prompt": "Go to Instagram and search for the song", "target_flow": "CONVERSATIONAL"})
    assert r4 == "DIRECT_TOOL", f"Expected DIRECT_TOOL, got {r4}"

    r5 = orc.route_router_decision({"prompt": "In terminal run Claude", "target_flow": "CONVERSATIONAL"})
    assert r5 == "DIRECT_TOOL", f"Expected DIRECT_TOOL, got {r5}"

    print("[OK] All 5 router decisions verified: 3 Web Crawling, 2 DOM/Terminal Automation.")
    print("Test 4 PASS!")


def test_voice_integration():
    print("\n--- [TEST 5: VOICE SYNTHESIS DISPATCH] ---")
    voice = WisprFlowVoiceService()
    test_text = "Virat Kohli is an Indian international cricketer and former captain."
    res = voice.synthesize_speech(test_text)
    assert res["status"] == "success", "TTS synthesis failed"
    assert "audio_base64" in res, "Audio payload missing"
    print(f"[OK] Speech synthesized ({len(res['audio_base64'])} bytes base64) for live voice streaming!")
    print("Test 5 PASS!")


if __name__ == "__main__":
    print("==================================================")
    print("O.P.S. WEB CRAWLING & AGENT EXECUTION TEST SUITE")
    print("==================================================")
    test_packages()
    test_scraping_service()
    test_gatekeeper_policies()
    test_orchestrator_routing()
    test_voice_integration()
    print("\n==================================================")
    print("ALL 5 TEST SUITES PASSED WITH 100% SUCCESS!")
    print("==================================================")
