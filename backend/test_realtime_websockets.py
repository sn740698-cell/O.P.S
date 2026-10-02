"""
Test Suite for O.P.S. Iteration 1: Django Channels & WebSocket Event Core
Tests:
1. AgentOrchestrationConsumer: /ws/agent/ connection, ping/pong, and event streaming.
2. PermissionConsumer & PermissionManager: /ws/permissions/ interactive authorization flow.
3. TerminalOutputConsumer: /ws/terminal/ log broadcasting.
4. VoiceStreamConsumer: /ws/voice/ voice events broadcasting.
5. OPSEventBus: Event emitter across sync/async contexts.
"""

import os
import sys
import json
import asyncio
import unittest

# Configure Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ops_backend.settings")
import django
django.setup()

from channels.testing import WebsocketCommunicator
from ops_backend.asgi import application
from ops_core.services.event_bus import OPSEventBus
from ops_core.services.permission_manager import OPSPermissionManager


class TestIteration1WebSockets(unittest.IsolatedAsyncioTestCase):

    async def test_01_agent_consumer_ping(self):
        """Test connecting to /ws/agent/ and sending ping."""
        communicator = WebsocketCommunicator(application, "/ws/agent/")
        connected, subprotocol = await communicator.connect()
        self.assertTrue(connected, "Failed to connect to /ws/agent/")

        # Receive welcome connection payload
        response = await communicator.receive_json_from(timeout=5)
        self.assertEqual(response.get("event"), "connected")

        # Send ping
        await communicator.send_json_to({"action": "ping"})
        response = await communicator.receive_json_from(timeout=5)
        self.assertEqual(response.get("event"), "pong")

        await communicator.disconnect()

    async def test_02_event_bus_agent_thought_broadcast(self):
        """Test OPSEventBus broadcasting agent thoughts to connected /ws/agent/ clients."""
        communicator = WebsocketCommunicator(application, "/ws/agent/")
        connected, _ = await communicator.connect()
        self.assertTrue(connected)
        await communicator.receive_json_from()  # consume 'connected'

        # Emit thought via OPSEventBus
        await OPSEventBus.emit_agent_thought_async(
            thought="Analyzing query intent...",
            agent="Router (Qwen 0.5B)",
            step=1,
            task_id="test-task-123"
        )

        response = await communicator.receive_json_from(timeout=5)
        self.assertEqual(response.get("event"), "agent_thought")
        self.assertEqual(response.get("task_id"), "test-task-123")
        self.assertEqual(response.get("agent"), "Router (Qwen 0.5B)")
        self.assertIn("Analyzing query intent", response.get("thought", ""))

        await communicator.disconnect()

    async def test_03_permission_consumer_flow(self):
        """Test permission request broadcasting and user decision resolution."""
        communicator = WebsocketCommunicator(application, "/ws/permissions/")
        connected, _ = await communicator.connect()
        self.assertTrue(connected)
        await communicator.receive_json_from()  # consume 'connected'

        # Start an async permission request task
        async def mock_agent_action():
            return await OPSPermissionManager.request_permission(
                agent="TerminalAgent",
                action="run_terminal_cmd",
                command="git push origin main",
                reason="Deploy completed code",
                risk_level="HIGH",
                timeout_seconds=5
            )

        agent_task = asyncio.create_task(mock_agent_action())

        # Client receives permission_request packet
        req_packet = await communicator.receive_json_from(timeout=5)
        self.assertEqual(req_packet.get("event"), "permission_request")
        self.assertEqual(req_packet.get("command"), "git push origin main")
        self.assertEqual(req_packet.get("risk_level"), "HIGH")
        request_id = req_packet.get("request_id")

        # Client responds with ALLOW_ONCE
        await communicator.send_json_to({
            "action": "permission_response",
            "request_id": request_id,
            "decision": "ALLOW_ONCE"
        })

        # Consumer acknowledges
        ack = await communicator.receive_json_from(timeout=5)
        self.assertEqual(ack.get("event"), "permission_acknowledged")
        self.assertTrue(ack.get("success"))

        # Agent task unblocks and receives approval
        agent_result = await agent_task
        self.assertTrue(agent_result.get("approved"))
        self.assertEqual(agent_result.get("decision"), "ALLOW_ONCE")

        await communicator.disconnect()

    async def test_04_terminal_output_broadcast(self):
        """Test broadcasting terminal stdout/stderr logs over /ws/terminal/."""
        communicator = WebsocketCommunicator(application, "/ws/terminal/")
        connected, _ = await communicator.connect()
        self.assertTrue(connected)
        await communicator.receive_json_from()

        # Emit log
        await OPSEventBus.emit_terminal_log_async(
            data="[OPS] Starting local build...",
            stream="stdout"
        )

        response = await communicator.receive_json_from(timeout=5)
        self.assertEqual(response.get("event"), "terminal_log")
        self.assertEqual(response.get("stream"), "stdout")
        self.assertEqual(response.get("data"), "[OPS] Starting local build...")

        await communicator.disconnect()

    async def test_05_voice_stream_broadcast(self):
        """Test broadcasting voice transcription events over /ws/voice/."""
        communicator = WebsocketCommunicator(application, "/ws/voice/")
        connected, _ = await communicator.connect()
        self.assertTrue(connected)
        await communicator.receive_json_from()

        # Emit voice event
        OPSEventBus.emit_voice_event("transcript", {"text": "Hey O.P.S, build backend", "confidence": 0.98})

        response = await communicator.receive_json_from(timeout=5)
        self.assertEqual(response.get("event"), "voice_event")
        self.assertEqual(response.get("voice_type"), "transcript")
        self.assertEqual(response.get("data", {}).get("text"), "Hey O.P.S, build backend")

        await communicator.disconnect()

    async def test_06_agent_orchestration_stream(self):
        """Test sending a prompt to /ws/agent/ and receiving streamed events."""
        communicator = WebsocketCommunicator(application, "/ws/agent/")
        connected, _ = await communicator.connect()
        self.assertTrue(connected)
        await communicator.receive_json_from()  # consume 'connected'

        # Send a prompt to agent
        await communicator.send_json_to({
            "action": "user_message",
            "prompt": "Explain what O.P.S. is",
            "task_id": "task-stream-456"
        })

        # Expect task_started
        evt1 = await communicator.receive_json_from(timeout=5)
        self.assertEqual(evt1.get("event"), "task_started")
        self.assertEqual(evt1.get("task_id"), "task-stream-456")

        # Expect thoughts and updates
        received_events = []
        for _ in range(8):
            try:
                evt = await communicator.receive_json_from(timeout=15)
                received_events.append(evt.get("event"))
                if evt.get("event") == "task_completed":
                    break
            except Exception:
                break

        self.assertTrue(len(received_events) > 0)
        await communicator.disconnect()


if __name__ == "__main__":
    unittest.main()
