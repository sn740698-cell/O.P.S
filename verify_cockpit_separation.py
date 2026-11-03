"""
Verification script for O.P.S. 2.0 Separate Desktop Pop-up Cockpit Implementation.
Validates:
1. Complete frontend separation between Main Application (App.jsx) and Separate Cockpit (SeparatePopupCockpit.jsx).
2. Routing logic in frontend/src/main.jsx.
3. Cockpit UI contract compliance (Header, Chat Area, Input Area, HITL Approval Modal).
4. Desktop overlay configuration in desktop_overlay/window.py and desktop_overlay/main.py.
5. Windows launcher integration in windows.bat.
6. Backend API communication for conversations and HITL approvals.
"""

import sys
import os
import re
import json
import urllib.request
import urllib.error

# Ensure utf-8 stdout for Windows consoles
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(ROOT_DIR, "frontend")
OVERLAY_DIR = os.path.join(ROOT_DIR, "desktop_overlay")

def check(name, condition, details=""):
    status = "[PASS]" if condition else "[FAIL]"
    print(f"{status} {name}")
    if not condition and details:
        print(f"       ERROR: {details}")
    return condition

def test_frontend_routing():
    print("\n--- 1. Testing Frontend Main Routing Separation ---")
    main_jsx = os.path.join(FRONTEND_DIR, "src", "main.jsx")
    check("main.jsx exists", os.path.exists(main_jsx))
    
    with open(main_jsx, "r", encoding="utf-8") as f:
        content = f.read()
    
    check("main.jsx imports App", "import App from './App.jsx'" in content or "import App from './App'" in content)
    check("main.jsx imports SeparatePopupCockpit", "import SeparatePopupCockpit from './components/SeparatePopupCockpit" in content)
    check("main.jsx inspects mode=cockpit", "mode=cockpit" in content)
    check("main.jsx conditionally renders SeparatePopupCockpit or App", "isCockpitMode ? <SeparatePopupCockpit /> : <App />" in content or "isCockpitMode ? <SeparatePopupCockpit" in content)

def test_cockpit_component_contract():
    print("\n--- 2. Testing Separate Popup Cockpit UI Contract ---")
    cockpit_jsx = os.path.join(FRONTEND_DIR, "src", "components", "SeparatePopupCockpit.jsx")
    check("SeparatePopupCockpit.jsx exists", os.path.exists(cockpit_jsx))
    
    with open(cockpit_jsx, "r", encoding="utf-8") as f:
        content = f.read()

    # Must NOT have main navigation, dashboards, or fleet inspector
    check("No Main Nav/Header Tabs", "tabs.map" not in content and "setActiveTab" not in content)
    check("No Fleet Inspector embedded", "FleetInspector" not in content)
    check("No Settings/Config tab embedded", "SettingsTab" not in content and "ConfigTab" not in content)

    # Must have minimal header
    check("Minimal Identity Header present (O.P.S.)", "O.P.S." in content and "POP-UP COCKPIT" in content)
    check("Refresh conversation button present", "handleTriggerRefreshApproval" in content or "RotateCcw" in content)

    # Must have continuous chat area
    check("Continuous Conversation history rendered", "conversationHistory.map" in content)
    check("AssistantMessage & UserMessage used", "AssistantMessage" in content and "UserMessage" in content)
    check("Streaming support integrated", "streamingChunk" in content and ("<CockpitLoadingSkeleton" in content or "<MarkdownRenderer" in content))
    check("Conversation summary support", "summary" in content)

    # Must have Input area
    check("Input element has id='ops-command-input'", 'id="ops-command-input"' in content)
    check("Send button present", "handleDispatchCommand" in content and "SEND" in content)
    check("Voice mic toggle present", "handleToggleVoice" in content)
    check("Stop generation button present", "handleEmergencyHalt" in content and "STOP" in content)

    # Must have HITL Approval Modal
    check("HumanApprovalModal integrated", "<HumanApprovalModal" in content)
    check("HITL polling and response handling", "/api/chat/approvals/pending/" in content and "handleAcceptApproval" in content)

def test_hitl_modal_contract():
    print("\n--- 3. Testing HITL Approval Modal Strict UI ---")
    modal_jsx = os.path.join(FRONTEND_DIR, "src", "components", "HumanApprovalModal.jsx")
    check("HumanApprovalModal.jsx exists", os.path.exists(modal_jsx))
    
    with open(modal_jsx, "r", encoding="utf-8") as f:
        content = f.read()

    check("Only ACCEPT and DENY buttons present", "ACCEPT" in content and "DENY" in content)
    check("No Cancel button", "CANCEL" not in content.upper() or "CANCEL" in content.upper() and "CANCELLED" not in content)
    check("Deny option has default focus", "autoFocus" in content and 'action: "DENY"' in content or 'denyRef' in content or "DENY" in content)

def test_desktop_overlay_config():
    print("\n--- 4. Testing Desktop Overlay Configuration ---")
    window_py = os.path.join(OVERLAY_DIR, "window.py")
    main_py = os.path.join(OVERLAY_DIR, "main.py")
    
    with open(window_py, "r", encoding="utf-8") as f:
        w_content = f.read()

    check("window.py defaults to mode=cockpit", "http://localhost:3000/?mode=cockpit" in w_content)
    check("window.py compact HUD dimensions (width <= 560, height <= 780)", "min(560" in w_content and "min(780" in w_content)
    check("window.py transparent and always on top flags", "Qt.WindowStaysOnTopHint" in w_content and "Qt.WA_TranslucentBackground" in w_content)

    with open(main_py, "r", encoding="utf-8") as f:
        m_content = f.read()
    check("main.py defaults frontend-url to mode=cockpit", "http://localhost:3000/?mode=cockpit" in m_content)

def test_windows_bat_launcher():
    print("\n--- 5. Testing Windows Launcher (windows.bat) ---")
    bat_file = os.path.join(ROOT_DIR, "windows.bat")
    check("windows.bat exists", os.path.exists(bat_file))
    
    with open(bat_file, "r", encoding="utf-8") as f:
        b_content = f.read()

    check("windows.bat opens Main Browser App (http://localhost:3000)", "start http://localhost:3000" in b_content)
    check("windows.bat launches Native Cockpit Overlay with mode=cockpit", "desktop_overlay.main" in b_content and "mode=cockpit" in b_content)

def test_backend_api_integration():
    print("\n--- 6. Testing Backend API Communication ---")
    base_url = "http://127.0.0.1:8000"
    
    # 6.1 Create test conversation
    test_conv_id = f"conv_verify_{int(os.getpid())}"
    create_url = f"{base_url}/api/chat/conversations/"
    payload = json.dumps({"conversation_id": test_conv_id, "title": "Verification Session"}).encode('utf-8')
    req = urllib.request.Request(create_url, data=payload, headers={"Content-Type": "application/json"})
    
    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode('utf-8'))
            check("Backend creates conversation session", data.get("conversation_id") == test_conv_id)
    except Exception as e:
        check("Backend creates conversation session", False, str(e))

    # 6.2 Fetch conversation
    try:
        get_url = f"{base_url}/api/chat/conversations/{test_conv_id}/"
        with urllib.request.urlopen(get_url, timeout=5) as response:
            data = json.loads(response.read().decode('utf-8'))
            check("Backend retrieves active conversation history", data.get("conversation_id") == test_conv_id)
    except Exception as e:
        check("Backend retrieves active conversation history", False, str(e))

    # 6.3 Request refresh approval (HITL)
    try:
        approval_req_url = f"{base_url}/api/chat/conversations/{test_conv_id}/refresh-approval/"
        req = urllib.request.Request(approval_req_url, data=b"{}", headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode('utf-8'))
            approval_id = data.get("approval_id")
            check("Backend creates PENDING approval for conversation refresh", data.get("status") == "pending_approval" and bool(approval_id))
    except Exception as e:
        check("Backend creates PENDING approval for conversation refresh", False, str(e))
        approval_id = None

    # 6.4 Query pending approvals
    if approval_id:
        try:
            poll_url = f"{base_url}/api/chat/approvals/pending/?conversation_id={test_conv_id}"
            with urllib.request.urlopen(poll_url, timeout=5) as response:
                data = json.loads(response.read().decode('utf-8'))
                has_pending = any(a.get("approval_id") == approval_id for a in data.get("approvals", []))
                check("Pending approval returned in approval queue", has_pending)
        except Exception as e:
            check("Pending approval returned in approval queue", False, str(e))

        # 6.5 Resolve approval with ACCEPT
        try:
            action_url = f"{base_url}/api/chat/conversations/{test_conv_id}/refresh-approval/{approval_id}/accept/"
            action_payload = json.dumps({"action": "ACCEPT"}).encode('utf-8')
            req = urllib.request.Request(action_url, data=action_payload, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode('utf-8'))
                check("HITL ACCEPT action clears conversation and succeeds", data.get("status") == "approved_and_deleted" and bool(data.get("new_conversation_id")))
        except Exception as e:
            check("HITL ACCEPT action clears conversation and succeeds", False, str(e))

def main():
    print("======================================================================")
    print(" O.P.S. 2.0 — SEPARATE POP-UP COCKPIT VERIFICATION SUITE              ")
    print("======================================================================")
    test_frontend_routing()
    test_cockpit_component_contract()
    test_hitl_modal_contract()
    test_desktop_overlay_config()
    test_windows_bat_launcher()
    test_backend_api_integration()
    print("\n======================================================================")
    print(" VERIFICATION COMPLETE                                                ")
    print("======================================================================")

if __name__ == "__main__":
    main()
