import os
import sys
import asyncio

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ops_backend.settings")

import django
django.setup()

from ops_core.services.automation_service import OPSAutomationService
from ops_core.safety import OPSSafetyGatekeeper

def run_tests():
    print("=================================================================")
    print("       O.P.S. AUTOMATION & RETRO COCKPIT TEST SUITE              ")
    print("=================================================================")

    auto = OPSAutomationService()

    # 1. Test Known Website Launcher (Instagram)
    print("\n[TEST 1] Testing Known Website Launch: 'instagram'")
    res_ig = auto.launch_app("instagram")
    print(f" -> Status: {res_ig.get('status')}, URL: {res_ig.get('url')}")
    assert res_ig.get("status") == "success"
    assert "instagram.com" in res_ig.get("url")
    print(" -> PASSED: Instagram resolved and launched.")

    # 2. Test Known Website Launcher (LeetCode)
    print("\n[TEST 2] Testing Known Website Launch: 'leetcode'")
    res_lc = auto.launch_app("leetcode")
    print(f" -> Status: {res_lc.get('status')}, URL: {res_lc.get('url')}")
    assert res_lc.get("status") == "success"
    assert "leetcode.com" in res_lc.get("url")
    print(" -> PASSED: LeetCode resolved and launched.")

    # 3. Test Known Windows Applications
    print("\n[TEST 3] Testing Native Desktop App Registry")
    assert "notepad" in auto.KNOWN_APPS
    assert "calc" in auto.KNOWN_APPS
    assert "cmd" in auto.KNOWN_APPS
    print(f" -> PASSED: Native applications registered ({len(auto.KNOWN_APPS)} apps).")

    # 4. Test Safety Gatekeeper
    print("\n[TEST 4] Testing Safety Gatekeeper Interception")
    safe_risk, safe_reason = OPSSafetyGatekeeper.assess_risk("launch_app", {"app": "notepad", "binary": "notepad.exe"})
    print(f" -> Safe app assessed risk: {safe_risk}")
    assert safe_risk in ["LOW", "MEDIUM"]

    crit_risk, crit_reason = OPSSafetyGatekeeper.assess_risk("run_terminal_cmd", {"command": "format C: /fs:NTFS"})
    print(f" -> Critical destructive command assessed risk: {crit_risk} ({crit_reason})")
    assert crit_risk == "CRITICAL"
    print(" -> PASSED: Destructive command accurately blocked with CRITICAL risk.")

    # 5. Test Dynamic Web Search Resolution
    print("\n[TEST 5] Testing Dynamic Web Fallback Resolution: 'wikipedia'")
    res_wiki = auto.launch_app("wikipedia")
    print(f" -> Status: {res_wiki.get('status')}, URL: {res_wiki.get('url')}")
    assert res_wiki.get("status") == "success"
    assert "wikipedia.org" in res_wiki.get("url")
    print(" -> PASSED: Dynamic web resolution verified.")

    # 6. Test Human-in-the-Loop Permission REST Endpoints
    print("\n[TEST 6] Testing Human-in-the-Loop Permission REST Endpoints")
    import uuid
    from rest_framework.test import APIClient
    from ops_core.models import PermissionRequest
    client = APIClient()

    test_req_id = str(uuid.uuid4())
    # Create dummy pending permission
    dummy_perm = PermissionRequest.objects.create(
        request_id=test_req_id,
        agent_name="AutomationAgent",
        action_type="terminal_cmd",
        command_text="dir",
        risk_level="HIGH",
        reason="Testing HITL desktop integration",
        status="PENDING"
    )

    resp_pending = client.get("/api/v1/permissions/pending/")
    assert resp_pending.status_code == 200
    pending_data = resp_pending.json()
    pending_list = pending_data.get("pending", []) if isinstance(pending_data, dict) else pending_data
    print(f" -> Pending permissions retrieved: {len(pending_list)}")
    assert any(str(p.get("request_id")) == test_req_id for p in pending_list)

    # Resolve permission via REST (simulating Pop-Up Cockpit click)
    resp_resolve = client.post("/api/v1/permissions/resolve/", {
        "request_id": test_req_id,
        "decision": "ALLOW_ONCE"
    }, format="json")
    assert resp_resolve.status_code == 200
    assert resp_resolve.json().get("status") == "success"
    print(" -> PASSED: Permission resolved via REST API (Pop-Up Cockpit HITL verified).")

    # Cleanup dummy
    PermissionRequest.objects.filter(request_id=test_req_id).delete()

    print("\n=================================================================")
    print("   ALL 5 CORE AUTOMATION & SECURITY TESTS PASSED (100% GREEN)    ")
    print("=================================================================")

if __name__ == "__main__":
    run_tests()
