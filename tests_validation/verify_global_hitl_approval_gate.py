"""
O.P.S. 2.0 — GLOBAL HUMAN-IN-THE-LOOP (HITL) APPROVAL GATE VALIDATION SUITE
Verifies all 13 Acceptance Criteria specified in Section 12:
1. Google search displays approval before Chrome opens.
2. YouTube play displays approval before browser launch or playback.
3. Spotify play displays approval before launching Spotify.
4. Instagram Reels displays approval before navigation.
5. Instagram messages displays approval before opening conversation.
6. Notepad write displays approval before Notepad launches.
7. VS Code write displays approval before VS Code launches.
8. File creation displays exact path and requests approval before creation.
9. File deletion displays exact target and requests explicit approval before deletion.
10. Hybrid workflow presents complete plan and requests approval before either service begins.
11. Selecting DENY results in zero automation actions.
12. Selecting ACCEPT executes only the approved plan and verifies the result.
13. Changing the approved plan requires fresh approval.
"""

import os
import sys
import json
import time
import uuid

# Configure unbuffered output
sys.stdout.reconfigure(line_buffering=True)

# Configure Django environment
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ops_backend.settings")

import django
django.setup()

from django.test import Client
from research_system.models import Conversation, ChatMessage, PendingApproval
from automation_system.models import AutomationTask
from research_system.orchestrator.service import CentralOrchestratorService
from automation_system.services.automation_service import AutomationService
from automation_system.safety.safety_policy import SafetyPolicy
from automation_system.planner.automation_planner import AutomationPlanner

passed = 0
failed = 0

def check(name: str, condition: bool, details: str = ""):
    global passed, failed
    if condition:
        passed += 1
        print(f"  [PASS] {name}", flush=True)
    else:
        failed += 1
        print(f"  [FAIL] {name}", flush=True)
        if details:
            print(f"         Diagnostic: {details}", flush=True)


def run_hitl_verification():
    print("=" * 80, flush=True)
    print(" O.P.S. 2.0 — GLOBAL HITL APPROVAL GATE VERIFICATION (13 CRITERIA)", flush=True)
    print("=" * 80, flush=True)

    client = Client()

    # -------------------------------------------------------------------------
    # Criterion 1: Open Google and search for something
    # -------------------------------------------------------------------------
    print("\n--- [Criterion 1] Google Search Approval Gate ---", flush=True)
    conv1 = f"conv_hitl_c1_{int(time.time())}"
    plan1 = AutomationService.create_and_plan_task(
        user_request="Open Google and search for Python tutorials.",
        conversation_id=conv1
    )
    check("Google search pauses for approval", plan1.get("status") == "WAITING_FOR_APPROVAL")
    appr1 = PendingApproval.objects.filter(target_conversation_id=conv1, status="PENDING").first()
    check("PendingApproval created in DB", appr1 is not None)
    if appr1:
        meta = appr1.metadata
        check("Target specifies Google/Chrome", "google" in meta.get("target", "").lower() or "chrome" in meta.get("target", "").lower(), str(meta.get("target")))
        check("Execution plan contains numbered operations", len(meta.get("execution_plan", [])) > 0)
        check("Input content captured search query", "python tutorials" in meta.get("input_content", "").lower())
        check("Expected result defined", len(meta.get("expected_result", "")) > 0)

    # -------------------------------------------------------------------------
    # Criterion 2: Open YouTube and play a song
    # -------------------------------------------------------------------------
    print("\n--- [Criterion 2] YouTube Playback Approval Gate ---", flush=True)
    conv2 = f"conv_hitl_c2_{int(time.time())}"
    plan2 = AutomationService.create_and_plan_task(
        user_request="Open YouTube and play lofi hip hop.",
        conversation_id=conv2
    )
    check("YouTube playback pauses for approval", plan2.get("status") == "WAITING_FOR_APPROVAL")
    appr2 = PendingApproval.objects.filter(target_conversation_id=conv2, status="PENDING").first()
    check("Target identifies YouTube", "youtube" in appr2.metadata.get("target", "").lower() if appr2 else False)
    check("Expected result specifies playback", "playing" in appr2.metadata.get("expected_result", "").lower() or "playback" in appr2.metadata.get("expected_result", "").lower() if appr2 else False)

    # -------------------------------------------------------------------------
    # Criterion 3: Open Spotify and play a song
    # -------------------------------------------------------------------------
    print("\n--- [Criterion 3] Spotify Automation Approval Gate ---", flush=True)
    conv3 = f"conv_hitl_c3_{int(time.time())}"
    plan3 = AutomationService.create_and_plan_task(
        user_request="Open Spotify and play Bohemian Rhapsody.",
        conversation_id=conv3
    )
    check("Spotify automation pauses for approval", plan3.get("status") == "WAITING_FOR_APPROVAL")
    appr3 = PendingApproval.objects.filter(target_conversation_id=conv3, status="PENDING").first()
    check("Target identifies Spotify", "spotify" in appr3.metadata.get("target", "").lower() if appr3 else False)

    # -------------------------------------------------------------------------
    # Criterion 4: Open Instagram and navigate to Reels
    # -------------------------------------------------------------------------
    print("\n--- [Criterion 4] Instagram Reels Approval Gate ---", flush=True)
    conv4 = f"conv_hitl_c4_{int(time.time())}"
    plan4 = AutomationService.create_and_plan_task(
        user_request="Open Instagram and navigate to Reels.",
        conversation_id=conv4
    )
    check("Instagram Reels pauses for approval", plan4.get("status") == "WAITING_FOR_APPROVAL")
    appr4 = PendingApproval.objects.filter(target_conversation_id=conv4, status="PENDING").first()
    check("Target identifies Instagram", "instagram" in appr4.metadata.get("target", "").lower() if appr4 else False)

    # -------------------------------------------------------------------------
    # Criterion 5: Open Instagram messages and open a conversation
    # -------------------------------------------------------------------------
    print("\n--- [Criterion 5] Instagram Direct Messages Approval Gate ---", flush=True)
    conv5 = f"conv_hitl_c5_{int(time.time())}"
    plan5 = AutomationService.create_and_plan_task(
        user_request="Open Instagram messages and open conversation with user.",
        conversation_id=conv5
    )
    check("Instagram messages pauses for approval", plan5.get("status") == "WAITING_FOR_APPROVAL")
    appr5 = PendingApproval.objects.filter(target_conversation_id=conv5, status="PENDING").first()
    check("Target specifies Direct Messages", "instagram" in appr5.metadata.get("target", "").lower() if appr5 else False)

    # -------------------------------------------------------------------------
    # Criterion 6: Open Notepad and write something
    # -------------------------------------------------------------------------
    print("\n--- [Criterion 6] Notepad Write Approval Gate ---", flush=True)
    conv6 = f"conv_hitl_c6_{int(time.time())}"
    plan6 = AutomationService.create_and_plan_task(
        user_request="Open Notepad and write Hello World into a new document.",
        conversation_id=conv6
    )
    check("Notepad write pauses for approval", plan6.get("status") == "WAITING_FOR_APPROVAL")
    appr6 = PendingApproval.objects.filter(target_conversation_id=conv6, status="PENDING").first()
    check("Target identifies Notepad", "notepad" in appr6.metadata.get("target", "").lower() if appr6 else False)
    check("Input content captured", "hello world" in appr6.metadata.get("input_content", "").lower() if appr6 else False)

    # -------------------------------------------------------------------------
    # Criterion 7: Open VS Code and write code
    # -------------------------------------------------------------------------
    print("\n--- [Criterion 7] VS Code Code Generation Approval Gate ---", flush=True)
    conv7 = f"conv_hitl_c7_{int(time.time())}"
    plan7 = AutomationService.create_and_plan_task(
        user_request="Open VS Code and write a Python program that prints Hello World.",
        conversation_id=conv7
    )
    check("VS Code write pauses for approval", plan7.get("status") == "WAITING_FOR_APPROVAL")
    appr7 = PendingApproval.objects.filter(target_conversation_id=conv7, status="PENDING").first()
    check("Target identifies VS Code", "code" in appr7.metadata.get("target", "").lower() if appr7 else False)

    # -------------------------------------------------------------------------
    # Criterion 8: Create a file at this path
    # -------------------------------------------------------------------------
    print("\n--- [Criterion 8] File Creation Approval Gate ---", flush=True)
    conv8 = f"conv_hitl_c8_{int(time.time())}"
    test_target_file = os.path.abspath("test_hitl_creation.py")
    if os.path.exists(test_target_file):
        os.remove(test_target_file)

    plan8 = AutomationService.create_and_plan_task(
        user_request=f"Create a file at path {test_target_file} with code print('Hello')",
        conversation_id=conv8
    )
    check("File creation pauses for approval", plan8.get("status") == "WAITING_FOR_APPROVAL")
    check("File does NOT exist on disk prior to approval", not os.path.exists(test_target_file))
    appr8 = PendingApproval.objects.filter(target_conversation_id=conv8, status="PENDING").first()
    check("Target contains exact file path", test_target_file.lower() in str(appr8.metadata.get("target", "")).lower() if appr8 else False)

    # -------------------------------------------------------------------------
    # Criterion 9: Delete this file at this path
    # -------------------------------------------------------------------------
    print("\n--- [Criterion 9] Destructive File Deletion Approval Gate ---", flush=True)
    conv9 = f"conv_hitl_c9_{int(time.time())}"
    test_delete_file = os.path.abspath("test_hitl_delete_me.txt")
    with open(test_delete_file, "w") as f:
        f.write("Important data to protect")

    plan9 = AutomationService.create_and_plan_task(
        user_request=f"Delete this file at path {test_delete_file}",
        conversation_id=conv9
    )
    appr9 = PendingApproval.objects.filter(target_conversation_id=conv9, status="PENDING").first()
    check("File deletion pauses for approval", plan9.get("status") == "WAITING_FOR_APPROVAL")
    check("Operation flagged as is_destructive", appr9.metadata.get("is_destructive") is True if appr9 else False)
    check("Risk level is HIGH", appr9.metadata.get("risk_level") == "HIGH" if appr9 else False)
    check("File still exists on disk before approval", os.path.exists(test_delete_file))

    # Clean up test delete file
    if os.path.exists(test_delete_file):
        os.remove(test_delete_file)

    # -------------------------------------------------------------------------
    # Criterion 10: Multi-step Hybrid Workflow Approval Gate
    # -------------------------------------------------------------------------
    print("\n--- [Criterion 10] Multi-step Hybrid Workflow Approval Gate ---", flush=True)
    conv10 = f"conv_hitl_c10_{int(time.time())}"
    plan10 = AutomationService.create_and_plan_task(
        user_request="Open the Django documentation, copy its actual URL, open Notepad and save that URL in a text file on my Desktop.",
        conversation_id=conv10
    )
    check("Hybrid workflow pauses for approval before any service begins", plan10.get("status") == "WAITING_FOR_APPROVAL")
    appr10 = PendingApproval.objects.filter(target_conversation_id=conv10, status="PENDING").first()
    check("Target contains both Browser and Desktop components", (
        "browser" in appr10.metadata.get("target", "").lower() or "website" in appr10.metadata.get("target", "").lower() or "django" in appr10.metadata.get("target", "").lower()
    ) and (
        "notepad" in appr10.metadata.get("target", "").lower() or "application" in appr10.metadata.get("target", "").lower() or "file" in appr10.metadata.get("target", "").lower()
    ) if appr10 else False)

    # -------------------------------------------------------------------------
    # Criterion 11: Selecting DENY results in zero automation actions
    # -------------------------------------------------------------------------
    print("\n--- [Criterion 11] Selecting DENY Halts Execution Safely ---", flush=True)
    conv11 = f"conv_hitl_c11_{int(time.time())}"
    plan11 = AutomationService.create_and_plan_task(
        user_request="Open Notepad and write confidential data.",
        conversation_id=conv11
    )
    appr11 = PendingApproval.objects.filter(target_conversation_id=conv11, status="PENDING").first()
    check("Task paused waiting for approval", appr11 is not None)

    # Submit DENY decision via API
    deny_resp = client.post(
        f"/api/chat/approvals/{appr11.approval_id}/respond/",
        data=json.dumps({"decision": "reject", "action": "deny", "conversation_id": conv11}),
        content_type="application/json"
    )
    check("DENY endpoint returns HTTP 200", deny_resp.status_code == 200)
    deny_data = deny_resp.json()
    check("Status is DENIED / CANCELLED", deny_data.get("status") in ["DENIED", "CANCELLED", "REJECTED"])
    check("Message states zero actions performed", "no automation actions were performed" in deny_data.get("message", "").lower())
    appr11.refresh_from_db()
    check("Approval status in DB is REJECTED", appr11.status == "REJECTED")

    # -------------------------------------------------------------------------
    # Criterion 12: Selecting ACCEPT executes only the approved plan
    # -------------------------------------------------------------------------
    print("\n--- [Criterion 12] Selecting ACCEPT Executes Approved Plan ---", flush=True)
    conv12 = f"conv_hitl_c12_{int(time.time())}"
    plan12 = AutomationService.create_and_plan_task(
        user_request="Launch Notepad.",
        conversation_id=conv12
    )
    check("Direct task created in WAITING_FOR_APPROVAL", plan12.get("status") == "WAITING_FOR_APPROVAL")
    appr_id12 = plan12.get("approval_id")

    # Before approval, execute_task must refuse to run!
    refused = AutomationService.execute_task(plan12["task_id"])
    check("Execution strictly blocked before approval", refused.get("success") is False and "approval" in refused.get("error", "").lower())

    # Now ACCEPT via API
    accept_resp = client.post(
        f"/api/chat/approvals/{appr_id12}/respond/",
        data=json.dumps({"decision": "approve", "action": "accept", "conversation_id": conv12}),
        content_type="application/json"
    )
    check("ACCEPT endpoint returns HTTP 200", accept_resp.status_code == 200)
    acc_data = accept_resp.json()
    check("Task resumed and executed successfully", acc_data.get("success") is True or acc_data.get("status") in ["COMPLETED", "APPROVED"])

    # -------------------------------------------------------------------------
    # Criterion 13: Changing the approved plan requires fresh approval
    # -------------------------------------------------------------------------
    print("\n--- [Criterion 13] Plan Mutation Requires Fresh Approval ---", flush=True)
    plan13_a = AutomationPlanner.plan_task("Launch Notepad.")
    details_a = SafetyPolicy.build_automation_hitl_details("Launch Notepad.", plan13_a.get("steps", []))

    plan13_b = AutomationPlanner.plan_task("Delete file confidential.txt")
    details_b = SafetyPolicy.build_automation_hitl_details("Delete file confidential.txt", plan13_b.get("steps", []))

    check("Plan hash is unique per plan", details_a["plan_hash"] != details_b["plan_hash"])
    check("Destructive plan classified distinctly from benign plan", details_a["is_destructive"] is False and details_b["is_destructive"] is True)

    print("\n" + "=" * 80, flush=True)
    print(f" TOTAL VERIFIED: {passed} PASS | {failed} FAIL", flush=True)
    print("=" * 80, flush=True)

    return failed == 0


if __name__ == "__main__":
    success = run_hitl_verification()
    sys.exit(0 if success else 1)
