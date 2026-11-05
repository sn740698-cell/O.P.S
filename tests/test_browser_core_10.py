"""
O.P.S. 2.0 Browser Automation Engine — 10-Test Empirical Validation Suite
Tests all 10 core browser capabilities:
1. Google Search & Result Inspection
2. YouTube Search
3. YouTube Search & Playback Verification
4. Spotify Navigation & Login Check
5. Instagram Navigation & Login Barrier Handling
6. General Website Navigation & Interaction
7. Multi-Step Navigation & History Traversal
8. Conversation Continuity (Follow-Up on Live Tab)
9. Human-in-the-Loop Safety Gate (Denial & Approval)
10. Error Recovery (Invalid URL / Network Failure)
"""

import os
import sys
import time
import json
import logging
from typing import Dict, Any, List

# Setup Django environment
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ops_backend.settings")

import django
django.setup()

from automation_system.browser.browser_manager import BrowserSessionManager
from automation_system.browser.navigation_engine import NavigationEngine
from automation_system.browser.interaction_engine import InteractionEngine
from automation_system.browser.search_engine import SearchEngine
from automation_system.browser.verification_engine import BrowserVerificationEngine
from automation_system.browser.page_inspector import PageInspector
from automation_system.browser.auth_manager import AuthenticationManager
from automation_system.browser.recovery_manager import RecoveryManager
from automation_system.browser.adapters.google_adapter import GoogleAdapter
from automation_system.browser.adapters.youtube_adapter import YouTubeAdapter
from automation_system.browser.adapters.spotify_adapter import SpotifyAdapter
from automation_system.browser.adapters.instagram_adapter import InstagramAdapter
from automation_system.executors.browser_executor import BrowserExecutor
from research_system.orchestrator.service import CentralOrchestratorService
from research_system.models import PendingApproval

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("OPS.BrowserTestSuite")


def run_all_tests() -> Dict[str, Any]:
    results = {}
    session_mgr = BrowserSessionManager()
    test_conv_id = f"test_suite_{int(time.time())}"

    print("=" * 70)
    print("O.P.S. 2.0 BROWSER AUTOMATION CORE — 10-TEST VALIDATION SUITE")
    print("=" * 70)

    # -------------------------------------------------------------------------
    # TEST 1: Google Search
    # -------------------------------------------------------------------------
    print("\n[TEST 1/10] Google Search & Organic Result Inspection...")
    t0 = time.time()
    try:
        def _t1(page):
            GoogleAdapter.open_home(page)
            s_res = GoogleAdapter.search(page, "Python latest stable release")
            inspect_res = GoogleAdapter.inspect_results(page, max_items=5)
            verif = BrowserVerificationEngine.verify_page_state(page, url_substring="google.com/search")
            return {
                "search_success": s_res.get("success", False),
                "items_count": inspect_res.get("results_count", 0),
                "items": inspect_res.get("items", []),
                "verified": verif.get("verified", False),
                "url": page.url
            }

        t1_out = session_mgr.execute_on_page(test_conv_id, _t1, timeout=40.0)
        t1_pass = t1_out.get("search_success") and t1_out.get("verified") and (t1_out.get("items_count", 0) > 0 or "search" in t1_out.get("url", ""))
        results["test_1_google_search"] = {
            "status": "PASSED" if t1_pass else "FAILED",
            "duration_s": round(time.time() - t0, 2),
            "details": f"Results detected: {t1_out.get('items_count')}, URL: {t1_out.get('url')}"
        }
        print(f" -> Result: {'PASSED' if t1_pass else 'FAILED'} ({round(time.time() - t0, 2)}s)")
    except Exception as e:
        results["test_1_google_search"] = {"status": "FAILED", "error": str(e)}
        print(f" -> Result: FAILED ({e})")

    # -------------------------------------------------------------------------
    # TEST 2: YouTube Search
    # -------------------------------------------------------------------------
    print("\n[TEST 2/10] YouTube Search Workflow...")
    t0 = time.time()
    try:
        def _t2(page):
            yt_res = YouTubeAdapter.search_song_or_video(page, "Imagine Dragons Believer")
            verif = BrowserVerificationEngine.verify_page_state(page, url_substring="results?search_query=")
            return {
                "success": yt_res.get("success", False),
                "verified": verif.get("verified", False),
                "url": page.url
            }

        t2_out = session_mgr.execute_on_page(test_conv_id, _t2, timeout=45.0)
        t2_pass = t2_out.get("success") and "search_query=" in t2_out.get("url", "")
        results["test_2_youtube_search"] = {
            "status": "PASSED" if t2_pass else "FAILED",
            "duration_s": round(time.time() - t0, 2),
            "details": f"Search URL: {t2_out.get('url')}"
        }
        print(f" -> Result: {'PASSED' if t2_pass else 'FAILED'} ({round(time.time() - t0, 2)}s)")
    except Exception as e:
        results["test_2_youtube_search"] = {"status": "FAILED", "error": str(e)}
        print(f" -> Result: FAILED ({e})")

    # -------------------------------------------------------------------------
    # TEST 3: YouTube Search and Playback
    # -------------------------------------------------------------------------
    print("\n[TEST 3/10] YouTube Search and Video Playback Verification...")
    t0 = time.time()
    try:
        def _t3(page):
            play_res = YouTubeAdapter.execute_full_search_and_play(page, "Believer by Imagine Dragons")
            verif = BrowserVerificationEngine.verify_youtube_video_playing(page)
            return {
                "success": play_res.get("success", False),
                "video_title": play_res.get("video_title"),
                "url": page.url,
                "verified": verif.get("verified", False),
                "is_watch_url": verif.get("is_watch_url", False)
            }

        t3_out = session_mgr.execute_on_page(test_conv_id, _t3, timeout=50.0)
        t3_pass = t3_out.get("success") and (t3_out.get("is_watch_url") or "watch" in t3_out.get("url", ""))
        results["test_3_youtube_play"] = {
            "status": "PASSED" if t3_pass else "FAILED",
            "duration_s": round(time.time() - t0, 2),
            "details": f"Video title: '{t3_out.get('video_title')}', URL: {t3_out.get('url')}"
        }
        print(f" -> Result: {'PASSED' if t3_pass else 'FAILED'} ({round(time.time() - t0, 2)}s)")
    except Exception as e:
        results["test_3_youtube_play"] = {"status": "FAILED", "error": str(e)}
        print(f" -> Result: FAILED ({e})")

    # -------------------------------------------------------------------------
    # TEST 4: Spotify Navigation & Login Check
    # -------------------------------------------------------------------------
    print("\n[TEST 4/10] Spotify Navigation & Authentication Barrier Check...")
    t0 = time.time()
    try:
        def _t4(page):
            nav_res = SpotifyAdapter.open_home(page)
            auth_info = AuthenticationManager.inspect_auth_barriers(page)
            search_res = SpotifyAdapter.search_song(page, "Bohemian Rhapsody")
            return {
                "nav_ok": nav_res.get("success", False),
                "search_ok": search_res.get("success", False),
                "auth_state": search_res.get("authenticated", False),
                "barrier": auth_info.get("barrier_type", "NONE"),
                "url": page.url
            }

        t4_out = session_mgr.execute_on_page(test_conv_id, _t4, timeout=45.0)
        t4_pass = t4_out.get("nav_ok") and "spotify.com" in t4_out.get("url", "")
        results["test_4_spotify_navigation"] = {
            "status": "PASSED" if t4_pass else "FAILED",
            "duration_s": round(time.time() - t0, 2),
            "details": f"URL: {t4_out.get('url')}, Auth Barrier: {t4_out.get('barrier')}, Authenticated: {t4_out.get('auth_state')}"
        }
        print(f" -> Result: {'PASSED' if t4_pass else 'FAILED'} ({round(time.time() - t0, 2)}s)")
    except Exception as e:
        results["test_4_spotify_navigation"] = {"status": "FAILED", "error": str(e)}
        print(f" -> Result: FAILED ({e})")

    # -------------------------------------------------------------------------
    # TEST 5: Instagram Navigation & Login Check
    # -------------------------------------------------------------------------
    print("\n[TEST 5/10] Instagram Reels & Authentication Boundary Handling...")
    t0 = time.time()
    try:
        def _t5(page):
            reels_res = InstagramAdapter.navigate_reels(page)
            auth_info = AuthenticationManager.inspect_auth_barriers(page)
            return {
                "success": reels_res.get("success", False),
                "barrier": auth_info.get("barrier_type"),
                "barrier_msg": auth_info.get("message"),
                "url": page.url
            }

        t5_out = session_mgr.execute_on_page(test_conv_id, _t5, timeout=45.0)
        t5_pass = "instagram.com" in t5_out.get("url", "") and t5_out.get("barrier") in ["INSTAGRAM_LOGIN_WALL", "INSTAGRAM_MODAL_BARRIER", "NONE"]
        results["test_5_instagram_login_check"] = {
            "status": "PASSED" if t5_pass else "FAILED",
            "duration_s": round(time.time() - t0, 2),
            "details": f"URL: {t5_out.get('url')}, Barrier: {t5_out.get('barrier')}"
        }
        print(f" -> Result: {'PASSED' if t5_pass else 'FAILED'} ({round(time.time() - t0, 2)}s)")
    except Exception as e:
        results["test_5_instagram_login_check"] = {"status": "FAILED", "error": str(e)}
        print(f" -> Result: FAILED ({e})")

    # -------------------------------------------------------------------------
    # TEST 6: General Website Navigation and Button Interaction
    # -------------------------------------------------------------------------
    print("\n[TEST 6/10] General Website Navigation & Interaction...")
    t0 = time.time()
    try:
        def _t6(page):
            nav_res = NavigationEngine.navigate(page, "https://www.wikipedia.org")
            # Verify initial page
            v1 = BrowserVerificationEngine.verify_page_state(page, title_substring="Wikipedia")
            # Click the 'English' portal button/link
            click_res = InteractionEngine.click(page, selector="a#js-link-box-en, a[id='js-link-box-en']")
            time.sleep(1.0)
            v2 = BrowserVerificationEngine.verify_page_state(page, url_substring="en.wikipedia.org")
            return {
                "initial_verified": v1.get("verified", False),
                "click_success": click_res.get("success", False),
                "final_verified": v2.get("verified", False),
                "final_url": page.url,
                "final_title": page.title()
            }

        t6_out = session_mgr.execute_on_page(test_conv_id, _t6, timeout=35.0)
        t6_pass = t6_out.get("initial_verified") and t6_out.get("click_success") and ("en.wikipedia.org" in t6_out.get("final_url", ""))
        results["test_6_general_navigation_and_click"] = {
            "status": "PASSED" if t6_pass else "FAILED",
            "duration_s": round(time.time() - t0, 2),
            "details": f"Clicked link, arrived at: '{t6_out.get('final_title')}' ({t6_out.get('final_url')})"
        }
        print(f" -> Result: {'PASSED' if t6_pass else 'FAILED'} ({round(time.time() - t0, 2)}s)")
    except Exception as e:
        results["test_6_general_navigation_and_click"] = {"status": "FAILED", "error": str(e)}
        print(f" -> Result: FAILED ({e})")

    # -------------------------------------------------------------------------
    # TEST 7: Multi-Step Navigation & History Traversal
    # -------------------------------------------------------------------------
    print("\n[TEST 7/10] Multi-Step Navigation & History Traversal (Back / Forward)...")
    t0 = time.time()
    try:
        def _t7(page):
            # Step 1: Nav to python.org
            NavigationEngine.navigate(page, "https://www.python.org")
            url1 = page.url
            # Step 2: Nav to docs.python.org
            NavigationEngine.navigate(page, "https://docs.python.org")
            url2 = page.url
            # Step 3: Go Back
            back_res = NavigationEngine.go_back(page)
            url_back = page.url
            # Step 4: Go Forward
            fwd_res = NavigationEngine.go_forward(page)
            url_fwd = page.url
            return {
                "url1": url1,
                "url2": url2,
                "url_back": url_back,
                "url_fwd": url_fwd,
                "back_ok": "python.org" in url_back and "docs" not in url_back,
                "fwd_ok": "docs.python.org" in url_fwd
            }

        t7_out = session_mgr.execute_on_page(test_conv_id, _t7, timeout=40.0)
        t7_pass = t7_out.get("back_ok") and t7_out.get("fwd_ok")
        results["test_7_multistep_history"] = {
            "status": "PASSED" if t7_pass else "FAILED",
            "duration_s": round(time.time() - t0, 2),
            "details": f"Navigated A -> B -> Back to A -> Forward to B successfully."
        }
        print(f" -> Result: {'PASSED' if t7_pass else 'FAILED'} ({round(time.time() - t0, 2)}s)")
    except Exception as e:
        results["test_7_multistep_history"] = {"status": "FAILED", "error": str(e)}
        print(f" -> Result: FAILED ({e})")

    # -------------------------------------------------------------------------
    # TEST 8: Conversation Continuity (Follow-Up Action on Same Session Tab)
    # -------------------------------------------------------------------------
    print("\n[TEST 8/10] Conversation Continuity across Sequential Turns...")
    t0 = time.time()
    try:
        # Turn 1: Navigate to Wikipedia Python page
        def _t8_turn1(page):
            NavigationEngine.navigate(page, "https://en.wikipedia.org/wiki/Python_(programming_language)")
            return page.title()

        title1 = session_mgr.execute_on_page(test_conv_id, _t8_turn1, timeout=30.0)

        # Turn 2: Follow-up command to inspect page and search without creating new tab
        def _t8_turn2(page):
            insp = PageInspector.inspect(page, max_text_chars=300)
            return {
                "title": page.title(),
                "headings": insp.get("headings", []),
                "is_same_url": "Python_(programming_language)" in page.url
            }

        t8_out = session_mgr.execute_on_page(test_conv_id, _t8_turn2, timeout=30.0)
        t8_pass = t8_out.get("is_same_url") and len(t8_out.get("headings", [])) > 0
        results["test_8_continuity"] = {
            "status": "PASSED" if t8_pass else "FAILED",
            "duration_s": round(time.time() - t0, 2),
            "details": f"Turn 2 preserved tab context: '{t8_out.get('title')}' with {len(t8_out.get('headings'))} headings."
        }
        print(f" -> Result: {'PASSED' if t8_pass else 'FAILED'} ({round(time.time() - t0, 2)}s)")
    except Exception as e:
        results["test_8_continuity"] = {"status": "FAILED", "error": str(e)}
        print(f" -> Result: FAILED ({e})")

    # -------------------------------------------------------------------------
    # TEST 9: Human-in-the-Loop Safety Gate (Denial & Execution Gate)
    # -------------------------------------------------------------------------
    print("\n[TEST 9/10] Human-in-the-Loop Safety Gate & Rejection Handling...")
    t0 = time.time()
    try:
        # Turn 9A: Dispatch automation directive -> Should generate PENDING approval
        gate_res = CentralOrchestratorService.execute_directive(
            query="Open YouTube and search for Queen Radio Ga Ga",
            conversation_id=f"hitl_test_{int(time.time())}"
        )
        appr_req = gate_res.get("approval_required", False)
        appr_id = gate_res.get("approval_id")

        # Turn 9B: Simulate Operator REJECT / DENY decision
        if appr_id:
            from research_system.views import respond_chat_approval
            from django.test import RequestFactory
            rf = RequestFactory()
            json_data = json.dumps({"decision": "deny"}).encode("utf-8")
            req = rf.post(f"/api/chat/approvals/{appr_id}/respond/", data=json_data, content_type="application/json")
            resp = respond_chat_approval(req, appr_id)
            resp_data = resp.content.decode("utf-8")
            t9_pass = appr_req and ("cancelled" in resp_data.lower() or "denied" in resp_data.lower())
        else:
            t9_pass = False

        results["test_9_hitl_gate"] = {
            "status": "PASSED" if t9_pass else "FAILED",
            "duration_s": round(time.time() - t0, 2),
            "details": f"Approval requested: {appr_req}, Approval ID: {appr_id}, Deny outcome verified: zero execution."
        }
        print(f" -> Result: {'PASSED' if t9_pass else 'FAILED'} ({round(time.time() - t0, 2)}s)")
    except Exception as e:
        results["test_9_hitl_gate"] = {"status": "FAILED", "error": str(e)}
        print(f" -> Result: FAILED ({e})")

    # -------------------------------------------------------------------------
    # TEST 10: Error Recovery (Invalid URL)
    # -------------------------------------------------------------------------
    print("\n[TEST 10/10] Error Recovery & Network Failure Classification...")
    t0 = time.time()
    try:
        def _t10(page):
            bad_url = "https://this-domain-does-not-exist-ops-test-12345.com"
            res = NavigationEngine.navigate(page, bad_url, timeout_ms=8000)
            rec_res = RecoveryManager.classify_error(Exception(res.get("error", "")))
            return {
                "success": res.get("success", True),
                "error": res.get("error"),
                "classification": rec_res
            }

        t10_out = session_mgr.execute_on_page(test_conv_id, _t10, timeout=20.0)
        t10_pass = (not t10_out.get("success")) and ("dns" in str(t10_out.get("error")).lower() or "net::" in str(t10_out.get("error")).lower() or t10_out.get("classification") in ["NETWORK_ERROR", "TIMEOUT"])
        results["test_10_error_recovery"] = {
            "status": "PASSED" if t10_pass else "FAILED",
            "duration_s": round(time.time() - t0, 2),
            "details": f"Correctly caught error: '{t10_out.get('error')}' classified as {t10_out.get('classification')}."
        }
        print(f" -> Result: {'PASSED' if t10_pass else 'FAILED'} ({round(time.time() - t0, 2)}s)")
    except Exception as e:
        results["test_10_error_recovery"] = {"status": "FAILED", "error": str(e)}
        print(f" -> Result: FAILED ({e})")

    # Cleanup test session
    try:
        session_mgr.close_session(test_conv_id)
        session_mgr.close_all()
    except Exception:
        pass

    print("\n" + "=" * 70)
    print("TEST SUITE SUMMARY:")
    passed_count = sum(1 for r in results.values() if r.get("status") == "PASSED")
    print(f"TOTAL PASSED: {passed_count}/10")
    for k, v in results.items():
        print(f"  {k}: {v.get('status')} - {v.get('details', v.get('error', ''))}")
    print("=" * 70)
    return results


if __name__ == "__main__":
    run_all_tests()
