"""
O.P.S. Safety, Permissions, and Audit Database Models
Provides persistent storage for safety rules, human-in-the-loop permission requests,
and immutable execution audit logs.
"""

import uuid
from django.db import models
from django.utils import timezone


class RiskLevel(models.TextChoices):
    LOW = "LOW", "Low (Read-Only / Safe)"
    MEDIUM = "MEDIUM", "Medium (Local Modification)"
    HIGH = "HIGH", "High (Terminal / System Execution)"
    CRITICAL = "CRITICAL", "Critical (High-Impact / Destructive)"


class PermissionStatus(models.TextChoices):
    PENDING = "PENDING", "Pending User Action"
    APPROVED = "APPROVED", "Approved by User"
    DENIED = "DENIED", "Denied by User"
    TIMEOUT = "TIMEOUT", "Timed Out"
    BLOCKED_POLICY = "BLOCKED_POLICY", "Blocked by Safety Policy"


class PermissionDecision(models.TextChoices):
    ALLOW_ONCE = "ALLOW_ONCE", "Allow Once"
    ALLOW_TASK = "ALLOW_TASK", "Allow for Entire Task"
    DENY = "DENY", "Deny"
    AUTO_BLOCKED = "AUTO_BLOCKED", "Automatically Blocked"


class PermissionRequest(models.Model):
    """
    Records every interactive authorization prompt sent to the user.
    """
    request_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    task_id = models.CharField(max_length=128, blank=True, null=True, db_index=True)
    agent_name = models.CharField(max_length=64, default="Agent")
    action_type = models.CharField(max_length=64)  # e.g., 'run_terminal_cmd', 'dom_click', 'file_write'
    command_text = models.TextField()
    reason = models.TextField(blank=True, default="")
    risk_level = models.CharField(
        max_length=16,
        choices=RiskLevel.choices,
        default=RiskLevel.MEDIUM
    )
    status = models.CharField(
        max_length=24,
        choices=PermissionStatus.choices,
        default=PermissionStatus.PENDING,
        db_index=True
    )
    decision = models.CharField(
        max_length=24,
        choices=PermissionDecision.choices,
        blank=True,
        null=True
    )
    timeout_seconds = models.IntegerField(default=60)
    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    resolved_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Permission Request"
        verbose_name_plural = "Permission Requests"

    def __str__(self):
        return f"[{self.status}] {self.agent_name} - {self.action_type} ({self.risk_level})"


class ExecutionAuditLog(models.Model):
    """
    Immutable audit trail recording every tool execution and system command.
    """
    log_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    task_id = models.CharField(max_length=128, blank=True, null=True, db_index=True)
    agent_name = models.CharField(max_length=64, default="Agent")
    action_type = models.CharField(max_length=64, db_index=True)
    target = models.TextField(blank=True, default="")  # Command, URL, or File path
    parameters = models.JSONField(default=dict, blank=True)
    status = models.CharField(max_length=24, default="SUCCESS")  # SUCCESS, FAILED, BLOCKED, DENIED
    stdout = models.TextField(blank=True, default="")
    stderr = models.TextField(blank=True, default="")
    duration_ms = models.IntegerField(default=0)
    executed_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        ordering = ['-executed_at']
        verbose_name = "Execution Audit Log"
        verbose_name_plural = "Execution Audit Logs"

    def __str__(self):
        return f"[{self.status}] {self.agent_name} - {self.action_type} @ {self.executed_at.strftime('%H:%M:%S')}"


class SafetyPolicyRule(models.Model):
    """
    Configurable security filter rule (regex blacklist, allowed domain, or command pattern).
    """
    RULE_TYPE_CHOICES = [
        ("REGEX_BLOCK", "Regex Block Pattern"),
        ("DOMAIN_WHITELIST", "Allowed Domain Whitelist"),
        ("PATH_RESTRICTION", "Restricted File Path"),
        ("COMMAND_WHITELIST", "Pre-Approved Command"),
    ]

    name = models.CharField(max_length=128, unique=True)
    rule_type = models.CharField(max_length=32, choices=RULE_TYPE_CHOICES, default="REGEX_BLOCK")
    pattern = models.CharField(max_length=512)
    risk_level = models.CharField(
        max_length=16,
        choices=RiskLevel.choices,
        default=RiskLevel.CRITICAL
    )
    is_active = models.BooleanField(default=True, db_index=True)
    description = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['name']
        verbose_name = "Safety Policy Rule"
        verbose_name_plural = "Safety Policy Rules"

    def __str__(self):
        status_str = "ACTIVE" if self.is_active else "DISABLED"
        return f"[{status_str}] {self.name} ({self.rule_type}): {self.pattern}"


class MobileCompanionDevice(models.Model):
    """
    Registered mobile companion device (iOS / Android / Flutter).
    Connects over local / static network to provide companion controls.
    """
    device_id = models.CharField(max_length=128, primary_key=True)
    device_name = models.CharField(max_length=128, default="Mobile Companion")
    device_type = models.CharField(max_length=32, default="android")  # android, ios, tablet
    auth_token = models.CharField(max_length=256, unique=True, db_index=True)
    ip_address = models.CharField(max_length=64, blank=True, default="")
    is_paired = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True, db_index=True)
    permissions_allowed = models.JSONField(default=list, blank=True)
    last_heartbeat = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Mobile Companion Device"
        verbose_name_plural = "Mobile Companion Devices"

    def __str__(self):
        return f"{self.device_name} ({self.device_id}) - {'Active' if self.is_active else 'Inactive'}"


class MobilePairingSession(models.Model):
    """
    Temporary PIN session for pairing new mobile clients securely.
    """
    pin_code = models.CharField(max_length=12, unique=True, db_index=True)
    pairing_secret = models.CharField(max_length=128)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)

    def is_valid(self):
        return not self.is_used and timezone.now() < self.expires_at

    def __str__(self):
        status = "USED" if self.is_used else ("VALID" if self.is_valid() else "EXPIRED")
        return f"PIN {self.pin_code} [{status}]"


class UserWorkstationMemory(models.Model):
    """
    Section in PostgreSQL for user personal memories:
    Captures active window context (YouTube songs, Instagram reels, Google searches, apps),
    stores user labels ("my favorite song", "AI research video"), and executes automatic
    window navigation and playback on command.
    """
    memory_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    label = models.CharField(max_length=255, db_index=True)  # e.g., "my favorite song", "workout playlist", "cooking reel"
    category = models.CharField(max_length=64, default="media", db_index=True) # media, social, search, app, doc, general
    window_title = models.CharField(max_length=512, blank=True, default="")
    target_url = models.TextField(blank=True, default="")
    app_name = models.CharField(max_length=128, blank=True, default="")
    action_type = models.CharField(max_length=64, default="play_media") # play_media, open_url, launch_app, custom
    content_snippet = models.TextField(blank=True, default="")
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "User Workstation Memory"
        verbose_name_plural = "User Workstation Memories"

    def __str__(self):
        return f"[{self.category.upper()}] {self.label} -> {self.window_title or self.target_url}"

