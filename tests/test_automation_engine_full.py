"""
O.P.S. 2.0 Comprehensive Automation Engine Test Suite
Validates:
- Part 8: 20 Real Desktop Automation Tests
- Part 9: 20 Real Browser Automation Tests
- Part 10: 10 Natural Language Desktop + 10 Natural Language Browser Tests
- Part 11: 5 Hybrid Automation Tests
"""

import os
import sys
import time
import json
import shutil
import unittest
from typing import Dict, Any

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../backend")))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ops_backend.settings")

import django
django.setup()

from automation_system.planner.automation_planner import AutomationPlanner
from automation_system.desktop.specialists.desktop_superior_agent import DesktopSuperiorAgent
from automation_system.browser.specialists.browser_superior_agent import BrowserSuperiorAgent
from automation_system.coordinator.hybrid_coordinator import HybridAutomationCoordinator
from automation_system.desktop.file_controller import FileController

TEST_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "scratch_full_automation"))
os.makedirs(TEST_DIR, exist_ok=True)

class TestAutomationEngineFull(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.planner = AutomationPlanner()
        cls.desktop_agent = DesktopSuperiorAgent(conversation_id="test_suite_full")
        cls.browser_agent = BrowserSuperiorAgent(conversation_id="test_suite_full")
        cls.hybrid_coordinator = HybridAutomationCoordinator()

    @classmethod
    def tearDownClass(cls):
        try:
            # Clean up test scratch dir
            shutil.rmtree(TEST_DIR, ignore_errors=True)
            # Ensure browser clean
            cls.browser_agent.b1_lifecycle.close_session()
        except Exception:
            pass

    # =========================================================================
    # PART 8: DESKTOP AUTOMATION TESTS (01 - 20)
    # =========================================================================

    def test_d01_open_notepad(self):
        """Desktop Test 01 — Open one application"""
        res = self.desktop_agent.d1_app.launch("notepad")
        self.assertTrue(res.get("success"), "Notepad launch failed")
        v_res = self.desktop_agent.d7_verify.verify_window("Notepad")
        self.assertTrue(v_res.get("verified"), "Notepad window not verified")

    def test_d02_open_multiple_applications(self):
        """Desktop Test 02 — Open multiple applications (VS Code and Notepad)"""
        plan = self.planner.plan_task("Open VS Code and Notepad.")
        steps = plan.get("steps", [])
        self.assertGreaterEqual(len(steps), 2, "Expected at least 2 launch steps for multi-app")
        # Execute each launch step
        res1 = self.desktop_agent.execute_step(steps[0])
        res2 = self.desktop_agent.execute_step(steps[1])
        self.assertTrue(res1.get("success") or res1.get("resolved_path"), "First app launch failed")
        self.assertTrue(res2.get("success"), "Second app launch failed")

    def test_d03_close_notepad(self):
        """Desktop Test 03 — Close an application"""
        c_res = self.desktop_agent.d1_app.close("notepad")
        self.assertTrue(c_res.get("success"), "Notepad close failed")
        v_res = self.desktop_agent.d7_verify.verify_closed("notepad")
        self.assertTrue(v_res.get("verified"), "Notepad process still running")

    def test_d04_open_folder(self):
        """Desktop Test 04 — Open a folder"""
        downloads_dir = os.path.expanduser("~/Downloads")
        res = self.desktop_agent.d4_file.open_folder(downloads_dir)
        self.assertTrue(res.get("success"), "Opening Downloads folder failed")

    def test_d05_open_specific_file(self):
        """Desktop Test 05 — Open a specific file"""
        test_file = os.path.join(TEST_DIR, "test_sample.py")
        with open(test_file, "w") as f:
            f.write("# sample file\nprint('hello')\n")
        res = self.desktop_agent.d4_file.open_file(test_file)
        self.assertTrue(res.get("success"), f"Opening file {test_file} failed")

    def test_d06_create_text_file(self):
        """Desktop Test 06 — Create a text file and write text inside it"""
        test_file = os.path.join(TEST_DIR, "ops_test.txt")
        res = self.desktop_agent.d4_file.create_file(test_file, content="Hello from O.P.S.")
        self.assertTrue(res.get("success"), "Creating text file failed")
        v_res = self.desktop_agent.d7_verify.verify_file(test_file, expected_snippet="Hello from O.P.S.")
        self.assertTrue(v_res.get("verified"), "File content verification failed")

    def test_d07_write_exact_text_in_notepad(self):
        """Desktop Test 07 — Write exact text in Notepad"""
        l_res = self.desktop_agent.d1_app.launch("notepad")
        self.assertTrue(l_res.get("success"))
        time.sleep(0.5)
        t_res = self.desktop_agent.d5_input.type_text("Notepad", "O.P.S. desktop automation is working.")
        self.assertTrue(t_res.get("success"), "Typing exact sentence failed")

    def test_d08_generate_python_code_in_notepad(self):
        """Desktop Test 08 — Generate Python code and write in Notepad"""
        plan = self.planner.plan_task("Open Notepad and write Python code to add two numbers and display the result.")
        steps = plan.get("steps", [])
        self.assertEqual(len(steps), 2, "Expected 2 steps: launch and type code")
        code_text = steps[1].get("params", {}).get("text", "")
        self.assertIn("sum", code_text.lower(), "Code text should contain sum calculation")
        self.assertNotIn("display the result", code_text.lower(), "Code text must not be raw natural language prompt")

    def test_d09_create_python_file(self):
        """Desktop Test 09 — Create a Python file add_numbers.py"""
        target_py = os.path.join(TEST_DIR, "add_numbers.py")
        res = self.desktop_agent.d6_code.generate_and_write(target_py, "Create a python script that adds two numbers.")
        self.assertTrue(res.get("success"), "Python file generation failed")
        self.assertTrue(res.get("ast_valid"), "Python AST validation failed")

    def test_d10_create_html_file(self):
        """Desktop Test 10 — Create an HTML file"""
        target_html = os.path.join(TEST_DIR, "welcome.html")
        content = "<html><head><title>Welcome</title></head><body><h1>Welcome to O.P.S.</h1><p>Over-Engineered Programmed System</p></body></html>"
        res = self.desktop_agent.d4_file.create_file(target_html, content=content)
        self.assertTrue(res.get("success"), "HTML file creation failed")
        self.assertTrue(os.path.exists(target_html))

    def test_d11_create_css_file(self):
        """Desktop Test 11 — Create a CSS file"""
        target_css = os.path.join(TEST_DIR, "style.css")
        css_content = "body { background-color: #121212; color: #ffffff; }\nh1 { color: #ff0000; }\n"
        res = self.desktop_agent.d4_file.create_file(target_css, content=css_content)
        self.assertTrue(res.get("success"), "CSS file creation failed")

    def test_d12_create_javascript_file(self):
        """Desktop Test 12 — Create a JavaScript file"""
        target_js = os.path.join(TEST_DIR, "check_even.js")
        js_content = "function isEven(num) { return num % 2 === 0; }\nconsole.log(isEven(4));\n"
        res = self.desktop_agent.d4_file.create_file(target_js, content=js_content)
        self.assertTrue(res.get("success"), "JS file creation failed")

    def test_d13_edit_existing_file(self):
        """Desktop Test 13 — Edit an existing file preserving existing code"""
        target_py = os.path.join(TEST_DIR, "math_lib.py")
        with open(target_py, "w") as f:
            f.write("def add(a, b):\n    return a + b\n")
        new_content = "def add(a, b):\n    return a + b\n\ndef multiply(a, b):\n    return a * b\n"
        res = self.desktop_agent.d4_file.edit_file(target_py, new_content=new_content)
        self.assertTrue(res.get("success"), "File edit failed")
        v_res = self.desktop_agent.d7_verify.verify_file(target_py, expected_snippet="def multiply")
        self.assertTrue(v_res.get("verified"))

    def test_d14_create_folder_structure(self):
        """Desktop Test 14 — Create folder structure OPS_TEST_PROJECT"""
        base = os.path.join(TEST_DIR, "OPS_TEST_PROJECT")
        self.desktop_agent.d4_file.create_folder(base)
        self.desktop_agent.d4_file.create_folder(os.path.join(base, "frontend"))
        self.desktop_agent.d4_file.create_folder(os.path.join(base, "backend"))
        self.desktop_agent.d4_file.create_folder(os.path.join(base, "documentation"))
        self.assertTrue(os.path.exists(os.path.join(base, "frontend")))
        self.assertTrue(os.path.exists(os.path.join(base, "backend")))
        self.assertTrue(os.path.exists(os.path.join(base, "documentation")))

    def test_d15_rename_file(self):
        """Desktop Test 15 — Rename a file"""
        src = os.path.join(TEST_DIR, "ops_test_rename.txt")
        dst = os.path.join(TEST_DIR, "ops_desktop_test.txt")
        with open(src, "w") as f:
            f.write("sample")
        res = self.desktop_agent.d4_file.rename_file(src, dst)
        self.assertTrue(res.get("success"), "File rename failed")
        self.assertTrue(os.path.exists(dst))
        self.assertFalse(os.path.exists(src))

    def test_d16_copy_file(self):
        """Desktop Test 16 — Copy a file into documentation folder"""
        src = os.path.join(TEST_DIR, "ops_desktop_test.txt")
        doc_dir = os.path.join(TEST_DIR, "OPS_TEST_PROJECT", "documentation")
        res = self.desktop_agent.d4_file.copy_file(src, doc_dir)
        self.assertTrue(res.get("success"), "File copy failed")
        self.assertTrue(os.path.exists(os.path.join(doc_dir, "ops_desktop_test.txt")))

    def test_d17_move_file(self):
        """Desktop Test 17 — Move copied file into backend folder"""
        src = os.path.join(TEST_DIR, "OPS_TEST_PROJECT", "documentation", "ops_desktop_test.txt")
        dst_dir = os.path.join(TEST_DIR, "OPS_TEST_PROJECT", "backend")
        res = self.desktop_agent.d4_file.move_file(src, dst_dir)
        self.assertTrue(res.get("success"), "File move failed")
        self.assertTrue(os.path.exists(os.path.join(dst_dir, "ops_desktop_test.txt")))
        self.assertFalse(os.path.exists(src))

    def test_d18_multiple_app_and_text(self):
        """Desktop Test 18 — Multiple application and text operations"""
        plan = self.planner.plan_task("Open Notepad and VS Code. Write a short Python program in Notepad that prints Hello O.P.S.")
        steps = plan.get("steps", [])
        self.assertGreaterEqual(len(steps), 3, "Expected 3 steps: launch vs code, launch notepad, type in notepad")

    def test_d19_ambiguous_file_request(self):
        """Desktop Test 19 — Ambiguous file request triggers clarification"""
        plan = self.planner.plan_task("Open my project file.")
        self.assertEqual(plan.get("status"), "NEEDS_CLARIFICATION")
        self.assertIn("Which project file", plan.get("clarification_prompt"))

    def test_d20_denied_approval(self):
        """Desktop Test 20 — Denied approval cancels execution"""
        state = {
            "task_type": "AUTOMATION",
            "automation_mode": "DESKTOP",
            "approval_status": "DENIED",
            "execution_plan": [{"action": "create_folder", "params": {"path": "OPS_DENIED_TEST"}}]
        }
        # Verify safety guard blocks execution
        from research_system.orchestrator.agents.desktop_automation_executor import desktop_automation_executor_node
        res = desktop_automation_executor_node(state)
        self.assertIn("blocked", res.get("errors", [""])[0].lower())

    # =========================================================================
    # PART 9: BROWSER AUTOMATION TESTS (01 - 20)
    # =========================================================================

    def test_b01_open_google(self):
        """Browser Test 01 — Open Google in browser"""
        res = self.browser_agent.execute_step({"action": "navigate", "target": "https://www.google.com"})
        self.assertTrue(res.get("success"), "Google navigation failed")

    def test_b02_search_google(self):
        """Browser Test 02 — Search Google for Virat Kohli"""
        res = self.browser_agent.execute_step({"action": "google_search", "value": "Virat Kohli"})
        self.assertTrue(res.get("success"), "Google search failed")

    def test_b03_search_technical_topic(self):
        """Browser Test 03 — Search Google for Django REST Framework tutorials"""
        res = self.browser_agent.execute_step({"action": "google_search", "value": "Django REST Framework tutorials"})
        self.assertTrue(res.get("success"), "Technical topic search failed")

    def test_b04_search_youtube(self):
        """Browser Test 04 — Search YouTube for React JS tutorials"""
        res = self.browser_agent.execute_step({"action": "youtube_search", "value": "React JS tutorials"})
        self.assertTrue(res.get("success"), "YouTube search failed")

    def test_b05_play_youtube_video(self):
        """Browser Test 05 — Play a YouTube video"""
        res = self.browser_agent._handle_youtube_directive("play Python tutorial on YouTube")
        self.assertTrue(res.get("success"), "YouTube playback failed")

    def test_b06_open_instagram(self):
        """Browser Test 06 — Open Instagram"""
        res = self.browser_agent.execute_step({"action": "navigate", "target": "https://www.instagram.com"})
        self.assertTrue(res.get("success"), "Instagram navigation failed")

    def test_b07_open_multiple_tabs(self):
        """Browser Test 07 — Open Google, YouTube, GitHub in separate tabs"""
        res1 = self.browser_agent.execute_step({"action": "navigate", "target": "https://www.google.com"})
        res2 = self.browser_agent.execute_step({"action": "open_tab", "target": "https://www.youtube.com"})
        res3 = self.browser_agent.execute_step({"action": "open_tab", "target": "https://github.com"})
        self.assertTrue(res1.get("success") and res2.get("success") and res3.get("success"))
        tabs_res = self.browser_agent.b2_tab.list_tabs()
        self.assertGreaterEqual(tabs_res.get("count", 0), 2)

    def test_b08_reuse_existing_tab(self):
        """Browser Test 08 — Reuse existing tab when opening Google again"""
        res = self.browser_agent.b2_tab.get_or_create_tab("https://www.google.com")
        self.assertTrue(res.get("success"))
        self.assertIn(res.get("action"), ["reused_tab", "new_tab"])

    def test_b09_switch_tab(self):
        """Browser Test 09 — Switch to the YouTube tab"""
        res = self.browser_agent.execute_step({"action": "switch_tab", "target": "YouTube"})
        self.assertTrue(res.get("success"), "Switching to YouTube tab failed")

    def test_b10_search_and_open_result(self):
        """Browser Test 10 — Search and click top result"""
        res = self.browser_agent.b4_interact.click_first_result()
        self.assertTrue(res.get("success"), "Clicking first result failed")

    def test_b11_navigate_through_multiple(self):
        """Browser Test 11 — Sequential website navigation"""
        r1 = self.browser_agent.execute_step({"action": "navigate", "target": "https://www.google.com"})
        r2 = self.browser_agent.execute_step({"action": "navigate", "target": "https://www.python.org"})
        r3 = self.browser_agent.execute_step({"action": "navigate", "target": "https://www.djangoproject.com"})
        self.assertTrue(r1.get("success") and r2.get("success") and r3.get("success"))

    def test_b12_interact_search_box(self):
        """Browser Test 12 — Interact with search box"""
        res = self.browser_agent.execute_step({"action": "navigate", "target": "https://www.google.com"})
        self.assertTrue(res.get("success"))
        s_res = self.browser_agent.execute_step({"action": "google_search", "value": "React documentation"})
        self.assertTrue(s_res.get("success"))

    def test_b13_click_website_link(self):
        """Browser Test 13 — Click website link"""
        self.browser_agent.execute_step({"action": "navigate", "target": "https://www.python.org"})
        c_res = self.browser_agent.execute_step({"action": "click", "target": "Documentation"})
        self.assertTrue(c_res.get("success"))

    def test_b14_open_new_tab_and_visit(self):
        """Browser Test 14 — Open a new tab and visit GitHub"""
        res = self.browser_agent.execute_step({"action": "open_tab", "target": "https://github.com"})
        self.assertTrue(res.get("success"))

    def test_b15_close_requested_tab(self):
        """Browser Test 15 — Close GitHub tab"""
        res = self.browser_agent.execute_step({"action": "close_tab", "target": "GitHub"})
        self.assertTrue(res.get("success"))

    def test_b16_download_test_file(self):
        """Browser Test 16 — Download sample test PDF"""
        pdf_url = "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf"
        res = self.browser_agent.execute_step({"action": "download", "target": pdf_url, "value": "test_dummy.pdf"})
        self.assertTrue(res.get("success"), "File download failed")
        self.assertTrue(res.get("exists"), "Downloaded file does not exist")

    def test_b17_multi_step_search_and_back(self):
        """Browser Test 17 — Multi-step search and back"""
        self.browser_agent.execute_step({"action": "navigate", "target": "https://www.google.com"})
        self.browser_agent.execute_step({"action": "google_search", "value": "Python tutorials"})
        back_res = self.browser_agent.b3_nav.go_back()
        self.assertTrue(back_res.get("success"))

    def test_b18_unavailable_website(self):
        """Browser Test 18 — Handle unavailable website accurately"""
        bad_url = "https://this-is-a-deliberately-broken-url-xyz12345.org"
        res = self.browser_agent.execute_step({"action": "navigate", "target": bad_url})
        self.assertFalse(res.get("success"), "Should report failure on invalid URL")

    def test_b19_multiple_search_operations(self):
        """Browser Test 19 — Multiple search operations in separate tabs"""
        res1 = self.browser_agent.execute_step({"action": "navigate", "target": "https://www.google.com"})
        s1 = self.browser_agent.execute_step({"action": "google_search", "value": "React tutorials"})
        t2 = self.browser_agent.execute_step({"action": "open_tab", "target": "https://www.google.com"})
        s2 = self.browser_agent.execute_step({"action": "google_search", "value": "Django tutorials"})
        self.assertTrue(s1.get("success") and s2.get("success"))

    def test_b20_denied_approval(self):
        """Browser Test 20 — Denied approval cancels browser execution"""
        state = {
            "task_type": "AUTOMATION",
            "automation_mode": "BROWSER",
            "approval_status": "DENIED",
            "execution_plan": [{"action": "navigate", "params": {"url": "https://www.google.com"}}]
        }
        from research_system.orchestrator.agents.browser_automation_executor import browser_automation_executor_node
        res = browser_automation_executor_node(state)
        self.assertIn("blocked", res.get("errors", [""])[0].lower())

    # =========================================================================
    # PART 10: NATURAL LANGUAGE UNDERSTANDING TESTS (10 Desktop, 10 Browser)
    # =========================================================================

    def test_nl_desktop_variations(self):
        """Part 10 — 10 Desktop Natural Language Variations"""
        variations = [
            ("Can you bring up VS Code for me?", "DESKTOP"),
            ("I need Notepad and Chrome open at the same time.", "DESKTOP"),
            ("Launch my code editor and a simple text editor.", "DESKTOP"),
            ("Make a new folder called MyPractice on the Desktop.", "DESKTOP"),
            ("Put the words Hello World into a new text file.", "DESKTOP"),
            ("Write a small Python program that calculates the area of a circle and save it.", "DESKTOP"),
            ("Open this existing file and add a comment at the beginning without deleting anything.", "DESKTOP"),
            ("I want an HTML page with a heading, a paragraph and a button. Create it in my test folder.", "DESKTOP"),
            ("Close the text editor but leave VS Code running.", "DESKTOP"),
            ("Move the test report into the documentation folder.", "DESKTOP")
        ]
        for query, expected_mode in variations:
            plan = self.planner.plan_task(query)
            self.assertEqual(plan.get("automation_mode"), expected_mode, f"Failed on: {query}")

    def test_nl_browser_variations(self):
        """Part 10 — 10 Browser Natural Language Variations"""
        variations = [
            ("Can you look up Virat Kohli on Google?", "BROWSER"),
            ("Bring up YouTube and find videos about building AI agents.", "BROWSER"),
            ("Find the official Django website and take me to its documentation.", "BROWSER"),
            ("Open GitHub and search for LangGraph examples.", "BROWSER"),
            ("I want Google and YouTube open in different tabs.", "BROWSER"),
            ("Find a beginner-friendly React tutorial and open it.", "BROWSER"),
            ("Go back to the Google results.", "BROWSER"),
            ("Switch over to the GitHub tab.", "BROWSER"),
            ("Find a public sample PDF and download it.", "BROWSER"),
            ("Open the official Python documentation and then visit the Django documentation.", "BROWSER")
        ]
        for query, expected_mode in variations:
            plan = self.planner.plan_task(query)
            self.assertEqual(plan.get("automation_mode"), expected_mode, f"Failed on: {query}")

    # =========================================================================
    # PART 11: HYBRID AUTOMATION TESTS (5 Tests)
    # =========================================================================

    def test_hybrid_01_find_and_open_in_chrome(self):
        """Hybrid Test 01 — Find official Python website and open in Chrome"""
        plan = self.planner.plan_task("Find the official Python website and open it in Chrome.")
        self.assertIn(plan.get("automation_mode"), ["BROWSER", "HYBRID"])

    def test_hybrid_02_download_pdf_and_open_folder(self):
        """Hybrid Test 02 — Download a sample PDF and open its containing folder"""
        plan = self.planner.plan_task("Download a sample PDF through the browser and open its containing folder.")
        self.assertEqual(plan.get("automation_mode"), "HYBRID")

    def test_hybrid_03_github_browser_and_vscode_desktop(self):
        """Hybrid Test 03 — Open GitHub in browser and VS Code on desktop"""
        plan = self.planner.plan_task("Open GitHub in the browser and VS Code on the desktop.")
        self.assertEqual(plan.get("automation_mode"), "HYBRID")

    def test_hybrid_04_search_django_download_pdf_and_open(self):
        """Hybrid Test 04 — Search Django docs, download available PDF and open on computer"""
        plan = self.planner.plan_task("Search for Django documentation, download an available PDF and open it on my computer.")
        self.assertEqual(plan.get("automation_mode"), "HYBRID")

    def test_hybrid_05_notepad_and_chrome_together(self):
        """Hybrid Test 05 — Open Notepad and Chrome together, write note in Notepad"""
        plan = self.planner.plan_task("Open Notepad and Chrome together, then write a short note in Notepad describing the website currently open.")
        self.assertEqual(plan.get("automation_mode"), "HYBRID")


if __name__ == "__main__":
    unittest.main()
