import uuid
import time
from django.db import models

class AutomationTask(models.Model):
    """
    O.P.S. 2.0 Central Automation Task State Representation
    Compatible with LangGraph multi-agent architecture and Human-in-the-Loop workflows.
    Tracks state across Desktop (Pywinauto), Browser (Playwright), and Hybrid execution.
    """
    # Execution State Constants (Section 5)
    STATUS_RECEIVED = "RECEIVED"
    STATUS_UNDERSTANDING = "UNDERSTANDING"
    STATUS_PLANNING = "PLANNING"
    STATUS_WAITING_FOR_APPROVAL = "WAITING_FOR_APPROVAL"
    STATUS_READY = "READY"
    STATUS_EXECUTING = "EXECUTING"
    STATUS_VERIFYING = "VERIFYING"
    STATUS_COMPLETED = "COMPLETED"
    STATUS_FAILED = "FAILED"
    STATUS_CANCELLED = "CANCELLED"

    STATUS_CHOICES = [
        (STATUS_RECEIVED, "Received"),
        (STATUS_UNDERSTANDING, "Understanding"),
        (STATUS_PLANNING, "Planning"),
        (STATUS_WAITING_FOR_APPROVAL, "Waiting for Approval"),
        (STATUS_READY, "Ready"),
        (STATUS_EXECUTING, "Executing"),
        (STATUS_VERIFYING, "Verifying"),
        (STATUS_COMPLETED, "Completed"),
        (STATUS_FAILED, "Failed"),
        (STATUS_CANCELLED, "Cancelled"),
    ]

    # Automation Modes (Section 3)
    MODE_DESKTOP = "DESKTOP"
    MODE_BROWSER = "BROWSER"
    MODE_HYBRID = "HYBRID"

    MODE_CHOICES = [
        (MODE_DESKTOP, "Desktop Automation (Pywinauto)"),
        (MODE_BROWSER, "Browser Automation (Playwright)"),
        (MODE_HYBRID, "Hybrid Automation (Pywinauto + Playwright)"),
    ]

    # Approval Status
    APPROVAL_NOT_REQUIRED = "NOT_REQUIRED"
    APPROVAL_PENDING = "PENDING"
    APPROVAL_APPROVED = "APPROVED"
    APPROVAL_REJECTED = "REJECTED"

    APPROVAL_CHOICES = [
        (APPROVAL_NOT_REQUIRED, "Not Required"),
        (APPROVAL_PENDING, "Pending"),
        (APPROVAL_APPROVED, "Approved"),
        (APPROVAL_REJECTED, "Rejected"),
    ]

    # Model Fields
    task_id = models.CharField(max_length=128, unique=True, db_index=True)
    conversation_id = models.CharField(max_length=128, db_index=True)
    user_request = models.TextField()
    task_type = models.CharField(max_length=32, choices=MODE_CHOICES, default=MODE_DESKTOP)
    automation_mode = models.CharField(max_length=32, choices=MODE_CHOICES, default=MODE_DESKTOP)
    execution_plan = models.JSONField(default=list, blank=True)
    current_step = models.IntegerField(default=0)
    dependencies = models.JSONField(default=dict, blank=True)
    execution_status = models.CharField(max_length=32, choices=STATUS_CHOICES, default=STATUS_RECEIVED)
    approval_status = models.CharField(max_length=32, choices=APPROVAL_CHOICES, default=APPROVAL_NOT_REQUIRED)
    tool_name = models.CharField(max_length=128, blank=True, default="")
    tool_output = models.JSONField(default=dict, blank=True)
    verification_result = models.JSONField(default=dict, blank=True)
    error_details = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Automation Task"
        verbose_name_plural = "Automation Tasks"

    def __str__(self):
        return f"AutomationTask[{self.task_id}] - {self.automation_mode} ({self.execution_status})"

    def to_dict(self):
        """Returns structured dictionary representation for API and EventBus streaming."""
        return {
            "task_id": self.task_id,
            "conversation_id": self.conversation_id,
            "user_request": self.user_request,
            "task_type": self.task_type,
            "automation_mode": self.automation_mode,
            "execution_plan": self.execution_plan,
            "current_step": self.current_step,
            "dependencies": self.dependencies,
            "execution_status": self.execution_status,
            "approval_status": self.approval_status,
            "tool_name": self.tool_name,
            "tool_output": self.tool_output,
            "verification_result": self.verification_result,
            "error_details": self.error_details,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
