"""
O.P.S. 2.0 Automation Engine API Views
Provides endpoints for task planning, execution, status, cancellation, and HITL approvals.
"""

import json
import time
import logging
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from automation_system.services.automation_service import AutomationService
from automation_system.models import AutomationTask
from research_system.models import PendingApproval

logger = logging.getLogger("OPS.AutomationViews")


@csrf_exempt
def automation_status(request):
    """
    GET /api/automation/status/
    Health and capability check for Pywinauto and Playwright executors.
    """
    pywinauto_ok = False
    playwright_ok = False
    try:
        import pywinauto
        pywinauto_ok = True
    except Exception:
        pass

    try:
        from playwright.sync_api import sync_playwright
        playwright_ok = True
    except Exception:
        pass

    return JsonResponse({
        "status": "online",
        "engine": "O.P.S. 2.0 Automation Engine",
        "executors": {
            "desktop_pywinauto": "READY" if pywinauto_ok else "UNAVAILABLE",
            "browser_playwright": "READY" if playwright_ok else "UNAVAILABLE"
        },
        "supported_modes": ["DESKTOP", "BROWSER", "HYBRID"],
        "timestamp": time.time()
    })


@csrf_exempt
def execute_automation(request):
    """
    POST /api/automation/execute/
    Creates, plans, and immediately executes an automation task (or pauses for approval).
    """
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed. Use POST."}, status=405)

    try:
        data = json.loads(request.body.decode("utf-8")) if request.body else {}
    except Exception:
        data = {}

    query = data.get("query") or data.get("content") or data.get("prompt") or ""
    if not query.strip():
        return JsonResponse({"error": "Query or directive is required."}, status=400)

    conversation_id = data.get("conversation_id") or f"conv_auto_{int(time.time())}"
    task_id = data.get("task_id")

    # Step 1: Create and plan
    plan_res = AutomationService.create_and_plan_task(
        user_request=query,
        conversation_id=conversation_id,
        task_id=task_id
    )

    # If clarification is needed
    if plan_res.get("status") == "NEEDS_CLARIFICATION":
        return JsonResponse({
            "status": "needs_clarification",
            "conversation_id": conversation_id,
            "task_id": plan_res.get("task_id"),
            "clarification_prompt": plan_res.get("clarification_prompt"),
            "content": f"⚠️ **Clarification Required**: {plan_res.get('clarification_prompt')}",
            "response": f"⚠️ **Clarification Required**: {plan_res.get('clarification_prompt')}",
            "final_answer": f"⚠️ **Clarification Required**: {plan_res.get('clarification_prompt')}"
        }, status=200)

    # If approval is needed
    if plan_res.get("status") == "WAITING_FOR_APPROVAL":
        return JsonResponse({
            "status": "waiting_for_approval",
            "conversation_id": conversation_id,
            "task_id": plan_res.get("task_id"),
            "approval_id": plan_res.get("approval_id"),
            "approval_reason": plan_res.get("approval_reason"),
            "content": f"🛑 **Human Approval Required**: {plan_res.get('approval_reason')}",
            "response": f"🛑 **Human Approval Required**: {plan_res.get('approval_reason')}",
            "final_answer": f"🛑 **Human Approval Required**: {plan_res.get('approval_reason')}",
            "steps": plan_res.get("steps")
        }, status=200)

    # Step 2: Execute task
    exec_res = AutomationService.execute_task(plan_res.get("task_id"))
    return JsonResponse({
        "status": "success" if exec_res.get("success") else "failed",
        "task_id": plan_res.get("task_id"),
        "conversation_id": conversation_id,
        "automation_mode": exec_res.get("automation_mode"),
        "completed_steps": exec_res.get("completed_steps"),
        "total_steps": exec_res.get("total_steps"),
        "content": exec_res.get("final_answer"),
        "response": exec_res.get("final_answer"),
        "final_answer": exec_res.get("final_answer"),
        "step_results": exec_res.get("step_results"),
        "error": exec_res.get("error")
    }, status=200 if exec_res.get("success") else 500)


@csrf_exempt
def plan_automation(request):
    """
    POST /api/automation/plan/
    Generates a structured automation plan without immediately executing it.
    """
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed. Use POST."}, status=405)

    try:
        data = json.loads(request.body.decode("utf-8")) if request.body else {}
    except Exception:
        data = {}

    query = data.get("query") or data.get("content") or ""
    conversation_id = data.get("conversation_id") or f"conv_auto_{int(time.time())}"

    plan_res = AutomationService.create_and_plan_task(
        user_request=query,
        conversation_id=conversation_id
    )
    return JsonResponse(plan_res, status=200)


@csrf_exempt
def task_detail(request, task_id):
    """
    GET  /api/automation/tasks/<task_id>/  - Returns task state and plan
    POST /api/automation/tasks/<task_id>/cancel/ - Aborts task
    """
    task = AutomationTask.objects.filter(task_id=task_id).first()
    if not task:
        return JsonResponse({"error": f"Task {task_id} not found"}, status=404)

    if request.method == "POST" and "cancel" in request.path:
        res = AutomationService.cancel_task(task_id)
        return JsonResponse(res)

    return JsonResponse({"task": task.to_dict()}, status=200)


@csrf_exempt
def respond_approval(request, approval_id):
    """
    POST /api/automation/approvals/<approval_id>/respond/
    Submits user approval or rejection for an automation task gate.
    """
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed. Use POST."}, status=405)

    try:
        data = json.loads(request.body.decode("utf-8")) if request.body else {}
    except Exception:
        data = {}

    decision = data.get("decision", "approve").lower()
    approved = decision in ["approve", "accept", "yes", "true"]

    res = AutomationService.resume_after_approval(approval_id, approved=approved)
    return JsonResponse(res, status=200)
