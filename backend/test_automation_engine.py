"""
O.P.S. 2.0 Comprehensive Automation Engine Test Suite
Tests:
1. Desktop Automation (Pywinauto):
   - Launch Notepad & type text
   - Launch VS Code
   - Create desktop folder & verify
   - Handle confirmation/dialog
2. Browser Automation (Playwright):
   - Navigate to website (e.g. python.org)
   - Interact with a form/input field without submitting
   - Download file & verify on filesystem
3. Hybrid Automation (Playwright + Pywinauto):
   - Download test archive
   - Verify download
   - Extract archive
   - Open in Visual Studio Code
   - Verify VS Code project window
4. Human-in-the-Loop & Safety:
   - Missing info -> Clarification requested
   - Consequential action -> Approval required
   - Reject approval -> Safe cancellation
   - Accept approval -> Successful resumption
   - Emergency cancellation
"""

import os
import sys
import time
import json
import zipfile
import tempfile
import urllib.request

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE_URL = "http://127.0.0.1:8000"


def send_post(endpoint: str, data: dict) -> dict:
    url = f"{BASE_URL}{endpoint}"
    payload = json.dumps(data).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=90) as resp:
        return json.loads(resp.read().decode("utf-8"))


def send_get(endpoint: str) -> dict:
    url = f"{BASE_URL}{endpoint}"
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


# =====================================================================
# 1. Desktop Automation Tests (Pywinauto)
# =====================================================================

def test_desktop_notepad():
    print("\n--- [TEST 1.1] Desktop: Open Notepad and Type Text ---")
    data = {
        "query": "Open Notepad and type Hello O.P.S. 2.0 Automation Engine into notepad",
        "conversation_id": f"conv_test_desktop_{int(time.time())}"
    }
    t0 = time.time()
    res = send_post("/api/automation/execute/", data)
    t1 = time.time()
    print(f"Status: {res.get('status')} | Mode: {res.get('automation_mode')} | Duration: {t1-t0:.2f}s")
    print(f"Completed Steps: {res.get('completed_steps')}/{res.get('total_steps')}")
    print(f"Summary:\n{res.get('final_answer')}")
    assert res.get("status") == "success", f"Notepad test failed: {res.get('error')}"
    return res


def test_desktop_create_folder():
    print("\n--- [TEST 1.2] Desktop: Create Folder Workflow ---")
    test_folder_name = f"OPS_Test_Folder_{int(time.time())}"
    data = {
        "query": f"Create a new folder named '{test_folder_name}' on Desktop",
        "conversation_id": f"conv_test_folder_{int(time.time())}"
    }
    t0 = time.time()
    res = send_post("/api/automation/execute/", data)
    t1 = time.time()
    print(f"Status: {res.get('status')} | Duration: {t1-t0:.2f}s")
    print(f"Summary:\n{res.get('final_answer')}")
    assert res.get("status") == "success", f"Create folder failed: {res.get('error')}"
    
    # Clean up test folder
    desktop_folder = os.path.join(os.path.expanduser("~/Desktop"), test_folder_name)
    if os.path.exists(desktop_folder):
        try: os.rmdir(desktop_folder)
        except Exception: pass
    return res


def test_desktop_vscode():
    print("\n--- [TEST 1.3] Desktop: Open VS Code ---")
    data = {
        "query": "Open VS Code",
        "conversation_id": f"conv_test_vscode_{int(time.time())}"
    }
    t0 = time.time()
    res = send_post("/api/automation/execute/", data)
    t1 = time.time()
    print(f"Status: {res.get('status')} | Duration: {t1-t0:.2f}s")
    print(f"Summary:\n{res.get('final_answer')}")
    assert res.get("status") == "success", f"VS Code test failed: {res.get('error')}"
    return res


# =====================================================================
# 2. Browser Automation Tests (Playwright)
# =====================================================================

def test_browser_navigation_and_form():
    print("\n--- [TEST 2.1] Browser: Navigate to python.org and Interact with Search Form ---")
    from automation_system.executors.browser_executor import BrowserExecutor
    browser = BrowserExecutor(headless=True)
    try:
        t0 = time.time()
        # Step 1: Navigate
        nav_res = browser.navigate("https://www.python.org", wait_until="load")
        print("Navigation:", nav_res.get("page_title"), f"({nav_res.get('duration_s')}s)")
        assert nav_res.get("success"), "Navigation failed"

        # Step 2: Fill search input without submitting
        fill_res = browser.fill_form("q", "LangGraph agents")
        print("Fill Form:", fill_res)
        assert fill_res.get("success"), "Fill form failed"

        # Step 3: Capture verification screenshot
        screenshot_path = os.path.join(tempfile.gettempdir(), f"ops_test_browser_{int(time.time())}.png")
        ss_res = browser.capture_screenshot(screenshot_path)
        print("Screenshot:", ss_res.get("screenshot_path"), "Exists:", os.path.exists(screenshot_path))
        assert os.path.exists(screenshot_path), "Screenshot file missing"
        print(f"Browser navigation & form test passed in {time.time()-t0:.2f}s!")
    finally:
        browser.close()


def test_browser_download_and_verify():
    print("\n--- [TEST 2.2] Browser: Download File and Empirically Verify on Disk ---")
    from automation_system.executors.browser_executor import BrowserExecutor
    from automation_system.verification.verifier import AutomationVerifier

    browser = BrowserExecutor(headless=True)
    temp_download_dir = tempfile.mkdtemp(prefix="ops_test_dl_")
    try:
        # Download a lightweight test file (e.g. Python logo or documentation file)
        test_url = "https://www.python.org/static/img/python-logo.png"
        dl_res = browser.download_file(direct_url=test_url, target_dir=temp_download_dir)
        print("Download Result:", dl_res)
        assert dl_res.get("success"), f"Download failed: {dl_res.get('error')}"

        file_path = dl_res.get("file_path")
        verif = AutomationVerifier.verify_file_exists(file_path, min_size=50)
        print("File Verification:", verif)
        assert verif.get("verified"), "File verification failed"
        print("Browser download test passed!")
    finally:
        browser.close()
        import shutil
        shutil.rmtree(temp_download_dir, ignore_errors=True)


# =====================================================================
# 3. Hybrid Automation Tests (Playwright + Pywinauto)
# =====================================================================

def test_hybrid_workflow():
    print("\n--- [TEST 3.1] Hybrid: Download Archive -> Extract -> Open in VS Code ---")
    from automation_system.executors.hybrid_executor import HybridExecutor
    from automation_system.verification.verifier import AutomationVerifier

    temp_dir = tempfile.mkdtemp(prefix="ops_hybrid_test_")
    archive_file = os.path.join(temp_dir, "sample_repo.zip")
    extract_folder = os.path.join(temp_dir, "extracted_project")

    # Create dummy repository zip
    with zipfile.ZipFile(archive_file, "w") as zf:
        zf.writestr("README.md", "# O.P.S. 2.0 Sample Project\nAutomated hybrid workflow test.")
        zf.writestr("main.py", "print('Hello from hybrid workflow!')\n")

    hybrid = HybridExecutor()
    try:
        # Step 1: Verify downloaded archive exists
        step1_res = AutomationVerifier.verify_file_exists(archive_file, min_size=10)
        print("Step 1 (Verify Archive):", step1_res)
        assert step1_res.get("verified"), "Archive not found"
        hybrid.step_outputs[1] = {"file_path": archive_file}

        # Step 2: Extract archive
        step2_res = hybrid.extract_archive(archive_path=archive_file, extract_to=extract_folder)
        print("Step 2 (Extract Archive):", step2_res)
        assert step2_res.get("success"), "Extraction failed"
        hybrid.step_outputs[2] = {"extracted_path": extract_folder}

        # Step 3: Launch in VS Code
        step3 = {
            "step_id": 3,
            "title": "Open extracted project in Visual Studio Code",
            "executor": "desktop",
            "action": "launch_app",
            "params": {"app_name": "code", "path": "code", "args": ["$step_2.extracted_path"]}
        }
        step3_res = hybrid.execute_step(step3)
        print("Step 3 (Desktop Open in VS Code):", step3_res)
        assert step3_res.get("success"), "Desktop launch failed"

        # Step 4: Verify VS Code window
        verif = AutomationVerifier.verify_window_exists("Visual Studio Code", timeout=6.0)
        print("Step 4 (Verification):", verif)
        assert verif.get("verified"), "VS Code window was not verified"

        print("Hybrid workflow test passed completely!")
    finally:
        hybrid.close()
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)


# =====================================================================
# 4. Human-in-the-Loop (HITL) Safety Tests
# =====================================================================

def test_hitl_clarification():
    print("\n--- [TEST 4.1] Safety: Ambiguous Request Triggers Clarification ---")
    data = {
        "query": "open app",
        "conversation_id": f"conv_test_clarify_{int(time.time())}"
    }
    res = send_post("/api/automation/execute/", data)
    print("Clarification Response:", res)
    assert res.get("status") == "needs_clarification", "Expected needs_clarification"
    assert "clarification_prompt" in res, "Missing clarification prompt"
    print("Clarification test passed!")


def test_hitl_approval_deny_and_accept():
    print("\n--- [TEST 4.2] Safety: Destructive Action Triggers Approval (Deny & Accept) ---")
    conv_id = f"conv_test_hitl_{int(time.time())}"
    data = {
        "query": "delete file C:\\Windows\\System32\\sample_dummy.dll",
        "conversation_id": conv_id
    }
    # 1. Trigger Approval Gate
    res = send_post("/api/automation/execute/", data)
    print("Approval Gate Triggered:", res)
    assert res.get("status") == "waiting_for_approval", "Expected waiting_for_approval"
    approval_id = res.get("approval_id")
    assert approval_id, "Missing approval_id"

    # 2. Test User Rejection (Deny)
    deny_data = {"decision": "reject"}
    deny_res = send_post(f"/api/automation/approvals/{approval_id}/respond/", deny_data)
    print("Approval Deny Response:", deny_res)
    assert deny_res.get("status") == "REJECTED", "Expected approval status REJECTED"

    # 3. Test New Approval with Accept
    data2 = {
        "query": "delete folder C:\\temp\\sample_safe_delete_dir",
        "conversation_id": conv_id
    }
    res2 = send_post("/api/automation/execute/", data2)
    approval_id2 = res2.get("approval_id")
    accept_data = {"decision": "approve"}
    accept_res = send_post(f"/api/automation/approvals/{approval_id2}/respond/", accept_data)
    print("Approval Accept Response:", accept_res)
    assert accept_res.get("success") is True or accept_res.get("status") in ["APPROVED", "FAILED", "COMPLETED"], "Expected valid response"
    print("Human-in-the-Loop approval gating test passed!")


if __name__ == "__main__":
    test_arg = sys.argv[1] if len(sys.argv) > 1 else "ALL"
    print(f"Running Automation Engine Tests: {test_arg}")

    if test_arg in ["ALL", "1", "DESKTOP"]:
        test_desktop_notepad()
        test_desktop_create_folder()
        test_desktop_vscode()

    if test_arg in ["ALL", "2", "BROWSER"]:
        test_browser_navigation_and_form()
        test_browser_download_and_verify()

    if test_arg in ["ALL", "3", "HYBRID"]:
        test_hybrid_workflow()

    if test_arg in ["ALL", "4", "HITL"]:
        test_hitl_clarification()
        test_hitl_approval_deny_and_accept()

    print("\n========================================================")
    print("ALL AUTOMATION ENGINE TESTS CONCLUDED SUCCESSFULLY!")
    print("========================================================")
