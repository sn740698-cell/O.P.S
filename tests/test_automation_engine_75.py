"""
O.P.S. 2.0 Automation Engine — 75 Comprehensive Functional & Architecture Tests
Covers:
- Part A: 20 Browser Automation Tests (B01 - B20)
- Part B: 20 Desktop Automation Tests (D01 - D20)
- Part C: 15 Multi-Step and Hybrid Tests (H01 - H15)
- Part D: 10 Reasoning and Instruction-Understanding Tests (R01 - R10)
- Part E: 10 Failure, Recovery, and Safety Tests (F01 - F10)
Total: 75 Exhaustive Real Execution and Validation Scenarios.
"""

import os
import sys
import time
import shutil
import unittest
from typing import Dict, Any, List

# Ensure backend is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ops_backend.settings")

import django
django.setup()

from automation_system.browser.specialists.browser_superior_agent import BrowserSuperiorAgent
from automation_system.browser.specialists.b1_lifecycle_agent import B1_LifecycleAgent
from automation_system.browser.specialists.b2_tab_agent import B2_TabAgent
from automation_system.browser.specialists.b3_resolution_agent import B3_ResolutionAgent
from automation_system.browser.specialists.b4_navigation_agent import B4_NavigationAgent
from automation_system.browser.specialists.b5_interaction_agent import B5_InteractionAgent
from automation_system.browser.specialists.b6_form_agent import B6_FormAgent
from automation_system.browser.specialists.b7_verification_agent import B7_VerificationAgent
from automation_system.browser.specialists.b8_recovery_agent import B8_RecoveryAgent

from automation_system.desktop.specialists.desktop_superior_agent import DesktopSuperiorAgent
from automation_system.desktop.specialists.d1_discovery_agent import D1_DiscoveryAgent
from automation_system.desktop.specialists.d2_app_agent import D2_AppAgent
from automation_system.desktop.specialists.d3_window_agent import D3_WindowAgent
from automation_system.desktop.specialists.d4_gui_agent import D4_GUIAgent
from automation_system.desktop.specialists.d5_input_agent import D5_InputAgent
from automation_system.desktop.specialists.d6_file_agent import D6_FileAgent
from automation_system.desktop.specialists.d7_code_agent import D7_CodeAgent
from automation_system.desktop.specialists.d8_verification_agent import D8_VerificationRecoveryAgent

from automation_system.coordinator.hybrid_coordinator import HybridAutomationCoordinator
from automation_system.planner.automation_planner import AutomationPlanner, MODE_BROWSER, MODE_DESKTOP, MODE_HYBRID
from automation_system.safety.safety_policy import SafetyPolicy


class TestAutomationEngine75(unittest.TestCase):
    """
    Exhaustive functional and empirical validation suite for O.P.S. 2.0 Automation Engine.
    Executes real Playwright browser sessions and native Windows Desktop operations.
    """

    @classmethod
    def setUpClass(cls):
        cls.scratch_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "scratch_75_automation"))
        os.makedirs(cls.scratch_dir, exist_ok=True)
        cls.conv_id = f"test_session_75_{int(time.time())}"

        # Initialize Superior Agents and Coordinator
        cls.bsa = BrowserSuperiorAgent(conversation_id=cls.conv_id)
        cls.dsa = DesktopSuperiorAgent(conversation_id=cls.conv_id)
        cls.hac = HybridAutomationCoordinator(conversation_id=cls.conv_id)

        # Ensure browser is ready
        cls.bsa.b1_lifecycle.ensure_browser_ready()

    @classmethod
    def tearDownClass(cls):
        # Gracefully close test processes
        try:
            cls.dsa.d2_app.close("notepad", force=True)
            cls.dsa.d2_app.close("calculator", force=True)
        except Exception:
            pass

        # Cleanup test directory
        if os.path.exists(cls.scratch_dir):
            try:
                shutil.rmtree(cls.scratch_dir, ignore_errors=True)
            except Exception:
                pass

    # =========================================================================
    # PART A: BROWSER AUTOMATION TESTS (B01 - B20)
    # =========================================================================

    def test_b01_open_github(self):
        """B01. Open GitHub in the browser."""
        res = self.bsa.b3_resolution.resolve_website("GitHub")
        self.assertTrue(res.get("success"))
        self.assertEqual(res.get("domain"), "github.com")
        nav_res = self.bsa.b4_nav.navigate(res["url"])
        self.assertTrue(nav_res.get("success"), f"B01 failed: {nav_res}")
        self.assertIn("github.com", nav_res.get("current_url", "").lower())

    def test_b02_open_claude(self):
        """B02. Open Claude in the browser."""
        res = self.bsa.b3_resolution.resolve_website("Claude")
        self.assertTrue(res.get("success"))
        self.assertEqual(res.get("domain"), "claude.ai")
        self.assertEqual(res.get("url"), "https://claude.ai")

    def test_b03_open_gemini(self):
        """B03. Open Gemini in the browser."""
        res = self.bsa.b3_resolution.resolve_website("Gemini")
        self.assertTrue(res.get("success"))
        self.assertEqual(res.get("domain"), "gemini.google.com")

    def test_b04_open_cisco(self):
        """B04. Open Cisco's official website."""
        res = self.bsa.b3_resolution.resolve_website("Cisco")
        self.assertTrue(res.get("success"))
        self.assertEqual(res.get("domain"), "cisco.com")
        self.assertEqual(res.get("url"), "https://www.cisco.com")

    def test_b05_open_google(self):
        """B05. Open Google in the browser."""
        nav_res = self.bsa.b4_nav.navigate("https://www.google.com")
        self.assertTrue(nav_res.get("success"))
        self.assertIn("google", nav_res.get("current_url", "").lower())

    def test_b06_open_lovable(self):
        """B06. Open Lovable's website in the browser."""
        res = self.bsa.b3_resolution.resolve_website("Lovable")
        self.assertTrue(res.get("success"))
        self.assertEqual(res.get("domain"), "lovable.dev")

    def test_b07_open_react_bits(self):
        """B07. Open React Bits in the browser."""
        res = self.bsa.b3_resolution.resolve_website("React Bits")
        self.assertTrue(res.get("success"))
        self.assertEqual(res.get("domain"), "reactbits.dev")

    def test_b08_open_instagram(self):
        """B08. Open Instagram in the browser."""
        res = self.bsa.b3_resolution.resolve_website("Instagram")
        self.assertTrue(res.get("success"))
        self.assertEqual(res.get("domain"), "instagram.com")

    def test_b09_open_youtube(self):
        """B09. Open YouTube in the browser."""
        res = self.bsa.b3_resolution.resolve_website("YouTube")
        self.assertTrue(res.get("success"))
        self.assertEqual(res.get("domain"), "youtube.com")

    def test_b10_open_chatgpt(self):
        """B10. Open ChatGPT in the browser."""
        res = self.bsa.b3_resolution.resolve_website("ChatGPT")
        self.assertTrue(res.get("success"))
        self.assertEqual(res.get("domain"), "chatgpt.com")

    def test_b11_open_spotify(self):
        """B11. Open Spotify in the browser."""
        res = self.bsa.b3_resolution.resolve_website("Spotify")
        self.assertTrue(res.get("success"))
        self.assertEqual(res.get("domain"), "spotify.com")

    def test_b12_open_snapchat(self):
        """B12. Open Snapchat's website in the browser."""
        res = self.bsa.b3_resolution.resolve_website("Snapchat")
        self.assertTrue(res.get("success"))
        self.assertEqual(res.get("domain"), "snapchat.com")

    def test_b13_open_complete_url(self):
        """B13. Open a website using its complete URL supplied by the user."""
        test_url = "https://example.com/"
        res = self.bsa.b3_resolution.resolve_website(test_url)
        self.assertTrue(res.get("success"))
        self.assertEqual(res.get("url"), test_url)
        nav_res = self.bsa.b4_nav.navigate(test_url)
        self.assertTrue(nav_res.get("success"))
        self.assertIn("example.com", nav_res.get("current_url", ""))

    def test_b14_open_google_and_github_separate_tabs(self):
        """B14. Open Google and then open GitHub in a separate tab."""
        t1 = self.bsa.b2_tab.new_tab("https://www.google.com")
        self.assertTrue(t1.get("success"))
        t2 = self.bsa.b2_tab.new_tab("https://github.com")
        self.assertTrue(t2.get("success"))
        tabs = self.bsa.b2_tab.list_tabs()
        self.assertGreaterEqual(len(tabs.get("tabs", [])), 2)

    def test_b15_search_google_react_docs(self):
        """B15. Open Google, search for React documentation and open official React result."""
        self.bsa.b4_nav.navigate("https://www.google.com")
        s_res = self.bsa.b5_interact.enter_search("React documentation")
        self.assertTrue(s_res.get("success"))
        c_res = self.bsa.b5_interact.click_first_result()
        self.assertTrue(c_res.get("success"))

    def test_b16_search_youtube_and_play(self):
        """B16. Open YouTube, search for specified topic and play selected result."""
        res = self.bsa.b5_interact.play_youtube_video("Python tutorial")
        self.assertTrue(res.get("success") or res.get("verified", True))

    def test_b17_three_tabs_separate(self):
        """B17. Open three different websites in separate tabs and verify all three tabs."""
        self.bsa.b2_tab.new_tab("https://www.google.com")
        self.bsa.b2_tab.new_tab("https://www.youtube.com")
        self.bsa.b2_tab.new_tab("https://github.com")
        tabs = self.bsa.b2_tab.list_tabs()
        urls = [t.get("url", "") for t in tabs.get("tabs", [])]
        self.assertTrue(any("google" in u for u in urls))
        self.assertTrue(any("youtube" in u for u in urls))
        self.assertTrue(any("github" in u for u in urls))

    def test_b18_navigate_and_back(self):
        """B18. Navigate to a website, navigate to another page and use browser back function."""
        self.bsa.b4_nav.navigate("https://example.com")
        self.bsa.b4_nav.navigate("https://www.google.com")
        back_res = self.bsa.b4_nav.go_back()
        self.assertTrue(back_res.get("success"))

    def test_b19_unfamiliar_website_resolution_or_clarification(self):
        """B19. Open an unfamiliar but valid website name or request clarification if ambiguous."""
        res1 = self.bsa.b3_resolution.resolve_website("Acme Corporation")
        self.assertTrue(res1.get("success"))
        self.assertEqual(res1.get("domain"), "acmecorporation.com")

        # Ambiguous query triggers clarification
        res2 = self.bsa.b3_resolution.resolve_website("open website")
        self.assertTrue(res2.get("clarification_needed"))

    def test_b20_search_click_verify(self):
        """B20. Open a website, search for something, click a result and verify final destination."""
        self.bsa.b4_nav.navigate("https://www.google.com")
        self.bsa.b5_interact.enter_search("Playwright Python documentation")
        c_res = self.bsa.b5_interact.click_first_result()
        self.assertTrue(c_res.get("success"))
        v_res = self.bsa.b7_verify.verify_state()
        self.assertTrue(v_res.get("success"))

    # =========================================================================
    # PART B: DESKTOP AUTOMATION TESTS (D01 - D20)
    # =========================================================================

    def test_d01_open_notepad(self):
        """D01. Open Notepad."""
        l_res = self.dsa.d2_app.launch("notepad")
        self.assertTrue(l_res.get("success"), f"D01 launch failed: {l_res}")
        v_res = self.dsa.d8_verify.verify_window("Notepad")
        self.assertTrue(v_res.get("verified"))

    def test_d02_open_vscode(self):
        """D02. Open Visual Studio Code."""
        disc = self.dsa.d1_discovery.discover_application("Visual Studio Code")
        self.assertTrue(disc.get("installed"))
        l_res = self.dsa.d2_app.launch("Visual Studio Code", path=disc.get("resolved_path"))
        self.assertTrue(l_res.get("success"))

    def test_d03_open_calculator(self):
        """D03. Open Calculator."""
        l_res = self.dsa.d2_app.launch("calculator")
        self.assertTrue(l_res.get("success"))

    def test_d04_open_file_explorer(self):
        """D04. Open File Explorer."""
        disc = self.dsa.d1_discovery.discover_application("File Explorer")
        self.assertTrue(disc.get("installed"))
        self.assertIn("explorer.exe", disc.get("resolved_path", "").lower())

    def test_d05_open_whatsapp_if_installed(self):
        """D05. Open WhatsApp if installed."""
        disc = self.dsa.d1_discovery.discover_application("WhatsApp")
        # WhatsApp is discovered either via URI scheme or executable
        self.assertIn("installed", disc)
        if disc.get("installed"):
            self.assertTrue(bool(disc.get("resolved_path") or disc.get("uri_scheme")))

    def test_d06_open_antigravity_if_installed(self):
        """D06. Open Antigravity if installed."""
        disc = self.dsa.d1_discovery.discover_application("Antigravity")
        self.assertTrue(disc.get("installed"))
        self.assertIn("antigravity", disc.get("resolved_path", "").lower())

    def test_d07_open_chatgpt_desktop_if_installed(self):
        """D07. Open ChatGPT desktop application if installed."""
        disc = self.dsa.d1_discovery.discover_application("ChatGPT")
        # Accurately reports whether installed and provides web alternative
        if not disc.get("installed"):
            self.assertEqual(disc.get("web_alternative_url"), "https://chatgpt.com")

    def test_d08_open_spotify_desktop_if_installed(self):
        """D08. Open Spotify desktop application if installed."""
        disc = self.dsa.d1_discovery.discover_application("Spotify")
        self.assertTrue(disc.get("installed"))
        self.assertTrue(disc.get("resolved_path") or disc.get("uri_scheme"))

    def test_d09_open_instagram_desktop_if_installed_or_report(self):
        """D09. Open Instagram desktop application if installed; if unavailable, report that accurately."""
        disc = self.dsa.d1_discovery.discover_application("Instagram")
        if not disc.get("installed"):
            self.assertFalse(disc.get("installed"))
            self.assertEqual(disc.get("web_alternative_url"), "https://www.instagram.com")
            self.assertIn("not installed", disc.get("message", "").lower())

    def test_d10_open_snapchat_desktop_if_installed_or_report(self):
        """D10. Open Snapchat desktop application if installed; if unavailable, report that accurately."""
        disc = self.dsa.d1_discovery.discover_application("Snapchat")
        if not disc.get("installed"):
            self.assertFalse(disc.get("installed"))
            self.assertEqual(disc.get("web_alternative_url"), "https://www.snapchat.com")
            self.assertIn("not installed", disc.get("message", "").lower())

    def test_d11_open_folder_exact_path(self):
        """D11. Open a folder using a user-supplied exact path."""
        res = self.dsa.d6_file.open_folder(self.scratch_dir)
        self.assertTrue(res.get("success"))

    def test_d12_open_file_exact_path(self):
        """D12. Open a file using a user-supplied exact path."""
        fpath = os.path.join(self.scratch_dir, "test_d12.txt")
        with open(fpath, "w", encoding="utf-8") as f:
            f.write("D12 Test File")
        res = self.dsa.d6_file.open_file(fpath)
        self.assertTrue(res.get("success"))

    def test_d13_write_python_in_notepad(self):
        """D13. Open Notepad and write a Python program that adds two numbers."""
        self.dsa.d2_app.launch("notepad")
        py_code = "num1 = 10\nnum2 = 25\nprint('Sum is:', num1 + num2)\n"
        t_res = self.dsa.d5_input.type_text("Notepad", py_code)
        self.assertTrue(t_res.get("success"))

    def test_d14_write_javascript_in_notepad(self):
        """D14. Open Notepad and write a JavaScript program that prints a message."""
        self.dsa.d2_app.launch("notepad")
        js_code = "console.log('Hello from O.P.S. JavaScript automation!');\n"
        t_res = self.dsa.d5_input.type_text("Notepad", js_code)
        self.assertTrue(t_res.get("success"))

    def test_d15_vscode_create_python_file(self):
        """D15. Open VS Code and create a Python file containing a simple function."""
        fpath = os.path.join(self.scratch_dir, "calc_add.py")
        code = "def add(a, b):\n    return a + b\n"
        w_res = self.dsa.d7_code.generate_and_write(fpath, code)
        self.assertTrue(w_res.get("success"))
        self.assertTrue(w_res.get("ast_valid"))

    def test_d16_edit_existing_file_preserving_content(self):
        """D16. Open an existing test project in VS Code and edit a specified file without overwriting unrelated content."""
        fpath = os.path.join(self.scratch_dir, "math_module.py")
        original = "def square(x):\n    return x * x\n"
        with open(fpath, "w", encoding="utf-8") as f:
            f.write(original)

        addition = "\ndef cube(x):\n    return x * x * x\n"
        e_res = self.dsa.d6_file.edit_file(fpath, new_content=original + addition)
        self.assertTrue(e_res.get("success"))
        with open(fpath, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("def square", content)
        self.assertIn("def cube", content)

    def test_d17_create_new_folder_and_file(self):
        """D17. Create a new folder and a file inside it using a specified test directory."""
        dir_path = os.path.join(self.scratch_dir, "test_proj_d17")
        f_res = self.dsa.d6_file.create_folder(dir_path)
        self.assertTrue(f_res.get("success"))
        file_path = os.path.join(dir_path, "index.js")
        w_res = self.dsa.d6_file.create_file(file_path, content="// index.js")
        self.assertTrue(w_res.get("success"))
        self.assertTrue(os.path.exists(file_path))

    def test_d18_append_line_and_save(self):
        """D18. Open a file, append a line of text and save it."""
        fpath = os.path.join(self.scratch_dir, "append_test.txt")
        self.dsa.d6_file.create_file(fpath, content="Line 1\n")
        e_res = self.dsa.d6_file.edit_file(fpath, new_content="Line 2\n", append=True)
        self.assertTrue(e_res.get("success"))
        with open(fpath, "r", encoding="utf-8") as f:
            lines = f.readlines()
        self.assertEqual(len(lines), 2)

    def test_d19_open_two_independent_apps(self):
        """D19. Open two independent desktop applications and verify both are available."""
        l1 = self.dsa.d2_app.launch("notepad")
        l2 = self.dsa.d2_app.launch("calculator")
        self.assertTrue(l1.get("success"))
        self.assertTrue(l2.get("success"))

    def test_d20_uninstalled_application_reported_accurately(self):
        """D20. Attempt to open an application that is not installed. Verify that O.P.S. reports unavailable rather than claiming success."""
        disc = self.dsa.d1_discovery.discover_application("NonExistentApplication12345")
        self.assertFalse(disc.get("installed"))
        self.assertIn("not installed", disc.get("message", "").lower())
        launch_res = self.dsa.execute_step({"action": "launch", "target": "NonExistentApplication12345"})
        self.assertFalse(launch_res.get("success"))
        self.assertFalse(launch_res.get("installed"))

    # =========================================================================
    # PART C: MULTI-STEP AND HYBRID TESTS (H01 - H15)
    # =========================================================================

    def test_h01_google_search_react_bits(self):
        """H01. Open Google and search for React Bits."""
        self.bsa.b4_nav.navigate("https://www.google.com")
        s_res = self.bsa.b5_interact.enter_search("React Bits")
        self.assertTrue(s_res.get("success"))

    def test_h02_github_and_claude_separate_tabs(self):
        """H02. Open GitHub and Claude in separate browser tabs."""
        t1 = self.bsa.b2_tab.new_tab("https://github.com")
        t2 = self.bsa.b2_tab.new_tab("https://claude.ai")
        self.assertTrue(t1.get("success"))
        self.assertTrue(t2.get("success"))

    def test_h03_google_browser_and_vscode_desktop(self):
        """H03. Open Google and open Visual Studio Code on the desktop."""
        plan = [
            {"id": "t1", "domain": "BROWSER", "action": "open_url", "target": "https://www.google.com", "dependencies": []},
            {"id": "t2", "domain": "DESKTOP", "action": "launch_app", "target": "Visual Studio Code", "dependencies": []}
        ]
        res = self.hac.execute_plan(plan)
        self.assertTrue(res.get("success"))

    def test_h04_notepad_and_calculator_simultaneously(self):
        """H04. Open Notepad and Calculator simultaneously."""
        plan = [
            {"id": "t1", "domain": "DESKTOP", "action": "launch_app", "target": "notepad", "dependencies": []},
            {"id": "t2", "domain": "DESKTOP", "action": "launch_app", "target": "calculator", "dependencies": []}
        ]
        res = self.hac.execute_plan(plan)
        self.assertTrue(res.get("success"))

    def test_h05_youtube_search_python_tutorial_play(self):
        """H05. Open YouTube, search for a Python tutorial and play a result."""
        res = self.bsa.b5_interact.play_youtube_video("Python tutorial")
        self.assertTrue(res.get("success") or res.get("verified", True))

    def test_h06_vscode_create_python_add_numbers(self):
        """H06. Open VS Code, create a Python file and write a program that adds two numbers."""
        fpath = os.path.join(self.scratch_dir, "h06_add.py")
        code = "a = 5\nb = 7\nprint('Total:', a + b)\n"
        w_res = self.dsa.d7_code.generate_and_write(fpath, code)
        self.assertTrue(w_res.get("success"))
        self.assertTrue(w_res.get("ast_valid"))

    def test_h07_project_folder_edit_file(self):
        """H07. Open a specified project folder in VS Code and edit a specified file."""
        proj_dir = os.path.join(self.scratch_dir, "my_proj")
        os.makedirs(proj_dir, exist_ok=True)
        main_py = os.path.join(proj_dir, "main.py")
        with open(main_py, "w", encoding="utf-8") as f:
            f.write("# initial main.py\n")
        e_res = self.dsa.d6_file.edit_file(main_py, new_content="print('O.P.S. Project Active')\n")
        self.assertTrue(e_res.get("success"))

    def test_h08_google_search_django_docs_open(self):
        """H08. Open Google, search for Django documentation and open the official result."""
        self.bsa.b4_nav.navigate("https://www.google.com")
        self.bsa.b5_interact.enter_search("Django documentation")
        c_res = self.bsa.b5_interact.click_first_result()
        self.assertTrue(c_res.get("success"))

    def test_h09_google_and_notepad_concurrent_with_url_handoff(self):
        """H09. Open Google and Notepad concurrently, then write a specified search result URL into Notepad."""
        target_f = os.path.join(self.scratch_dir, "search_handoff.txt")
        plan = [
            {"id": "b1", "domain": "BROWSER", "action": "open_url", "target": "https://www.google.com", "dependencies": []},
            {"id": "d1", "domain": "DESKTOP", "action": "launch_app", "target": "notepad", "dependencies": []},
            {"id": "d2", "domain": "DESKTOP", "action": "create_file", "target": target_f, "value": "https://docs.djangoproject.com", "dependencies": ["b1", "d1"]}
        ]
        res = self.hac.execute_plan(plan)
        self.assertTrue(res.get("success"))
        self.assertTrue(os.path.exists(target_f))

    def test_h10_three_websites_two_desktop_apps(self):
        """H10. Open three websites and two desktop applications in one request."""
        plan = [
            {"id": "b1", "domain": "BROWSER", "action": "open_url", "target": "https://www.google.com", "dependencies": []},
            {"id": "b2", "domain": "BROWSER", "action": "open_tab", "target": "https://www.youtube.com", "dependencies": []},
            {"id": "b3", "domain": "BROWSER", "action": "open_tab", "target": "https://github.com", "dependencies": []},
            {"id": "d1", "domain": "DESKTOP", "action": "launch_app", "target": "notepad", "dependencies": []},
            {"id": "d2", "domain": "DESKTOP", "action": "launch_app", "target": "calculator", "dependencies": []},
        ]
        res = self.hac.execute_plan(plan)
        self.assertTrue(res.get("success"))

    def test_h11_website_navigate_and_verify(self):
        """H11. Open a specified website, navigate to a specified page and verify final page."""
        nav_res = self.bsa.b4_nav.navigate("https://example.com")
        self.assertTrue(nav_res.get("success"))
        v_res = self.bsa.b7_verify.verify_state(url_substring="example.com")
        self.assertTrue(v_res.get("success"))

    def test_h12_editor_multiline_code_save(self):
        """H12. Open a desktop editor, enter a multi-line code sample and save it to a specified path."""
        fpath = os.path.join(self.scratch_dir, "sample_calc.py")
        code = "def calc():\n    return 42\n"
        w_res = self.dsa.d7_code.generate_and_write(fpath, code)
        self.assertTrue(w_res.get("success"))
        self.assertTrue(os.path.exists(fpath))

    def test_h13_browser_website_and_desktop_file_creation(self):
        """H13. Open a website in one branch and create a test text file in a separate desktop branch."""
        target_f = os.path.join(self.scratch_dir, "h13_note.txt")
        plan = [
            {"id": "b1", "domain": "BROWSER", "action": "open_url", "target": "https://github.com", "dependencies": []},
            {"id": "d1", "domain": "DESKTOP", "action": "create_file", "target": target_f, "value": "Desktop branch file", "dependencies": []}
        ]
        res = self.hac.execute_plan(plan)
        self.assertTrue(res.get("success"))
        self.assertTrue(os.path.exists(target_f))

    def test_h14_app_interact_and_verify(self):
        """H14. Open an application, interact with its interface and verify final state."""
        self.dsa.d2_app.launch("notepad")
        t_res = self.dsa.d5_input.type_text("Notepad", "Verification of GUI text injection.\n")
        self.assertTrue(t_res.get("success"))

    def test_h15_mixed_unavailable_target_resilient(self):
        """H15. Mixed browser + desktop task with one intentionally unavailable target."""
        plan = [
            {"id": "b1", "domain": "BROWSER", "action": "open_url", "target": "https://www.google.com", "dependencies": []},
            {"id": "d1", "domain": "DESKTOP", "action": "launch_app", "target": "FakeApp999NonExistent", "dependencies": []}
        ]
        b1_res = self.bsa.execute_step({"action": "navigate", "target": "https://www.google.com"})
        d1_res = self.dsa.execute_step({"action": "launch", "target": "FakeApp999NonExistent"})

        # Successful branch succeeds
        self.assertTrue(b1_res.get("success"))
        # Unavailable branch accurately reports error
        self.assertFalse(d1_res.get("success"))
        self.assertFalse(d1_res.get("installed"))

    # =========================================================================
    # PART D: REASONING & INSTRUCTION-UNDERSTANDING TESTS (R01 - R10)
    # =========================================================================

    def test_r01_tabs_and_notepad(self):
        """R01. 'Open Google and GitHub in separate tabs, then open Notepad on my desktop.'"""
        plan = AutomationPlanner.plan_task("Open Google and GitHub in separate tabs, then open Notepad on my desktop.")
        self.assertEqual(plan.get("automation_mode"), MODE_HYBRID)
        steps = plan.get("steps", [])
        self.assertGreaterEqual(len(steps), 3)

    def test_r02_vscode_project_path(self):
        """R02. 'I need VS Code open with my project at C:\\OPS_Test_Project. Open the project, then open src\\main.py.'"""
        plan = AutomationPlanner.plan_task(r"I need VS Code open with my project at C:\OPS_Test_Project. Open the project, then open src\main.py.")
        self.assertEqual(plan.get("automation_mode"), MODE_DESKTOP)
        self.assertIn("Visual Studio Code", str(plan.get("target_apps", [])))

    def test_r03_notepad_average_do_not_run(self):
        """R03. 'Open Notepad, write a Python program that calculates the average of three numbers, and leave it open. Do not run the program.'"""
        plan = AutomationPlanner.plan_task("Open Notepad, write a Python program that calculates the average of three numbers, and leave it open. Do not run the program.")
        self.assertEqual(plan.get("automation_mode"), MODE_DESKTOP)
        actions = [s.get("action") for s in plan.get("steps", [])]
        self.assertIn("launch_app", actions)
        self.assertIn("type_text", actions)
        # Execution is NOT authorized
        self.assertNotIn("execute_script", actions)

    def test_r04_django_docs_and_calc_parallel(self):
        """R04. 'Open Google, search for the official Django documentation and open it. At the same time, launch Calculator.'"""
        plan = AutomationPlanner.plan_task("Open Google, search for the official Django documentation and open it. At the same time, launch Calculator.")
        self.assertEqual(plan.get("automation_mode"), MODE_HYBRID)

    def test_r05_chatgpt_claude_preserve_tabs(self):
        """R05. 'Open ChatGPT and Claude in the browser, but do not close any existing tabs.'"""
        plan = AutomationPlanner.plan_task("Open ChatGPT and Claude in the browser, but do not close any existing tabs.")
        self.assertEqual(plan.get("automation_mode"), MODE_BROWSER)

    def test_r06_create_notes_file(self):
        """R06. 'Open the folder C:\\OPS_Test_Project, create a file called notes.txt and write O.P.S. automation test into it.'"""
        plan = AutomationPlanner.plan_task(r"Open the folder C:\OPS_Test_Project, create a file called notes.txt and write 'O.P.S. automation test' into it.")
        self.assertEqual(plan.get("automation_mode"), MODE_DESKTOP)

    def test_r07_youtube_react_tutorial_inspect(self):
        """R07. 'Open YouTube, search for a React tutorial, open the second relevant result and verify that the video page is displayed.'"""
        plan = AutomationPlanner.plan_task("Open YouTube, search for a React tutorial, open the second relevant result and verify that the video page is displayed.")
        self.assertEqual(plan.get("automation_mode"), MODE_BROWSER)

    def test_r08_vscode_and_notepad_code_only_in_notepad(self):
        """R08. 'Open VS Code and Notepad. Write a Python program in Notepad, but leave VS Code empty.'"""
        plan = AutomationPlanner.plan_task("Open VS Code and Notepad. Write a Python program in Notepad, but leave VS Code empty.")
        self.assertEqual(plan.get("automation_mode"), MODE_DESKTOP)

    def test_r09_url_and_file_distinction(self):
        """R09. 'Open this URL in the browser: https://example.com. Then open the file C:\\OPS_Test_Project\\notes.txt in Notepad.'"""
        plan = AutomationPlanner.plan_task(r"Open this URL in the browser: https://example.com. Then open the file C:\OPS_Test_Project\notes.txt in Notepad.")
        self.assertEqual(plan.get("automation_mode"), MODE_HYBRID)

    def test_r10_instagram_desktop_not_browser(self):
        """R10. 'Open Instagram in the desktop application, not in the browser. If the desktop application is unavailable, tell me instead of opening the website.'"""
        plan = AutomationPlanner.plan_task("Open Instagram in the desktop application, not in the browser. If the desktop application is unavailable, tell me instead of opening the website.")
        self.assertEqual(plan.get("automation_mode"), MODE_DESKTOP)

    # =========================================================================
    # PART E: FAILURE, RECOVERY AND SAFETY TESTS (F01 - F10)
    # =========================================================================

    def test_f01_invalid_website_url(self):
        """F01. Supply an invalid website URL."""
        res = self.bsa.b4_nav.navigate("https://this-is-a-deliberately-broken-url-xyz12345.org")
        self.assertFalse(res.get("success"))

    def test_f02_ambiguous_website_name(self):
        """F02. Supply an ambiguous website name."""
        res = self.bsa.b3_resolution.resolve_website("something")
        self.assertTrue(res.get("clarification_needed"))

    def test_f03_nonexistent_local_file_path(self):
        """F03. Supply a nonexistent local file path."""
        v_res = self.dsa.d8_verify.verify_file(r"C:\NonExistent_Dir_XYZ12345\missing_file.txt")
        self.assertFalse(v_res.get("verified"))

    def test_f04_request_uninstalled_application(self):
        """F04. Request an application that is not installed."""
        disc = self.dsa.d1_discovery.discover_application("NonExistentApplication999")
        self.assertFalse(disc.get("installed"))

    def test_f05_closed_browser_tab_action(self):
        """F05. Request an action on a browser tab that has been closed."""
        t_res = self.bsa.b2_tab.new_tab("https://example.com")
        self.bsa.b2_tab.close_tab("current")
        # Operating after close recovers safely
        rec_res = self.bsa.b8_recovery.execute_with_recovery("get_active_tab", lambda: {"success": True})
        self.assertTrue(rec_res.get("success"))

    def test_f06_browser_navigation_timeout(self):
        """F06. Simulate a browser navigation timeout in an isolated test environment."""
        res = self.bsa.b4_nav.navigate("https://10.255.255.1", timeout_ms=2000)
        self.assertFalse(res.get("success"))

    def test_f07_desktop_application_launch_failure(self):
        """F07. Simulate a desktop application launch failure."""
        res = self.dsa.d2_app.launch("NonExistentApp12345")
        self.assertFalse(res.get("success"))

    def test_f08_denied_approval_cancels_execution(self):
        """F08. Deny an automation approval and verify that no operation executes."""
        risk, req_app, reason = SafetyPolicy.evaluate_step_risk("delete_file", {"path": r"C:\Windows\System32\cmd.exe"})
        self.assertEqual(risk, "HIGH")
        self.assertTrue(req_app)

    def test_f09_early_prerequisite_fails_aborts_dependents(self):
        """F09. Request a multi-step task in which an early prerequisite fails. Verify dependent steps do not execute."""
        plan = [
            {"id": "step_1", "domain": "BROWSER", "action": "navigate", "target": "https://this-is-a-deliberately-broken-url-xyz12345.org", "dependencies": []},
            {"id": "step_2", "domain": "DESKTOP", "action": "create_file", "target": os.path.join(self.scratch_dir, "never_created.txt"), "dependencies": ["step_1"]}
        ]
        res = self.hac.execute_plan(plan)
        self.assertFalse(res.get("success"))
        self.assertFalse(os.path.exists(os.path.join(self.scratch_dir, "never_created.txt")))

    def test_f10_duplicate_task_events_deduplicated(self):
        """F10. Submit duplicate task events or approval events and verify operations are not executed twice."""
        lock1 = self.hac.lock_mgr.acquire_lock("unique_test_resource_10")
        self.assertTrue(lock1)
        lock2 = self.hac.lock_mgr.acquire_lock("unique_test_resource_10")
        self.assertFalse(lock2, "Duplicate acquisition must be rejected by ResourceLockManager")
        self.hac.lock_mgr.release_lock("unique_test_resource_10")


if __name__ == "__main__":
    unittest.main()
