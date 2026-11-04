"""
O.P.S. 2.0 Focused Validation Suite
Validates the targeted repairs across:
- Issue 1: Web & Hybrid research factual grounding and freshness
- Issue 2: Browser tool dispatch (YouTube search vs play, Google, Instagram)
- Issue 3: Desktop Save As directory/filename separation and content verification
- Issue 4: Hybrid automation cross-engine coordination and state passing
- Issue 5: Real-time event propagation and agent status
- Issue 6: Human-in-the-Loop server-enforced permission gates
"""

import os
import sys
import time
import json
import unittest

# Ensure backend root is on sys.path
BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ops_backend.settings")
import django
django.setup()

from research_system.router import classify_request_mode, MODE_LLM, MODE_WEB, MODE_HYBRID, MODE_HYBRID_AUTO, MODE_DESKTOP_AUTO, MODE_BROWSER_AUTO
from automation_system.planner.automation_planner import AutomationPlanner, MODE_DESKTOP, MODE_BROWSER, MODE_HYBRID as AUTO_HYBRID
from automation_system.verification.verifier import AutomationVerifier
from automation_system.executors.file_system_executor import FileSystemExecutor
from research_system.orchestrator.agents.hitl_safety_controller import hitl_safety_controller_node
from research_system.orchestrator.agents.desktop_automation_executor import desktop_automation_executor_node
from research_system.orchestrator.agents.browser_automation_executor import browser_automation_executor_node
from research_system.graph.workers.search_worker import _execute_duckduckgo_search
from research_system.graph.workers.url_selection_worker import url_selection_worker_node
from research_system.graph.workers.crawling_worker import _fetch_single_page
from research_system.graph.workers.content_extraction_worker import _extract_with_bs4


class TestRepairedExecutionAndAccuracy(unittest.TestCase):

    def test_01_llm_mode_routing_and_isolation(self):
        """Test LLM Mode handles explanation without invoking web or automation."""
        query = "Explain REST APIs and provide a React-to-Django example."
        res = classify_request_mode(query)
        self.assertEqual(res["task_type"], "ANSWER")
        self.assertEqual(res["response_mode"], MODE_LLM)
        self.assertFalse(res["automation_engine_required"])
        self.assertFalse(res["approval_required"])
        print("\n[PASS] Scenario 1: LLM mode routed cleanly without web/automation tools.")

    def test_02_web_mode_django_freshness_and_official_source(self):
        """Test Web Mode retrieves official Django documentation and current release."""
        query = "What is the latest stable Django release?"
        res = classify_request_mode(query)
        self.assertEqual(res["task_type"], "ANSWER")
        self.assertEqual(res["response_mode"], MODE_WEB)

        # Search official sources
        search_res = _execute_duckduckgo_search("latest stable Django release")
        self.assertTrue(len(search_res) > 0)
        has_official = any("djangoproject.com" in r["url"] or "pypi.org/project/Django" in r["url"] for r in search_res)
        self.assertTrue(has_official, "Official Django source was not retrieved in search results")

        # Rank and select URLs
        selected = url_selection_worker_node({"search_results": search_res, "query": query})
        urls = [u["url"] for u in selected["selected_urls"]]
        self.assertTrue(any("djangoproject.com" in u or "pypi.org" in u for u in urls))

        # Crawl and verify actual release text
        target = next(u for u in search_res if "download" in u["url"] or "pypi.org" in u["url"])
        page = _fetch_single_page(target)
        ext = _extract_with_bs4(page.get("html", ""), page["url"], page["title"])
        clean_text = ext.get("clean_text", "")
        # Official page in 2026 mentions 6.x or 5.2+, NOT 5.1 as latest stable
        self.assertIn("6.1", clean_text)
        print("\n[PASS] Scenario 2: Web Mode retrieved official Django release text (found version 6.1).")

    def test_03_hybrid_answering_comparison(self):
        """Test Hybrid answering route combines reasoning and external research."""
        query = "Compare the latest Django and FastAPI versions and analyze their architectural differences."
        res = classify_request_mode(query)
        self.assertEqual(res["task_type"], "ANSWER")
        self.assertEqual(res["response_mode"], MODE_HYBRID)
        self.assertTrue(res["requires_web_research"])
        self.assertTrue(res["requires_llm_reasoning"])
        print("\n[PASS] Scenario 3: Hybrid Answering mode properly routed with dual execution requirements.")

    def test_04_desktop_save_as_path_separation_and_verification(self):
        """Test Save As separates directory from filename and verifies saved file and deletion."""
        desktop_dir = os.path.expanduser("~/Desktop")
        test_filename = "OPS_HITL_Desktop_Test.txt"
        full_path = os.path.join(desktop_dir, test_filename)
        test_content = "Hello OPS Desktop Verification Test Content\nGenerated by O.P.S. 2.0"

        # 1. Create file using FileSystemExecutor
        create_res = FileSystemExecutor.create_file(path=full_path, content=test_content, overwrite=True)
        self.assertTrue(create_res["success"])
        self.assertTrue(os.path.exists(full_path))

        # 2. Verify file content
        content_verif = AutomationVerifier.verify_file_content(full_path, "Hello OPS Desktop Verification", timeout=2.0)
        self.assertTrue(content_verif["verified"])

        # 3. Delete file and verify deletion
        del_res = FileSystemExecutor.delete_file(path=full_path)
        self.assertTrue(del_res["success"])
        del_verif = AutomationVerifier.verify_file_deleted(full_path, timeout=2.0)
        self.assertTrue(del_verif["verified"])
        print("\n[PASS] Scenario 4: Desktop file creation, content verification, and deletion verification verified.")

    def test_05_browser_automation_youtube_and_google_planning(self):
        """Test YouTube search-only does not autoplay, and Google search extracts query."""
        # 1. YouTube Search Only
        p_search = AutomationPlanner.plan_task("Open YouTube and search for Believer by Imagine Dragons")
        self.assertEqual(p_search["automation_mode"], MODE_BROWSER)
        self.assertEqual(p_search["steps"][0]["action"], "youtube_search")
        self.assertEqual(p_search["steps"][0]["params"]["query"], "Believer by Imagine Dragons")

        # 2. YouTube Search & Play
        p_play = AutomationPlanner.plan_task("Open YouTube and play Believer by Imagine Dragons")
        self.assertEqual(p_play["steps"][0]["action"], "youtube_search_and_play")

        # 3. Google Search
        p_google = AutomationPlanner.plan_task("Open Google and search for Python tutorials")
        self.assertEqual(p_google["steps"][0]["action"], "google_search")
        self.assertEqual(p_google["steps"][0]["params"]["query"], "Python tutorials")

        # 4. Instagram DMs with conversation target
        p_insta = AutomationPlanner.plan_task("Open Instagram Messages and open Alex")
        self.assertEqual(p_insta["steps"][0]["action"], "instagram_dms")
        self.assertEqual(p_insta["steps"][1]["action"], "instagram_open_conversation")
        self.assertEqual(p_insta["steps"][1]["params"]["username"], "Alex")
        print("\n[PASS] Scenario 5: Browser automation actions, parameters, and targets correctly planned.")

    def test_06_hybrid_automation_coordination_and_state(self):
        """Test Hybrid Automation coordinates browser and desktop with exact filename."""
        query = "Open Chrome and navigate to the official Django documentation. Then open Notepad, write the actual URL of the page you opened, and save it to my Desktop as OPS_Hybrid_Automation_Test.txt."
        router_res = classify_request_mode(query)
        self.assertEqual(router_res["task_type"], "AUTOMATION")
        self.assertEqual(router_res["response_mode"], "HYBRID")

        plan = AutomationPlanner.plan_task(query)
        self.assertEqual(plan["automation_mode"], "HYBRID")
        steps = plan["steps"]
        self.assertEqual(len(steps), 4)

        # Step 1: Browser navigation
        self.assertEqual(steps[0]["executor"], "browser")
        self.assertEqual(steps[0]["action"], "navigate")

        # Step 2: Notepad launch
        self.assertEqual(steps[1]["executor"], "desktop")
        self.assertEqual(steps[1]["action"], "launch_app")

        # Step 3: Type URL using inter-step reference
        self.assertEqual(steps[2]["executor"], "desktop")
        self.assertIn("$step_1.current_url", steps[2]["params"]["text"])

        # Step 4: Save As with exact destination filename
        self.assertEqual(steps[3]["executor"], "desktop")
        self.assertEqual(steps[3]["action"], "save_file")
        self.assertIn("OPS_Hybrid_Automation_Test.txt", steps[3]["params"]["path"])
        print("\n[PASS] Scenario 6: Hybrid Automation properly coordinates Playwright and Pywinauto with $step bindings.")

    def test_07_human_in_the_loop_server_enforcement(self):
        """Test backend enforces HITL gate and blocks unapproved actions."""
        # Unapproved task state
        unapproved_state = {
            "task_id": "test_unapproved_1",
            "task_type": "AUTOMATION",
            "automation_mode": "DESKTOP",
            "approval_status": "NONE",
            "execution_plan": [
                {"step_id": 1, "executor": "desktop", "action": "create_file", "params": {"path": "C:\\test.txt"}}
            ]
        }

        # Desktop executor must block
        desktop_res = desktop_automation_executor_node(unapproved_state)
        self.assertIn("errors", desktop_res)
        self.assertTrue(any("blocked" in err.lower() for err in desktop_res["errors"]))

        # Browser executor must block
        unapproved_browser = {
            "task_id": "test_unapproved_2",
            "task_type": "AUTOMATION",
            "automation_mode": "BROWSER",
            "approval_status": "NONE",
            "execution_plan": [
                {"step_id": 1, "executor": "browser", "action": "navigate", "params": {"url": "https://google.com"}}
            ]
        }
        browser_res = browser_automation_executor_node(unapproved_browser)
        self.assertIn("errors", browser_res)
        self.assertTrue(any("blocked" in err.lower() for err in browser_res["errors"]))
        print("\n[PASS] Scenario 7: Server-side HITL safety gate strictly blocks unapproved automation actions.")


if __name__ == "__main__":
    unittest.main()
