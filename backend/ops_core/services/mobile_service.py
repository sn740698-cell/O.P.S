"""
O.P.S. Mobile Companion Synchronization & Remote Control Service
Provides secure device pairing, token authentication, remote permission resolution,
emergency system halt triggers, and mobile camera stream processing.
"""

import logging
import secrets
import random
import time
from datetime import timedelta
from typing import Dict, Any, Optional, List
from django.utils import timezone
from channels.db import database_sync_to_async

from ops_core.models import (
    MobileCompanionDevice,
    MobilePairingSession,
    PermissionRequest,
    PermissionStatus,
    PermissionDecision,
    ExecutionAuditLog,
    RiskLevel
)

from ops_core.services.event_bus import OPSEventBus
from ops_core.services.permission_manager import OPSPermissionManager
from ops_core.services.vision_service import OPSVisionService
from ops_core.services.escalation_engine import OPSEscalationEngine

logger = logging.getLogger("ops.mobile_service")


class OPSMobileService:
    """
    Core orchestrator for mobile companion connectivity and remote system control.
    """

    DEFAULT_PERMISSIONS = [
        "approve_permissions",
        "stream_camera",
        "remote_prompt",
        "system_halt"
    ]

    # ==================== Pairing & Authentication ====================

    @classmethod
    def generate_pairing_session(
        cls,
        expires_in_minutes: int = 10,
        host: str = "127.0.0.1",
        port: int = 8000
    ) -> Dict[str, Any]:
        """
        Generates a 6-digit numeric PIN code and pairing secret with expiration time.
        """
        pin_code = f"{random.randint(100000, 999999)}"
        # Guarantee PIN uniqueness among active sessions
        while MobilePairingSession.objects.filter(pin_code=pin_code, is_used=False, expires_at__gt=timezone.now()).exists():
            pin_code = f"{random.randint(100000, 999999)}"

        pairing_secret = secrets.token_hex(16)
        expires_at = timezone.now() + timedelta(minutes=expires_in_minutes)

        session = MobilePairingSession.objects.create(
            pin_code=pin_code,
            pairing_secret=pairing_secret,
            expires_at=expires_at,
            is_used=False
        )

        qr_payload = {
            "pin": pin_code,
            "secret": pairing_secret,
            "http_endpoint": f"http://{host}:{port}/api/v1/mobile/pairing/verify/",
            "ws_endpoint": f"ws://{host}:{port}/ws/mobile/",
            "expires_at": expires_at.isoformat()
        }

        return {
            "pin_code": pin_code,
            "pairing_secret": pairing_secret,
            "expires_at": expires_at.isoformat(),
            "expires_in_seconds": expires_in_minutes * 60,
            "qr_payload": qr_payload
        }

    @classmethod
    def verify_and_pair_device(
        cls,
        pin_code: str,
        device_id: str,
        device_name: str = "Mobile Companion",
        device_type: str = "android",
        ip_address: str = ""
    ) -> Dict[str, Any]:
        """
        Validates the PIN code and registers or updates the companion device.
        """
        now = timezone.now()
        session = MobilePairingSession.objects.filter(
            pin_code=pin_code.strip(),
            is_used=False,
            expires_at__gt=now
        ).first()

        if not session:
            return {
                "success": False,
                "error": "Invalid or expired pairing PIN code."
            }

        # Mark session as used
        session.is_used = True
        session.save()

        # Generate persistent token for the device
        auth_token = f"ops_mob_{secrets.token_hex(24)}"

        device, _ = MobileCompanionDevice.objects.update_or_create(
            device_id=device_id.strip(),
            defaults={
                "device_name": device_name.strip(),
                "device_type": device_type.lower().strip(),
                "auth_token": auth_token,
                "ip_address": ip_address,
                "is_paired": True,
                "is_active": True,
                "permissions_allowed": cls.DEFAULT_PERMISSIONS,
                "last_heartbeat": now
            }
        )

        # Broadcast pairing event
        OPSEventBus.emit_mobile_event("device_paired", {
            "device_id": device.device_id,
            "device_name": device.device_name,
            "device_type": device.device_type,
            "ip_address": device.ip_address,
            "timestamp": time.time()
        })

        return {
            "success": True,
            "device_id": device.device_id,
            "device_name": device.device_name,
            "auth_token": auth_token,
            "permissions_allowed": device.permissions_allowed,
            "message": "Device successfully paired with O.P.S."
        }

    @classmethod
    def authenticate_token(cls, auth_token: str) -> Optional[MobileCompanionDevice]:
        """
        Validates the mobile auth token and updates device heartbeat.
        """
        if not auth_token:
            return None
        clean_token = auth_token.replace("Bearer ", "").strip()
        device = MobileCompanionDevice.objects.filter(
            auth_token=clean_token,
            is_active=True,
            is_paired=True
        ).first()

        if device:
            device.last_heartbeat = timezone.now()
            device.save(update_fields=["last_heartbeat"])
        return device

    # ==================== Remote Permission & Control ====================

    @classmethod
    def resolve_remote_permission(
        cls,
        auth_token: str,
        request_id: str,
        decision: str
    ) -> Dict[str, Any]:
        """
        Allows mobile companion to approve or deny human-in-the-loop security requests.
        """
        device = cls.authenticate_token(auth_token)
        if not device:
            return {"success": False, "error": "Unauthorized mobile device."}

        if "approve_permissions" not in device.permissions_allowed:
            return {"success": False, "error": "Device not authorized to resolve permissions."}

        # Resolve through standard in-memory permission manager if waiting
        in_memory_resolved = OPSPermissionManager.resolve_permission(request_id, decision)

        # Update persistent database model
        db_resolved = False
        try:
            req = PermissionRequest.objects.filter(request_id=request_id).first()
            if req:
                req.status = PermissionStatus.APPROVED if decision in [
                    PermissionDecision.ALLOW_ONCE,
                    PermissionDecision.ALLOW_TASK
                ] else PermissionStatus.DENIED
                req.decision = decision
                req.resolved_at = timezone.now()
                req.save()
                db_resolved = True
        except Exception as e:
            logger.error(f"Error persisting permission resolution to DB: {e}")

        resolved = in_memory_resolved or db_resolved

        # Record audit log
        ExecutionAuditLog.objects.create(
            agent_name=f"MobileApp:{device.device_name}",
            action_type="remote_permission_resolved",
            target=f"request_id:{request_id}",
            parameters={"decision": decision, "device_id": device.device_id},
            status="SUCCESS" if resolved else "FAILED",
            executed_at=timezone.now()
        )

        OPSEventBus.emit_mobile_event("remote_permission_handled", {
            "request_id": request_id,
            "decision": decision,
            "device_id": device.device_id
        })

        return {
            "success": resolved,
            "request_id": request_id,
            "decision": decision,
            "resolved_by": device.device_name
        }


    @classmethod
    def trigger_emergency_halt(cls, auth_token: str, reason: str = "Triggered from Mobile Companion") -> Dict[str, Any]:
        """
        Immediately emits an emergency halt event across all O.P.S. subsystems.
        """
        device = cls.authenticate_token(auth_token)
        if not device:
            return {"success": False, "error": "Unauthorized mobile device."}

        if "system_halt" not in device.permissions_allowed:
            return {"success": False, "error": "Device not authorized for emergency halt."}

        # Emit emergency halt to all channel layers
        OPSEventBus.emit_emergency_halt(
            source=f"Mobile:{device.device_name}",
            reason=reason
        )

        # Audit log critical security action
        ExecutionAuditLog.objects.create(
            agent_name=f"MobileApp:{device.device_name}",
            action_type="EMERGENCY_HALT",
            target="SYSTEM_CORE",
            parameters={"reason": reason, "device_id": device.device_id},
            status="TRIGGERED",
            executed_at=timezone.now()
        )

        return {
            "success": True,
            "halt_triggered": True,
            "source": device.device_name,
            "reason": reason,
            "timestamp": time.time()
        }

    # ==================== Remote Dispatch & Camera Stream ====================

    @classmethod
    async def dispatch_remote_task_async(
        cls,
        auth_token: str,
        prompt: str,
        task_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Dispatches an autonomous task from the mobile companion to the escalation engine.
        """
        device = await database_sync_to_async(cls.authenticate_token)(auth_token)
        if not device:
            return {"success": False, "error": "Unauthorized mobile device."}

        if "remote_prompt" not in device.permissions_allowed:
            return {"success": False, "error": "Device not authorized for remote dispatch."}

        engine = OPSEscalationEngine()
        result = await engine.resolve_query(prompt, task_id=task_id)

        return {
            "success": True,
            "task_id": result.get("task_id"),
            "tier_used": result.get("tier_used"),
            "tier_name": result.get("tier_name"),
            "resolved": result.get("resolved"),
            "response": result.get("response")
        }

    @classmethod
    def process_camera_frame(
        cls,
        auth_token: str,
        image_base64: str,
        prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Feeds mobile camera frames to the vision reasoning pipeline.
        """
        device = cls.authenticate_token(auth_token)
        if not device:
            return {"success": False, "error": "Unauthorized mobile device."}

        if "stream_camera" not in device.permissions_allowed:
            return {"success": False, "error": "Device not authorized for camera streaming."}

        vision_prompt = prompt or "Analyze this mobile camera snapshot and describe any visible code, screen, or objects."
        analysis_result = OPSVisionService.analyze_image(image_base64, prompt=vision_prompt)

        return {
            "success": True,
            "device_id": device.device_id,
            "prompt": vision_prompt,
            "analysis": analysis_result.get("analysis"),
            "source": analysis_result.get("source")
        }

    # ==================== Device Management ====================

    @classmethod
    def list_devices(cls) -> List[Dict[str, Any]]:
        """Lists all registered companion devices."""
        devices = MobileCompanionDevice.objects.all()
        return [
            {
                "device_id": d.device_id,
                "device_name": d.device_name,
                "device_type": d.device_type,
                "ip_address": d.ip_address,
                "is_paired": d.is_paired,
                "is_active": d.is_active,
                "permissions_allowed": d.permissions_allowed,
                "last_heartbeat": d.last_heartbeat.isoformat() if d.last_heartbeat else None,
                "created_at": d.created_at.isoformat()
            }
            for d in devices
        ]

    @classmethod
    def revoke_device(cls, device_id: str) -> bool:
        """Revokes access for a companion device."""
        updated = MobileCompanionDevice.objects.filter(device_id=device_id).update(
            is_active=False,
            is_paired=False
        )
        return updated > 0
