from django.db import models

class Conversation(models.Model):
    """
    Category 1: Active Conversation Context
    Scoped to an individual conversation lifecycle. Deleted on permanent refresh.
    """
    conversation_id = models.CharField(max_length=128, unique=True, db_index=True)
    title = models.CharField(max_length=255, default="New Conversation")
    summary = models.TextField(blank=True, default="")
    status = models.CharField(max_length=32, default="ACTIVE")  # ACTIVE, GENERATING, PENDING_APPROVAL, CANCELLED, DELETED
    active_execution_id = models.CharField(max_length=128, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        return f"Conversation[{self.conversation_id}] - {self.status}"


class ChatMessage(models.Model):
    """
    Category 1: Active Conversation Messages
    Maintains chronological conversation history for an active conversation.
    """
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name="messages"
    )
    message_id = models.CharField(max_length=128, unique=True, db_index=True)
    role = models.CharField(max_length=32)  # 'user', 'assistant', 'system'
    content = models.TextField(blank=True, default="")
    input_type = models.CharField(max_length=32, default="text")  # 'text', 'voice'
    status = models.CharField(max_length=32, default="completed")  # 'pending', 'streaming', 'completed', 'failed', 'cancelled'
    metadata = models.JSONField(default=dict, blank=True)  # citations, plan, research details
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"[{self.role.upper()}] {self.content[:40]}..."


class PendingApproval(models.Model):
    """
    Human-in-the-Loop (HITL) Pending Approval Record.
    Tracks sensitive, destructive, or policy-gated operations requiring explicit human authorization.
    """
    approval_id = models.CharField(max_length=128, unique=True, db_index=True)
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name="pending_approvals",
        null=True,
        blank=True
    )
    target_conversation_id = models.CharField(max_length=128, db_index=True)
    execution_id = models.CharField(max_length=128, blank=True, null=True)
    action_type = models.CharField(max_length=64, default="PERMANENT_CONVERSATION_DELETION")
    status = models.CharField(max_length=32, default="PENDING")  # PENDING, APPROVED, REJECTED, EXECUTED, EXPIRED
    description = models.TextField(blank=True, default="")
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"PendingApproval[{self.approval_id}] - {self.action_type} ({self.status})"


class UserLongTermMemory(models.Model):
    """
    Category 2: O.P.S. Long-Term Memory
    Persistent user-approved preferences, general retained knowledge, personalization.
    PRESERVED across conversation resets and permanent refreshes.
    """
    key = models.CharField(max_length=128, db_index=True)
    content = models.TextField()
    category = models.CharField(max_length=64, default="preference")  # preference, knowledge, personalization
    user_approved = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Memory[{self.key}] - {self.category}"


class ProjectKnowledge(models.Model):
    """
    Category 3: Project Knowledge and RAG
    Project documentation, indexed code, uploaded reference materials.
    PRESERVED across conversation resets and permanent refreshes.
    """
    doc_id = models.CharField(max_length=128, unique=True, db_index=True)
    title = models.CharField(max_length=255)
    content = models.TextField()
    source = models.CharField(max_length=255, default="project_doc")
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"ProjectKnowledge[{self.doc_id}] - {self.title}"


class ResearchSession(models.Model):
    conversation_id = models.CharField(max_length=128, blank=True, null=True, db_index=True)
    session_id = models.CharField(max_length=128, db_index=True)
    request_id = models.CharField(max_length=128, unique=True, db_index=True)
    query = models.TextField()
    status = models.CharField(max_length=32, default="PENDING")
    final_answer = models.TextField(blank=True, default="")
    iterations = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"ResearchSession[{self.request_id}] - {self.status}"


class NodeExecutionEvent(models.Model):
    session = models.ForeignKey(
        ResearchSession,
        on_delete=models.CASCADE,
        related_name="events",
        null=True,
        blank=True
    )
    conversation_id = models.CharField(max_length=128, blank=True, null=True, db_index=True)
    request_id = models.CharField(max_length=128, db_index=True)
    execution_id = models.CharField(max_length=128, db_index=True)
    node_id = models.CharField(max_length=64, db_index=True)
    component_name = models.CharField(max_length=128)
    component_type = models.CharField(max_length=64)  # 'reasoning_agent', 'execution_worker', 'adaptive_controller'
    event_type = models.CharField(max_length=64)  # 'NODE_STARTED', 'NODE_COMPLETED', 'TOOL_INVOKED', etc.
    execution_status = models.CharField(max_length=32)  # 'RUNNING', 'COMPLETED', 'FAILED', 'SKIPPED'
    timestamp = models.FloatField()
    tool_name = models.CharField(max_length=128, blank=True, null=True)
    safe_task_summary = models.TextField()
    safe_output_summary = models.TextField(blank=True, null=True)
    error_details = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["timestamp"]

    def __str__(self):
        return f"[{self.component_name}] {self.event_type} - {self.execution_status}"
