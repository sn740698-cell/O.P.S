"""
O.P.S. Real-Time WebSocket Consumers (Django Channels)
Handles streaming agent thoughts, interactive permission prompts, terminal logs, and voice events.
"""

import json
import logging
import uuid
import time
from channels.generic.websocket import AsyncWebsocketConsumer
from ops_core.services.event_bus import OPSEventBus
from ops_core.services.permission_manager import OPSPermissionManager
from ops_core.services.ollama_service import OPSOllamaService
from asgiref.sync import sync_to_async

logger = logging.getLogger("ops.consumers")


class BaseOPSConsumer(AsyncWebsocketConsumer):
    """Base consumer with group subscription and generic broadcast forwarding."""
    group_name: str = ""

    async def connect(self):
        if self.group_name:
            await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        await self.send(text_data=json.dumps({
            "event": "connected",
            "channel": self.group_name,
            "timestamp": time.time()
        }))

    async def disconnect(self, close_code):
        if self.group_name:
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def broadcast_event(self, event):
        """Handler for group messages sent via OPSEventBus."""
        payload = event.get("payload", {})
        await self.send(text_data=json.dumps(payload))


class AgentOrchestrationConsumer(BaseOPSConsumer):
    """
    WebSocket endpoint: /ws/agent/
    Streams live LLM token generation, multi-step agent plans, and thoughts.
    """
    group_name = OPSEventBus.GROUP_AGENT

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ollama_service = OPSOllamaService()

    async def receive(self, text_data=None, bytes_data=None):
        if not text_data:
            return

        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({"event": "error", "message": "Invalid JSON format."}))
            return

        action = data.get("action") or data.get("type", "user_message")

        if action == "ping":
            await self.send(text_data=json.dumps({"event": "pong", "timestamp": time.time()}))
            return

        if action in ["user_message", "prompt"]:
            prompt = data.get("prompt") or data.get("message", "")
            task_id = data.get("task_id") or str(uuid.uuid4())

            if not prompt:
                await self.send(text_data=json.dumps({"event": "error", "message": "Prompt is required."}))
                return

            # Acknowledge receipt
            await self.send(text_data=json.dumps({
                "event": "task_started",
                "task_id": task_id,
                "prompt": prompt
            }))

            # Async execution of tri-model pipeline
            await self._run_agent_pipeline(task_id, prompt)

    async def _run_agent_pipeline(self, task_id: str, prompt: str, session_id: str = "default"):
        try:
            from ops_core.orchestration.supervisor import Supervisor
            from ops_core.session.session_manager import SessionManager
            
            session_mgr = SessionManager()
            session = session_mgr.get_or_create_session(session_id)
            session_mgr.add_message(session.session_id, "user", prompt)

            supervisor = Supervisor()
            response = await supervisor.handle_request(
                user_input=prompt,
                session_id=session.session_id,
                context={"task_id": task_id}
            )

            session_mgr.add_message(
                session.session_id,
                "assistant",
                response.content,
                metadata={"status": response.status, "mode": response.mode.value}
            )

            await self.send(text_data=json.dumps({
                "event": "task_completed",
                "task_id": task_id,
                "status": response.status,
                "mode": response.mode.value,
                "agent": response.agent,
                "tool": response.tool,
                "response": response.content,
                "evidence": response.evidence,
                "error": response.error
            }))
        except Exception as e:
            logger.error(f"Error executing canonical supervisor pipeline: {e}", exc_info=True)
            await self.send(text_data=json.dumps({
                "event": "task_failed",
                "task_id": task_id,
                "error": str(e)
            }))

    async def emit_thought(self, thought: str, agent: str, step: int, task_id: str):
        await self.send(text_data=json.dumps({
            "event": "agent_thought",
            "task_id": task_id,
            "agent": agent,
            "thought": thought,
            "step": step,
            "timestamp": time.time()
        }))


class PermissionConsumer(BaseOPSConsumer):
    """
    WebSocket endpoint: /ws/permissions/
    Streams high-priority security approval modals and receives user responses (ALLOW_ONCE, ALLOW_TASK, DENY).
    """
    group_name = OPSEventBus.GROUP_PERMISSIONS

    async def receive(self, text_data=None, bytes_data=None):
        if not text_data:
            return

        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({"event": "error", "message": "Invalid JSON format."}))
            return

        action = data.get("action") or data.get("type")

        if action == "permission_response":
            request_id = data.get("request_id")
            decision = data.get("decision", "DENY")  # ALLOW_ONCE, ALLOW_TASK, DENY

            if not request_id:
                await self.send(text_data=json.dumps({"event": "error", "message": "request_id required."}))
                return

            resolved = OPSPermissionManager.resolve_permission(request_id, decision)
            await self.send(text_data=json.dumps({
                "event": "permission_acknowledged",
                "request_id": request_id,
                "decision": decision,
                "success": resolved
            }))
        elif action == "ping":
            await self.send(text_data=json.dumps({"event": "pong", "timestamp": time.time()}))


class TerminalOutputConsumer(BaseOPSConsumer):
    """
    WebSocket endpoint: /ws/terminal/
    Streams real-time terminal stdout/stderr lines and logs.
    """
    group_name = OPSEventBus.GROUP_TERMINAL

    async def receive(self, text_data=None, bytes_data=None):
        if not text_data:
            return
        try:
            data = json.loads(text_data)
            if data.get("action") == "ping":
                await self.send(text_data=json.dumps({"event": "pong", "timestamp": time.time()}))
        except Exception:
            pass


class VoiceStreamConsumer(BaseOPSConsumer):
    """
    WebSocket endpoint: /ws/voice/
    Streams real-time audio transcriptions and voice activity events.
    """
    group_name = OPSEventBus.GROUP_VOICE

    async def receive(self, text_data=None, bytes_data=None):
        if not text_data:
            return
        try:
            data = json.loads(text_data)
            if data.get("action") == "ping":
                await self.send(text_data=json.dumps({"event": "pong", "timestamp": time.time()}))
        except Exception:
            pass


class MobileSyncConsumer(BaseOPSConsumer):
    """
    WebSocket endpoint: /ws/mobile/
    Real-time bidirectional synchronization for mobile companion devices.
    Streams permission alerts, system state telemetry, and accepts remote control commands.
    """
    group_name = OPSEventBus.GROUP_MOBILE

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.device = None

    async def receive(self, text_data=None, bytes_data=None):
        if not text_data:
            return

        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({"event": "error", "message": "Invalid JSON format."}))
            return

        action = data.get("action") or data.get("type", "ping")
        token = data.get("auth_token", "")

        if action == "ping":
            await self.send(text_data=json.dumps({"event": "pong", "timestamp": time.time()}))
            return

        from ops_core.services.mobile_service import OPSMobileService
        from channels.db import database_sync_to_async

        if action == "authenticate":
            device = await database_sync_to_async(OPSMobileService.authenticate_token)(token)
            if device:
                self.device = device
                await self.send(text_data=json.dumps({
                    "event": "authenticated",
                    "device_id": device.device_id,
                    "device_name": device.device_name,
                    "permissions": device.permissions_allowed
                }))
            else:
                await self.send(text_data=json.dumps({
                    "event": "auth_failed",
                    "error": "Invalid or expired mobile auth token."
                }))
            return

        if action == "permission_response":
            request_id = data.get("request_id")
            decision = data.get("decision", "DENY")
            res = await database_sync_to_async(OPSMobileService.resolve_remote_permission)(
                auth_token=token,
                request_id=request_id,
                decision=decision
            )
            await self.send(text_data=json.dumps({
                "event": "remote_permission_result",
                **res
            }))
            return

        if action == "emergency_halt":
            reason = data.get("reason", "Halt triggered from mobile WebSocket")
            res = await database_sync_to_async(OPSMobileService.trigger_emergency_halt)(
                auth_token=token,
                reason=reason
            )
            await self.send(text_data=json.dumps({
                "event": "emergency_halt_result",
                **res
            }))
            return

        if action == "camera_frame":
            image_base64 = data.get("image_base64", "")
            prompt = data.get("prompt")
            res = await database_sync_to_async(OPSMobileService.process_camera_frame)(
                auth_token=token,
                image_base64=image_base64,
                prompt=prompt
            )
            await self.send(text_data=json.dumps({
                "event": "camera_frame_result",
                **res
            }))
            return

