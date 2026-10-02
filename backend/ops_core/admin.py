from django.contrib import admin
from ops_core.models import PermissionRequest, ExecutionAuditLog, SafetyPolicyRule


@admin.register(PermissionRequest)
class PermissionRequestAdmin(admin.ModelAdmin):
    list_display = ('request_id', 'agent_name', 'action_type', 'risk_level', 'status', 'decision', 'created_at')
    list_filter = ('status', 'risk_level', 'decision', 'created_at')
    search_fields = ('agent_name', 'action_type', 'command_text', 'reason')
    readonly_fields = ('request_id', 'created_at')


@admin.register(ExecutionAuditLog)
class ExecutionAuditLogAdmin(admin.ModelAdmin):
    list_display = ('log_id', 'agent_name', 'action_type', 'status', 'duration_ms', 'executed_at')
    list_filter = ('status', 'action_type', 'executed_at')
    search_fields = ('agent_name', 'action_type', 'target', 'stdout', 'stderr')
    readonly_fields = ('log_id', 'executed_at')


@admin.register(SafetyPolicyRule)
class SafetyPolicyRuleAdmin(admin.ModelAdmin):
    list_display = ('name', 'rule_type', 'risk_level', 'is_active', 'created_at')
    list_filter = ('rule_type', 'risk_level', 'is_active')
    search_fields = ('name', 'pattern', 'description')
