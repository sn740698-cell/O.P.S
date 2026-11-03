"""
O.P.S. 2.0 Automation Service
High-level service interface orchestrating planning, safety approval gates,
desktop/browser/hybrid execution, verification, and live EventBus telemetry.
Compatible with LangGraph and the O.P.S. Pop-up Cockpit.
"""

import os
import time
import uuid
import logging
from typing import Dict, Any, List, Optional
from django.utils import timezone
from automation_system.models import AutomationTask
from automation_system.planner.automation_planner import AutomationPlanner, MODE_DESKTOP, MODE_BROWSER, MODE_HYBRID
from automation_system.safety.safety_policy import SafetyPolicy
from automation_system.executors.desktop_executor import DesktopExecutor
from automation_system.executors.browser_executor import BrowserExecutor
from automation_system.executors.hybrid_executor import HybridExecutor
from research_system.events.event_bus import event_bus
from research_system.models import PendingApproval, Conversation

logger = logging.getLogger("OPS.AutomationService")


class AutomationService:
    """
    Central operational service for creating, managing, and executing automation tasks.
    """

    @classmethod
    def create_and_plan_task(
        cls,
        user_request: str,
        conversation_id: str,
        task_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Creates an AutomationTask record, runs the AutomationPlanner,
        evaluates safety risk, and prepares execution state.
        """
        t0 = time.time()
        tid = task_id or f"task_auto_{int(time.time())}_{uuid.uuid4().hex[:6]}"

        event_bus.publish(
            request_id=f"req_{tid}",
            execution_id=tid,
            conversation_id=conversation_id,
            node_id="automation_planner",
            component_name="Automation Planner",
            component_type="reasoning_agent",
            event_type="PLANNING_STARTED",
            execution_status="PLANNING",
            safe_task_summary=f"Analyzing automation request: '{user_request[:60]}...'",
            tool_name="Automation Planner Engine",
            timestamp=t0
        )

        plan_result = AutomationPlanner.plan_task(user_request)
        mode = plan_result.get("automation_mode", MODE_DESKTOP)
        mode_reason = plan_result.get("mode_reason", "Automated plan generated.")
        steps = plan_result.get("steps", [])

        # Emit Mode Selected Event
        event_bus.publish(
            request_id=f"req_{tid}",
            execution_id=tid,
            conversation_id=conversation_id,
            node_id="automation_router",
            component_name="Automation Router",
            component_type="reasoning_agent",
            event_type="AUTOMATION_MODE_SELECTED",
            execution_status="RUNNING",
            safe_task_summary=f"Selected {mode} Mode: {mode_reason}",
            automation_mode=mode,
            response_mode=f"AUTO_{mode}",
            current_stage="Planning execution steps",
            tool_name=f"Automation Engine ({mode})",
            timestamp=time.time()
        )

        # Check if clarification is required
        if plan_result.get("status") == "NEEDS_CLARIFICATION":
            task = AutomationTask.objects.create(
                task_id=tid,
                conversation_id=conversation_id,
                user_request=user_request,
                task_type=mode,
                automation_mode=mode,
                execution_plan=[],
                current_step=0,
                execution_status=AutomationTask.STATUS_WAITING_FOR_APPROVAL,
                approval_status=AutomationTask.APPROVAL_PENDING,
                tool_name="Automation Planner",
                error_details=plan_result.get("clarification_prompt", "")
            )
            return {
                "status": "NEEDS_CLARIFICATION",
                "task_id": tid,
                "automation_mode": mode,
                "clarification_prompt": plan_result.get("clarification_prompt"),
                "task": task.to_dict()
            }

        # Mandatory Human-in-the-Loop (HITL) Approval Gate for ALL Automation Operations
        requires_approval = True
        hitl_details = SafetyPolicy.build_automation_hitl_details(user_request, steps, mode=mode)
        approval_reason = hitl_details["action_summary"]

        initial_status = AutomationTask.STATUS_WAITING_FOR_APPROVAL
        appr_status = AutomationTask.APPROVAL_PENDING

        task = AutomationTask.objects.create(
            task_id=tid,
            conversation_id=conversation_id,
            user_request=user_request,
            task_type=mode,
            automation_mode=mode,
            execution_plan=steps,
            current_step=0,
            execution_status=initial_status,
            approval_status=appr_status,
            tool_name=f"Pywinauto / Playwright ({mode})",
            dependencies=plan_result.get("dependencies", {})
        )

        # Emit Plan Created Event
        event_bus.publish(
            request_id=f"req_{tid}",
            execution_id=tid,
            conversation_id=conversation_id,
            node_id="automation_planner",
            component_name="Automation Planner",
            component_type="reasoning_agent",
            event_type="AUTOMATION_PLAN_CREATED",
            execution_status=initial_status,
            safe_task_summary=f"Formulated {len(steps)}-step execution plan ({mode} Mode)",
            automation_mode=mode,
            steps_count=len(steps),
            requires_approval=True,
            current_stage="Awaiting user approval",
            timestamp=time.time()
        )

        # Create PendingApproval record with complete Section 4 metadata
        appr_id = f"appr_{int(time.time())}_{uuid.uuid4().hex[:6]}"
        conv = Conversation.objects.filter(conversation_id=conversation_id).first()
        appr_record = PendingApproval.objects.create(
            approval_id=appr_id,
            conversation=conv,
            target_conversation_id=conversation_id,
            execution_id=tid,
            action_type=f"AUTOMATION_{mode.upper()}",
            status="PENDING",
            description=hitl_details["action_summary"],
            metadata={
                "task_id": tid,
                "query": user_request,
                "user_query": user_request,
                "mode": mode,
                **hitl_details
            }
        )

        event_bus.publish(
            request_id=f"req_{appr_id}",
            execution_id=tid,
            conversation_id=conversation_id,
            node_id="hitl_approval_gate",
            component_name="Safety & HITL Policy Gate",
            component_type="approval_controller",
            event_type="APPROVAL_REQUIRED",
            execution_status="WAITING_FOR_APPROVAL",
            safe_task_summary=f"Human authorization required: {hitl_details['action_summary']}",
            approval_id=appr_id,
            approval_reason=hitl_details["action_summary"],
            target=hitl_details["target"],
            execution_plan=hitl_details["execution_plan"],
            input_content=hitl_details["input_content"],
            expected_result=hitl_details["expected_result"],
            is_destructive=hitl_details["is_destructive"],
            risk_level=hitl_details["risk_level"],
            status="WAITING_FOR_APPROVAL",
            timestamp=time.time()
        )

        return {
            "status": "WAITING_FOR_APPROVAL",
            "task_id": tid,
            "automation_mode": mode,
            "mode_reason": mode_reason,
            "steps": steps,
            "requires_approval": True,
            "approval_id": appr_record.approval_id,
            "approval_reason": approval_reason,
            "target": hitl_details["target"],
            "execution_plan": hitl_details["execution_plan"],
            "input_content": hitl_details["input_content"],
            "expected_result": hitl_details["expected_result"],
            "task": task.to_dict()
        }

    @classmethod
    def execute_task(cls, task_id: str) -> Dict[str, Any]:
        """
        Executes a planned AutomationTask step-by-step with real-time verification and EventBus streaming.
        """
        task = AutomationTask.objects.filter(task_id=task_id).first()
        if not task:
            return {"success": False, "error": f"AutomationTask {task_id} not found"}

        if task.approval_status == AutomationTask.APPROVAL_PENDING:
            return {
                "success": False,
                "status": "WAITING_FOR_APPROVAL",
                "error": "Task cannot execute while Human-in-the-Loop approval is pending."
            }

        task.execution_status = AutomationTask.STATUS_EXECUTING
        task.save()

        mode = task.automation_mode
        steps = task.execution_plan
        conversation_id = task.conversation_id
        hybrid_exec = HybridExecutor()

        # Emit Execution Started Event
        event_type = "DESKTOP_EXECUTION_STARTED" if mode == MODE_DESKTOP else ("BROWSER_EXECUTION_STARTED" if mode == MODE_BROWSER else "HYBRID_EXECUTION_STARTED")
        active_executor_name = "Pywinauto" if mode == MODE_DESKTOP else ("Playwright" if mode == MODE_BROWSER else "Pywinauto + Playwright")

        event_bus.publish(
            request_id=f"req_{task_id}",
            execution_id=task_id,
            conversation_id=conversation_id,
            node_id="automation_executor",
            component_name=f"{active_executor_name} Executor",
            component_type="execution_worker",
            event_type=event_type,
            execution_status="EXECUTING",
            safe_task_summary=f"Initiating {mode} automation via {active_executor_name}",
            automation_mode=mode,
            active_executor=active_executor_name,
            current_stage=f"Running step 1 of {len(steps)}",
            timestamp=time.time()
        )

        step_results = []
        overall_success = True
        failed_step = None
        error_msg = ""

        try:
            for idx, step in enumerate(steps, start=1):
                # Check for cancellation before each step
                if event_bus.is_cancelled(conversation_id) or task.execution_status == AutomationTask.STATUS_CANCELLED:
                    task.execution_status = AutomationTask.STATUS_CANCELLED
                    task.save()
                    event_bus.publish(
                        request_id=f"req_{task_id}",
                        execution_id=task_id,
                        conversation_id=conversation_id,
                        node_id="automation_executor",
                        component_name="Automation Engine",
                        component_type="execution_worker",
                        event_type="EXECUTION_CANCELLED",
                        execution_status="CANCELLED",
                        safe_task_summary=f"Task cancelled by user before step #{idx}",
                        timestamp=time.time()
                    )
                    return {"success": False, "status": "CANCELLED", "message": "Task was cancelled by user."}

                step["status"] = "RUNNING"
                task.current_step = idx
                task.save()

                step_title = step.get("title", f"Step {idx}")
                step_action = step.get("action", "")
                step_executor = step.get("executor", "desktop")

                event_bus.publish(
                    request_id=f"req_{task_id}",
                    execution_id=task_id,
                    conversation_id=conversation_id,
                    node_id="automation_executor",
                    component_name=f"{step_executor.capitalize()} Worker",
                    component_type="execution_worker",
                    event_type="EXECUTION_STEP_STARTED",
                    execution_status="RUNNING",
                    safe_task_summary=f"Step {idx}/{len(steps)}: {step_title}",
                    step_id=idx,
                    step_action=step_action,
                    executor=step_executor,
                    current_stage=f"Step {idx}/{len(steps)}: {step_title}",
                    timestamp=time.time()
                )

                # Execute step through HybridExecutor
                step_out = hybrid_exec.execute_step(step)

                # Post-step verification
                event_bus.publish(
                    request_id=f"req_{task_id}",
                    execution_id=task_id,
                    conversation_id=conversation_id,
                    node_id="automation_verifier",
                    component_name="Automation Verifier",
                    component_type="execution_worker",
                    event_type="VERIFICATION_STARTED",
                    execution_status="RUNNING",
                    safe_task_summary=f"Verifying step {idx}: {step_action}...",
                    step_id=idx,
                    timestamp=time.time()
                )

                verif_out = step_out.get("verification", {})
                is_verified = step_out.get("success", False)

                if is_verified:
                    step["status"] = "COMPLETED"
                    event_bus.publish(
                        request_id=f"req_{task_id}",
                        execution_id=task_id,
                        conversation_id=conversation_id,
                        node_id="automation_verifier",
                        component_name="Automation Verifier",
                        component_type="execution_worker",
                        event_type="VERIFICATION_PASSED",
                        execution_status="RUNNING",
                        safe_task_summary=f"Verification passed for step #{idx}: {step_title}",
                        step_id=idx,
                        verification=verif_out,
                        timestamp=time.time()
                    )

                    event_bus.publish(
                        request_id=f"req_{task_id}",
                        execution_id=task_id,
                        conversation_id=conversation_id,
                        node_id="automation_executor",
                        component_name="Automation Engine",
                        component_type="execution_worker",
                        event_type="EXECUTION_STEP_COMPLETED",
                        execution_status="RUNNING",
                        safe_task_summary=f"Completed step {idx}/{len(steps)}: {step_title}",
                        step_id=idx,
                        step_output=step_out,
                        timestamp=time.time()
                    )
                else:
                    step["status"] = "FAILED"
                    overall_success = False
                    failed_step = idx
                    error_msg = step_out.get("error", "Verification check failed.")

                    event_bus.publish(
                        request_id=f"req_{task_id}",
                        execution_id=task_id,
                        conversation_id=conversation_id,
                        node_id="automation_verifier",
                        component_name="Automation Verifier",
                        component_type="execution_worker",
                        event_type="VERIFICATION_FAILED",
                        execution_status="FAILED",
                        safe_task_summary=f"Verification failed on step #{idx}: {error_msg}",
                        step_id=idx,
                        error=error_msg,
                        timestamp=time.time()
                    )
                    break

                step_results.append(step_out)

        finally:
            hybrid_exec.close()

        # Update Final Task State
        final_status = AutomationTask.STATUS_COMPLETED if overall_success else AutomationTask.STATUS_FAILED
        task.execution_status = final_status
        task.tool_output = {"steps": step_results}
        task.error_details = error_msg if not overall_success else ""
        task.save()

        # Generate JARVIS formatted summary of execution
        summary_text = cls._generate_completion_summary(task, steps, overall_success, error_msg)

        event_bus.publish(
            request_id=f"req_{task_id}",
            execution_id=task_id,
            conversation_id=conversation_id,
            node_id="automation_engine",
            component_name="Automation Engine",
            component_type="execution_worker",
            event_type="EXECUTION_COMPLETED" if overall_success else "EXECUTION_FAILED",
            execution_status=final_status,
            safe_task_summary=f"Automation task {final_status.lower()}: {len(step_results)}/{len(steps)} steps executed",
            final_answer=summary_text,
            content=summary_text,
            automation_mode=mode,
            current_stage="Task completed" if overall_success else "Task halted on error",
            timestamp=time.time()
        )

        return {
            "success": overall_success,
            "status": final_status,
            "task_id": task_id,
            "automation_mode": mode,
            "completed_steps": len(step_results),
            "total_steps": len(steps),
            "step_results": step_results,
            "final_answer": summary_text,
            "error": error_msg if not overall_success else None,
            "task": task.to_dict()
        }

    @classmethod
    def resume_after_approval(cls, approval_id: str, approved: bool = True) -> Dict[str, Any]:
        """
        Resumes task execution following human authorization or marks task rejected.
        """
        appr = PendingApproval.objects.filter(approval_id=approval_id).first()
        if not appr:
            return {"success": False, "error": f"Approval {approval_id} not found"}

        task_id = appr.execution_id or appr.metadata.get("task_id")
        task = AutomationTask.objects.filter(task_id=task_id).first()

        if not approved:
            appr.status = "REJECTED"
            appr.resolved_at = timezone.now()
            appr.save()

            if task:
                task.approval_status = AutomationTask.APPROVAL_REJECTED
                task.execution_status = AutomationTask.STATUS_CANCELLED
                task.error_details = "Operation rejected by user during Human-in-the-Loop review."
                task.save()

            cancel_msg = "O.P.S. execution cancelled. No automation actions were performed."
            event_bus.publish(
                request_id=f"req_{approval_id}",
                execution_id=task_id or f"exec_{approval_id}",
                conversation_id=appr.target_conversation_id,
                node_id="hitl_approval_gate",
                component_name="Safety & HITL Policy Gate",
                component_type="approval_controller",
                event_type="APPROVAL_REJECTED",
                execution_status="CANCELLED",
                safe_task_summary="Human-in-the-Loop approval rejected. Operation halted safely.",
                final_answer=cancel_msg,
                content=cancel_msg,
                timestamp=time.time()
            )
            return {"success": True, "status": "DENIED", "message": cancel_msg, "final_answer": cancel_msg}

        # User Approved
        appr.status = "APPROVED"
        appr.resolved_at = timezone.now()
        appr.save()

        if task:
            task.approval_status = AutomationTask.APPROVAL_APPROVED
            task.execution_status = AutomationTask.STATUS_READY
            task.save()

        event_bus.publish(
            request_id=f"req_{approval_id}",
            execution_id=task_id or f"exec_{approval_id}",
            conversation_id=appr.target_conversation_id,
            node_id="hitl_approval_gate",
            component_name="Safety & HITL Policy Gate",
            component_type="approval_controller",
            event_type="APPROVAL_GRANTED",
            execution_status="READY",
            safe_task_summary="Human authorization confirmed. Resuming automation execution.",
            timestamp=time.time()
        )

        # Resume execution
        if task:
            return cls.execute_task(task.task_id)

        return {"success": True, "status": "APPROVED", "message": "Approval confirmed."}

    @classmethod
    def cancel_task(cls, task_id: str) -> Dict[str, Any]:
        """
        Gracefully aborts a running automation task.
        """
        task = AutomationTask.objects.filter(task_id=task_id).first()
        if not task:
            return {"success": False, "error": f"Task {task_id} not found"}

        task.execution_status = AutomationTask.STATUS_CANCELLED
        task.save()

        event_bus.cancel_conversation(task.conversation_id)
        event_bus.publish(
            request_id=f"req_{task_id}",
            execution_id=task_id,
            conversation_id=task.conversation_id,
            node_id="automation_engine",
            component_name="Automation Engine",
            component_type="execution_worker",
            event_type="EXECUTION_CANCELLED",
            execution_status="CANCELLED",
            safe_task_summary=f"Automation task {task_id} cancelled by user.",
            timestamp=time.time()
        )
        return {"success": True, "status": "CANCELLED", "task_id": task_id}

    @classmethod
    def _generate_completion_summary(cls, task: AutomationTask, steps: List[Dict[str, Any]], success: bool, error: str) -> str:
        """
        Generates clean JARVIS Markdown formatted response summarizing the automation execution.
        """
        status_icon = "✅" if success else "⚠️"
        mode_title = f"{task.automation_mode} AUTOMATION"
        
        lines = [
            f"## {status_icon} {mode_title} EXECUTION {'COMPLETED' if success else 'HALTED'}\n",
            f"**Directive**: `{task.user_request}`\n",
            "### 🛠️ Execution Pipeline Steps\n"
        ]

        for s in steps:
            s_icon = "✅" if s.get("status") == "COMPLETED" else ("❌" if s.get("status") == "FAILED" else "⏳")
            lines.append(f"- {s_icon} **Step {s.get('step_id')}**: {s.get('title')} `[{s.get('executor').upper()}]`")

        if success:
            lines.append(f"\nAll operations and empirical state verifications succeeded.")
        else:
            lines.append(f"\n❌ **Failure Diagnostic**: {error}")

        lines.append(f"\n## 📌 Discussion So Far\n")
        lines.append(f"- Executed {task.automation_mode} automation directive: '{task.user_request[:50]}'")
        lines.append(f"- Status: `{task.execution_status}` across {len(steps)} planned step(s)")
        lines.append(f"- Task Identifier: `{task.task_id[:16]}`")

        return "\n".join(lines)
