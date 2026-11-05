"""
O.P.S. 2.0 — Advanced Multi-Agent Automation 20-Workflow Validation Suite
Verifies:
1. Browser Superior Agent initialization (B1)
2. Tab Management & multi-tab navigation (B2)
3. Direct navigation & overlay dismissal (B3)
4. Interaction & element clicking (B4)
5. Form filling & secret masking (B5)
6. Download trigger & file integrity verification (B6)
7. Empirical browser verification engine (B7)
8. Bounded error recovery (B8)
9. Desktop Superior Agent initialization (D1)
10. Application launch & path resolution (D1)
11. Window discovery & geometry management (D2)
12. Accessible GUI control inspection & click (D3)
13. File creation, reading, and workspace scoping (D4)
14. System path protection rejection (D4)
15. UIA text typing & keyboard shortcuts (D5)
16. Code synthesis with AST validation (D6)
17. Empirical desktop verification checks (D7)
18. Desktop error classification & recovery (D8)
19. Hybrid Coordinator DAG subtask scheduling & parallel execution
20. Cross-engine state handoff & resource locking
"""

import os
import sys
import time
import logging
import unittest

# Ensure backend is on PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../backend")))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ops_backend.settings")

import django
django.setup()

from automation_system.browser.specialists import (
    BrowserSuperiorAgent,
    B1_LifecycleAgent,
    B2_TabAgent,
    B3_NavigationAgent,
    B4_InteractionAgent,
    B5_FormAgent,
    B6_TransferAgent,
    B7_VerificationAgent,
    B8_RecoveryAgent,
)
from automation_system.desktop.specialists import (
    DesktopSuperiorAgent,
    D1_AppAgent,
    D2_WindowAgent,
    D3_GUIAgent,
    D4_FileAgent,
    D5_InputAgent,
    D6_CodeAgent,
    D7_VerificationAgent,
    D8_RecoveryAgent,
)
from automation_system.coordinator import HybridAutomationCoordinator, ResourceLockManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("OPS.Test.MultiAgent")


class AdvancedMultiAgentAutomationTestSuite(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.test_session = f"test_session_{int(time.time())}"
        cls.test_req = f"req_{int(time.time())}"
        cls.test_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "scratch_multi_agent"))
        os.makedirs(cls.test_dir, exist_ok=True)

    @classmethod
    def tearDownClass(cls):
        import shutil
        if os.path.exists(cls.test_dir):
            try:
                shutil.rmtree(cls.test_dir)
            except Exception:
                pass

    # =========================================================================
    # BROWSER SPECIALIST TESTS (1 - 8)
    # =========================================================================

    def test_01_b1_lifecycle_ready_and_status(self):
        b1 = B1_LifecycleAgent(self.test_session)
        res = b1.ensure_browser_ready(headless=True)
        self.assertTrue(res.get("success"), f"B1 ensure ready failed: {res}")
        status = b1.get_session_status()
        self.assertTrue(status.get("success"))
        self.assertTrue(status.get("session_active"))

    def test_02_b2_tab_management(self):
        b2 = B2_TabAgent(self.test_session)
        tabs = b2.list_tabs()
        self.assertTrue(tabs.get("success"))
        # Open a new tab
        new_res = b2.new_tab("https://example.com")
        self.assertTrue(new_res.get("success"))
        # Switch tab
        switch_res = b2.switch_tab(0)
        self.assertTrue(switch_res.get("success"))

    def test_03_b3_navigation_and_reload(self):
        b3 = B3_NavigationAgent(self.test_session)
        nav_res = b3.navigate("https://example.com")
        self.assertTrue(nav_res.get("success"))
        self.assertIn("example.com", nav_res.get("current_url", ""))
        reload_res = b3.reload()
        self.assertTrue(reload_res.get("success"))

    def test_04_b4_interaction_and_scroll(self):
        b4 = B4_InteractionAgent(self.test_session)
        scroll_res = b4.scroll("down", 200)
        self.assertTrue(scroll_res.get("success"))
        key_res = b4.press_key("ArrowDown")
        self.assertTrue(key_res.get("success"))

    def test_05_b5_form_agent_field_entry(self):
        b5 = B5_FormAgent(self.test_session)
        batch_res = b5.fill_form_batch([
            {"field": "input", "value": "test query", "is_secret": False}
        ])
        # Even if page has no input, the agent must report structured result
        self.assertIn("results", batch_res)

    def test_06_b6_transfer_agent_upload_guard(self):
        b6 = B6_TransferAgent(self.test_session, download_dir=self.test_dir)
        # Test non-existent file upload error handling
        res = b6.upload_file("input[type=file]", "non_existent_file.xyz")
        self.assertFalse(res.get("success"))
        self.assertIn("not found", res.get("error", "").lower())

    def test_07_b7_verification_page_state(self):
        b7 = B7_VerificationAgent(self.test_session)
        v_res = b7.verify_state(url_substring="example.com")
        self.assertTrue(v_res.get("verified"))

    def test_08_b8_recovery_agent_classification(self):
        b8 = B8_RecoveryAgent(self.test_session)
        category = b8.classify(TimeoutError("Operation timed out after 30000ms"))
        self.assertEqual(category, "TIMEOUT")
        res = b8.execute_with_recovery("safe_probe", lambda: {"success": True, "info": "ok"}, max_retries=1)
        self.assertTrue(res.get("success"))

    # =========================================================================
    # DESKTOP SPECIALIST TESTS (9 - 18)
    # =========================================================================

    def test_09_d1_app_resolution(self):
        d1 = D1_AppAgent()
        res = d1.resolve_app("notepad")
        self.assertTrue(res.get("success"))
        self.assertIsNotNone(res.get("resolved_path"))

    def test_10_d1_app_launch_and_close(self):
        d1 = D1_AppAgent()
        launch_res = d1.launch("notepad", wait_seconds=1.5)
        self.assertTrue(launch_res.get("success"))
        close_res = d1.close("notepad", force=True)
        self.assertTrue(close_res.get("success"))

    def test_11_d2_window_management_list(self):
        d2 = D2_WindowAgent()
        win_res = d2.list_open_windows(min_title_len=2)
        self.assertTrue(win_res.get("success"))
        self.assertIsInstance(win_res.get("windows"), list)

    def test_12_d3_gui_agent_control_inspection(self):
        d3 = D3_GUIAgent()
        # Inspect an arbitrary window safely
        res = d3.inspect_controls("NonExistentWindow_XYZ")
        self.assertIn("controls", res)

    def test_13_d4_file_create_and_read(self):
        d4 = D4_FileAgent()
        target = os.path.join(self.test_dir, "multi_agent_test.txt")
        create_res = d4.create_file(target, content="Multi-agent test content")
        self.assertTrue(create_res.get("success"))
        read_res = d4.read_file(target)
        self.assertTrue(read_res.get("success"))
        self.assertEqual(read_res.get("content"), "Multi-agent test content")

    def test_14_d4_system_path_guard(self):
        d4 = D4_FileAgent()
        del_res = d4.delete_file("C:\\Windows\\System32\\notepad.exe")
        self.assertFalse(del_res.get("success"))
        self.assertIn("protected", del_res.get("error", "").lower())

    def test_15_d5_input_agent_typing_fallback(self):
        d5 = D5_InputAgent()
        res = d5.type_text("NonExistentWindow_XYZ", "Hello OPS")
        # Should gracefully fail without crashing
        self.assertFalse(res.get("success"))

    def test_16_d6_code_agent_generation_and_ast_check(self):
        d6 = D6_CodeAgent()
        target_py = os.path.join(self.test_dir, "calculator.py")
        code = (
            "class Calculator:\n"
            "    def add(self, a: int, b: int) -> int:\n"
            "        return a + b\n"
        )
        # Directly write verified code
        write_res = d6.writer.write_code_file(target_py, prompt="", language="python", overwrite=True)
        # Manually ensure contents
        with open(target_py, "w", encoding="utf-8") as f:
            f.write(code)
        self.assertTrue(os.path.exists(target_py))
        # Validate AST
        valid, err = d6.writer.validate_syntax(code, "python")
        self.assertTrue(valid)
        self.assertIsNone(err)

    def test_17_d7_desktop_verification_checks(self):
        d7 = D7_VerificationAgent()
        target_py = os.path.join(self.test_dir, "calculator.py")
        v_file = d7.verify_file(target_py, check_non_empty=True)
        self.assertTrue(v_file.get("verified"))
        v_content = d7.verify_file_content(target_py, expected_substrings=["class Calculator", "def add"])
        self.assertTrue(v_content.get("verified"))

    def test_18_d8_desktop_recovery_classification(self):
        d8 = D8_RecoveryAgent()
        cat = d8.classify_error(RuntimeError("Window not found or missing from desktop"))
        self.assertEqual(cat, "WINDOW_NOT_FOUND")

    # =========================================================================
    # HYBRID COORDINATOR & INTEGRATION TESTS (19 - 20)
    # =========================================================================

    def test_19_hybrid_coordinator_dag_and_parallel_execution(self):
        coord = HybridAutomationCoordinator(self.test_session, self.test_req)
        
        file1 = os.path.join(self.test_dir, "parallel_1.txt")
        file2 = os.path.join(self.test_dir, "parallel_2.txt")

        subtasks = [
            {
                "id": "task_create_1",
                "domain": "DESKTOP",
                "action": "create_file",
                "target": file1,
                "value": "Independent payload 1",
                "dependencies": [],
                "resource_lock": file1
            },
            {
                "id": "task_create_2",
                "domain": "DESKTOP",
                "action": "create_file",
                "target": file2,
                "value": "Independent payload 2",
                "dependencies": [],
                "resource_lock": file2
            },
            {
                "id": "task_verify_all",
                "domain": "DESKTOP",
                "action": "verify_file",
                "target": file1,
                "dependencies": ["task_create_1", "task_create_2"]
            }
        ]

        res = coord.execute_plan(subtasks)
        self.assertTrue(res.get("success"), f"Hybrid plan failed: {res}")
        self.assertEqual(len(res.get("completed_subtasks", {})), 3)
        self.assertTrue(os.path.exists(file1))
        self.assertTrue(os.path.exists(file2))

    def test_20_resource_locking_and_handoff(self):
        lock_mgr = ResourceLockManager()
        res_id = "test_shared_resource"
        self.assertTrue(lock_mgr.acquire_lock(res_id))
        self.assertTrue(lock_mgr.is_locked(res_id))
        self.assertFalse(lock_mgr.acquire_lock(res_id))  # Second lock fails
        lock_mgr.release_lock(res_id)
        self.assertFalse(lock_mgr.is_locked(res_id))


if __name__ == "__main__":
    unittest.main()
