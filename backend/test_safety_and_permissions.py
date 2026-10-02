"""
Test Suite for O.P.S. Iteration 2: Safety & Permission Audit Subsystem
Tests:
1. Critical Destructive Command Hard-Blocking & Audit Logging.
2. Low-Risk Safe Operation Auto-Approval.
3. Interactive Async Human-in-the-Loop Authorization with DB persistence (ALLOW_ONCE & DENY).
4. REST Endpoints for Audit Logs, Permission History, and Safety Rules.
"""

import os
import sys
import json
import uuid
import asyncio
import unittest

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ops_backend.settings")
import django
django.setup()

from rest_framework.test import APIClient
from channels.testing import WebsocketCommunicator
from channels.db import database_sync_to_async
from ops_backend.asgi import application
from ops_core.safety import OPSSafetyGatekeeper
from ops_core.models import PermissionRequest, ExecutionAuditLog, SafetyPolicyRule, PermissionStatus, PermissionDecision


class TestIteration2SafetyAudit(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.client = APIClient()

    async def test_01_critical_command_hard_block(self):
        """Test that destructive commands are immediately blocked and recorded in DB audit."""
        destructive_cmd = "rm -rf /var/data"
        result = await OPSSafetyGatekeeper.validate_and_authorize_async(
            agent_name="TestTerminalAgent",
            action="run_terminal_cmd",
            params={"command": destructive_cmd},
            task_id="task-destruct-1"
        )

        self.assertFalse(result.get("approved"))
        self.assertEqual(result.get("risk_level"), "CRITICAL")
        self.assertEqual(result.get("decision"), "AUTO_BLOCKED")

        # Verify audit record in DB
        audit = await database_sync_to_async(
            lambda: ExecutionAuditLog.objects.filter(task_id="task-destruct-1").first()
        )()

        self.assertIsNotNone(audit)
        self.assertEqual(audit.status, "BLOCKED")
        self.assertEqual(audit.agent_name, "TestTerminalAgent")

    async def test_02_low_risk_auto_approved(self):
        """Test that safe read-only operations are auto-approved."""
        result = await OPSSafetyGatekeeper.validate_and_authorize_async(
            agent_name="ScraperAgent",
            action="web_scrape",
            params={"url": "https://example.com/docs"},
            task_id="task-scrape-1"
        )
        self.assertTrue(result.get("approved"))
        self.assertEqual(result.get("risk_level"), "LOW")
        self.assertEqual(result.get("decision"), "AUTO_APPROVED")

    async def test_03_async_permission_approval_flow(self):
        """Test interactive authorization modal flow with DB status updates."""
        communicator = WebsocketCommunicator(application, "/ws/permissions/")
        connected, _ = await communicator.connect()
        self.assertTrue(connected)
        await communicator.receive_json_from()  # consume 'connected'

        # Agent initiates sensitive action
        agent_task = asyncio.create_task(
            OPSSafetyGatekeeper.validate_and_authorize_async(
                agent_name="DevAgent",
                action="run_terminal_cmd",
                params={"command": "git push origin main"},
                reason_explanation="Push new features",
                task_id="task-perm-approve",
                timeout_seconds=5
            )
        )

        # Receive WebSocket permission prompt
        req_pkt = await communicator.receive_json_from(timeout=5)
        self.assertEqual(req_pkt.get("event"), "permission_request")
        self.assertEqual(req_pkt.get("command"), "git push origin main")
        request_id = req_pkt.get("request_id")

        # User clicks [ ALLOW_ONCE ]
        await communicator.send_json_to({
            "action": "permission_response",
            "request_id": request_id,
            "decision": "ALLOW_ONCE"
        })

        # Consumer ack
        ack = await communicator.receive_json_from(timeout=5)
        self.assertTrue(ack.get("success"))

        # Agent unblocks
        result = await agent_task
        self.assertTrue(result.get("approved"))
        self.assertEqual(result.get("decision"), "ALLOW_ONCE")

        # Verify DB record updated
        perm_record = await database_sync_to_async(
            lambda: PermissionRequest.objects.get(request_id=request_id)
        )()
        self.assertEqual(perm_record.status, PermissionStatus.APPROVED)
        self.assertEqual(perm_record.decision, PermissionDecision.ALLOW_ONCE)
        self.assertIsNotNone(perm_record.resolved_at)

        await communicator.disconnect()

    async def test_04_async_permission_denial_flow(self):
        """Test interactive authorization modal denial with DB status updates."""
        communicator = WebsocketCommunicator(application, "/ws/permissions/")
        connected, _ = await communicator.connect()
        self.assertTrue(connected)
        await communicator.receive_json_from()

        agent_task = asyncio.create_task(
            OPSSafetyGatekeeper.validate_and_authorize_async(
                agent_name="DevAgent",
                action="delete_file",
                params={"file_path": "backend/legacy.py"},
                reason_explanation="Remove legacy module",
                task_id="task-perm-deny",
                timeout_seconds=5
            )
        )

        req_pkt = await communicator.receive_json_from(timeout=5)
        request_id = req_pkt.get("request_id")

        # User clicks [ DENY ]
        await communicator.send_json_to({
            "action": "permission_response",
            "request_id": request_id,
            "decision": "DENY"
        })

        await communicator.receive_json_from(timeout=5)
        result = await agent_task
        self.assertFalse(result.get("approved"))
        self.assertEqual(result.get("decision"), "DENY")

        perm_record = await database_sync_to_async(
            lambda: PermissionRequest.objects.get(request_id=request_id)
        )()
        self.assertEqual(perm_record.status, PermissionStatus.DENIED)
        self.assertEqual(perm_record.decision, PermissionDecision.DENY)

        await communicator.disconnect()

    def test_05_rest_api_audit_and_rules(self):
        """Test REST API endpoints for logs, permissions, and safety rules."""
        # 1. Audit Logs API
        res1 = self.client.get('/api/audit/logs/')
        self.assertEqual(res1.status_code, 200)
        self.assertIn("logs", res1.json())

        # 2. Permission History API
        res2 = self.client.get('/api/permissions/history/')
        self.assertEqual(res2.status_code, 200)
        self.assertIn("requests", res2.json())

        # 3. Safety Rules API
        res3 = self.client.get('/api/safety/rules/')
        self.assertEqual(res3.status_code, 200)
        self.assertIn("rules", res3.json())

        # Create new rule
        unique_name = f"Block dangerous drop command {uuid.uuid4().hex[:6]}"
        post_rule = self.client.post('/api/safety/rules/', {
            "name": unique_name,
            "rule_type": "REGEX_BLOCK",
            "pattern": r"drop\s+table",
            "risk_level": "CRITICAL",
            "is_active": True,
            "description": "Prevent table dropping"
        }, format='json')
        self.assertEqual(post_rule.status_code, 201)


if __name__ == "__main__":
    unittest.main()
