"""
Automated Verification Suite for Iteration 7: Mobile Companion Sync & Remote Control API
Tests PIN generation, secure device pairing, mobile token authentication, remote permission
approval, emergency kill switch execution, camera streaming, and REST API endpoints.
"""

import os
import django
import unittest
import base64
from unittest.mock import patch, MagicMock

# Setup Django Environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ops_backend.settings')
django.setup()

from rest_framework.test import APIClient
from ops_core.models import (
    MobileCompanionDevice,
    MobilePairingSession,
    PermissionRequest,
    ExecutionAuditLog,
    RiskLevel,
    PermissionStatus,
    PermissionDecision
)
from ops_core.services.mobile_service import OPSMobileService
from ops_core.services.permission_manager import OPSPermissionManager


class TestMobileCompanionSync(unittest.TestCase):
    """
    Test suite for Mobile Companion device lifecycle, pairing, remote control, and security.
    """

    def setUp(self):
        self.client = APIClient()
        # Clean up database records
        MobileCompanionDevice.objects.all().delete()
        MobilePairingSession.objects.all().delete()
        PermissionRequest.objects.all().delete()
        ExecutionAuditLog.objects.all().delete()

    def test_01_pairing_session_generation(self):
        """Test generating PIN code and QR pairing payload."""
        session_data = OPSMobileService.generate_pairing_session(
            expires_in_minutes=15,
            host="192.168.1.100",
            port=8000
        )
        self.assertIn("pin_code", session_data)
        self.assertEqual(len(session_data["pin_code"]), 6)
        self.assertIn("pairing_secret", session_data)
        self.assertIn("qr_payload", session_data)
        self.assertIn("192.168.1.100", session_data["qr_payload"]["http_endpoint"])

        # Check DB persistence
        session_db = MobilePairingSession.objects.filter(pin_code=session_data["pin_code"]).first()
        self.assertIsNotNone(session_db)
        self.assertTrue(session_db.is_valid())

    def test_02_device_verification_and_auth(self):
        """Test verifying PIN code, issuing token, and authenticating device."""
        session_data = OPSMobileService.generate_pairing_session(expires_in_minutes=5)
        pin_code = session_data["pin_code"]

        # Pair device
        pair_res = OPSMobileService.verify_and_pair_device(
            pin_code=pin_code,
            device_id="iphone-14-pro-01",
            device_name="Dev iPhone",
            device_type="ios",
            ip_address="192.168.1.50"
        )
        self.assertTrue(pair_res["success"])
        self.assertIn("auth_token", pair_res)
        auth_token = pair_res["auth_token"]

        # Session should now be marked as used
        session_db = MobilePairingSession.objects.get(pin_code=pin_code)
        self.assertTrue(session_db.is_used)
        self.assertFalse(session_db.is_valid())

        # Authenticate token
        authenticated_dev = OPSMobileService.authenticate_token(auth_token)
        self.assertIsNotNone(authenticated_dev)
        self.assertEqual(authenticated_dev.device_id, "iphone-14-pro-01")
        self.assertEqual(authenticated_dev.device_name, "Dev iPhone")

        # Invalid token check
        invalid_dev = OPSMobileService.authenticate_token("ops_mob_invalid_fake_token")
        self.assertIsNone(invalid_dev)

    def test_03_remote_permission_resolution(self):
        """Test resolving an interactive desktop permission request remotely from mobile."""
        # 1. Register paired device
        session_data = OPSMobileService.generate_pairing_session()
        pair_res = OPSMobileService.verify_and_pair_device(
            pin_code=session_data["pin_code"],
            device_id="pixel-8-test",
            device_name="Admin Pixel",
            device_type="android"
        )
        token = pair_res["auth_token"]

        # 2. Create pending PermissionRequest
        req = PermissionRequest.objects.create(
            task_id="task-mobile-sync-01",
            agent_name="SystemAutomationAgent",
            action_type="write_system_config",
            command_text="echo 'ops_mode=active' > /etc/ops.conf",
            risk_level=RiskLevel.HIGH,
            status=PermissionStatus.PENDING
        )

        # 3. Resolve via mobile service
        res = OPSMobileService.resolve_remote_permission(
            auth_token=token,
            request_id=str(req.request_id),
            decision=PermissionDecision.ALLOW_ONCE
        )
        self.assertTrue(res["success"])
        self.assertEqual(res["decision"], PermissionDecision.ALLOW_ONCE)

        # 4. Check DB status
        req.refresh_from_db()
        self.assertEqual(req.status, PermissionStatus.APPROVED)
        self.assertEqual(req.decision, PermissionDecision.ALLOW_ONCE)

        # 5. Check Audit Log
        audit = ExecutionAuditLog.objects.filter(action_type="remote_permission_resolved").first()
        self.assertIsNotNone(audit)
        self.assertIn("Admin Pixel", audit.agent_name)

    def test_04_emergency_halt_trigger(self):
        """Test triggering emergency system halt kill switch from mobile app."""
        session_data = OPSMobileService.generate_pairing_session()
        pair_res = OPSMobileService.verify_and_pair_device(
            pin_code=session_data["pin_code"],
            device_id="galaxy-s24-ultra",
            device_name="Control Phone",
            device_type="android"
        )
        token = pair_res["auth_token"]

        # Trigger emergency halt
        halt_res = OPSMobileService.trigger_emergency_halt(
            auth_token=token,
            reason="Unattended runaway loop detected by user"
        )
        self.assertTrue(halt_res["success"])
        self.assertTrue(halt_res["halt_triggered"])

        # Check Audit Log for critical entry
        audit = ExecutionAuditLog.objects.filter(action_type="EMERGENCY_HALT").first()
        self.assertIsNotNone(audit)
        self.assertEqual(audit.target, "SYSTEM_CORE")
        self.assertIn("Control Phone", audit.agent_name)

    def test_05_mobile_camera_and_device_management(self):
        """Test mobile camera frame intake and device listing/revocation."""
        session_data = OPSMobileService.generate_pairing_session()
        pair_res = OPSMobileService.verify_and_pair_device(
            pin_code=session_data["pin_code"],
            device_id="ipad-air-lab",
            device_name="Lab Tablet",
            device_type="tablet"
        )
        token = pair_res["auth_token"]

        # Test camera frame analysis
        sample_img_b64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
        camera_res = OPSMobileService.process_camera_frame(
            auth_token=token,
            image_base64=sample_img_b64,
            prompt="Analyze component"
        )
        self.assertTrue(camera_res["success"])
        self.assertEqual(camera_res["device_id"], "ipad-air-lab")
        self.assertIn("analysis", camera_res)

        # Test device listing
        devices = OPSMobileService.list_devices()
        self.assertGreaterEqual(len(devices), 1)
        self.assertEqual(devices[0]["device_id"], "ipad-air-lab")

        # Test revoking device
        revoked = OPSMobileService.revoke_device("ipad-air-lab")
        self.assertTrue(revoked)
        auth_check = OPSMobileService.authenticate_token(token)
        self.assertIsNone(auth_check)

    def test_06_mobile_rest_api_endpoints(self):
        """Test complete REST API workflow for pairing, device listing, and emergency halt."""
        # 1. Generate PIN
        resp = self.client.post('/api/v1/mobile/pairing/generate/', {"expires_in_minutes": 10}, format='json')
        self.assertEqual(resp.status_code, 200)
        pin_code = resp.json()["pin_code"]

        # 2. Verify PIN & Pair
        pair_payload = {
            "pin_code": pin_code,
            "device_id": "api-test-phone-007",
            "device_name": "API Test Phone",
            "device_type": "android"
        }
        resp = self.client.post('/api/v1/mobile/pairing/verify/', pair_payload, format='json')
        self.assertEqual(resp.status_code, 200)
        auth_token = resp.json()["auth_token"]

        # 3. List devices
        resp = self.client.get('/api/v1/mobile/devices/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["count"], 1)

        # 4. Trigger emergency halt via API with Authorization header
        resp = self.client.post(
            '/api/v1/mobile/emergency-halt/',
            {"reason": "API Emergency Halt Test"},
            HTTP_AUTHORIZATION=f"Bearer {auth_token}",
            format='json'
        )
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.json()["halt_triggered"])


if __name__ == '__main__':
    unittest.main()
