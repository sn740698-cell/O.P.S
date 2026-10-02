"""
O.P.S. Django REST Framework Serializers
"""

from rest_framework import serializers
from ops_core.models import PermissionRequest, ExecutionAuditLog, SafetyPolicyRule, UserWorkstationMemory


class PermissionRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = PermissionRequest
        fields = '__all__'


class ExecutionAuditLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExecutionAuditLog
        fields = '__all__'


class SafetyPolicyRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = SafetyPolicyRule
        fields = '__all__'


class UserWorkstationMemorySerializer(serializers.ModelSerializer):
    class Meta:
        model = UserWorkstationMemory
        fields = '__all__'
