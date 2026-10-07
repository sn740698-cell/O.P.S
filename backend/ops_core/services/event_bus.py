"""
O.P.S. Real-Time Event Bus Service
Unified interface for broadcasting events, agent thoughts, logs, permission prompts, 
and system states across Django Channels to React UI, Desktop Overlay, and Mobile clients.
"""

import time
import uuid
import logging
import asyncio
from typing import Dict, Any, Optional
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

logger = logging.getLogger("ops.event_bus")


class OPSEventBus:
    """
    Central event broadcaster for O.P.S. ecosystem.
    Works seamlessly in both synchronous and asynchronous execution contexts.
    """

    GROUP_AGENT = "ops_agent_broadcast"
    GROUP_PERMISSIONS = "ops_permission_gate"
    GROUP_TERMINAL = "ops_terminal_stream"
    GROUP_VOICE = "ops_voice_stream"
    GROUP_MOBILE = "ops_mobile_sync"

    @staticmethod
    def _send_to_group_sync(group_name: str, message: Dict[str, Any]):
        try:
            channel_layer = get_channel_layer()
            if not channel_layer:
                return

            msg_payload = {
                "type": "broadcast_event",
                "payload": message
            }

            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = None

            if loop and loop.is_running():
                # We are in an active async event loop thread
                loop.create_task(channel_layer.group_send(group_name, msg_payload))
            else:
                # We are in a synchronous thread (e.g., standard Django view or background worker)
                async_to_sync(channel_layer.group_send)(group_name, msg_payload)
        except Exception as e:
            logger.error(f"Failed to broadcast sync event to {group_name}: {e}")

    @staticmethod
    async def _send_to_group_async(group_name: str, message: Dict[str, Any]):
        try:
            channel_layer = get_channel_layer()
            if channel_layer:
                await channel_layer.group_send(
                    group_name,
                    {
                        "type": "broadcast_event",
                        "payload": message
                    }
                )
        except Exception as e:
            logger.error(f"Failed to broadcast async event to {group_name}: {e}")

    # ==================== Agent Broadcasts ====================

    @classmethod
    def emit_agent_thought(cls, thought: str, agent: str = "Router", step: int = 1, task_id: Optional[str] = None):
        """Broadcasts intermediate model thinking and reasoning steps."""
        payload = {
            "event": "agent_thought",
            "task_id": task_id or str(uuid.uuid4()),
            "agent": agent,
            "thought": thought,
            "step": step,
            "timestamp": time.time()
        }
        cls._send_to_group_sync(cls.GROUP_AGENT, payload)

    @classmethod
    async def emit_agent_thought_async(cls, thought: str, agent: str = "Router", step: int = 1, task_id: Optional[str] = None):
        payload = {
            "event": "agent_thought",
            "task_id": task_id or str(uuid.uuid4()),
            "agent": agent,
            "thought": thought,
            "step": step,
            "timestamp": time.time()
        }
        await cls._send_to_group_async(cls.GROUP_AGENT, payload)

    @classmethod
    async def emit_thought_async(cls, thought: str, agent: str = "Router", step: int = 1, task_id: Optional[str] = None):
        await cls.emit_agent_thought_async(thought=thought, agent=agent, step=step, task_id=task_id)

    @classmethod
    def emit_thought(cls, thought: str, agent: str = "Router", step: int = 1, task_id: Optional[str] = None):
        cls.emit_agent_thought(thought=thought, agent=agent, step=step, task_id=task_id)

    @classmethod
    async def emit_ops_event_async(cls, event_data: Dict[str, Any]):
        """Broadcasts a canonical structured O.P.S. event to the agent group."""
        payload = {
            "type": "broadcast_event",
            "payload": event_data
        }
        await cls._send_to_group_async(cls.GROUP_AGENT, event_data)

    @classmethod
    def emit_ops_event(cls, event_data: Dict[str, Any]):
        """Broadcasts a canonical structured O.P.S. event synchronously."""
        cls._send_to_group_sync(cls.GROUP_AGENT, event_data)

    @classmethod
    def emit_agent_status(cls, status: str, details: Optional[Dict[str, Any]] = None):
        """Broadcasts agent operational state: IDLE, THINKING, EXECUTING, WAITING_PERMISSION, ERROR."""
        payload = {
            "event": "agent_status",
            "status": status,
            "details": details or {},
            "timestamp": time.time()
        }
        cls._send_to_group_sync(cls.GROUP_AGENT, payload)

    @classmethod
    def emit_agent_plan(cls, plan_steps: list, model: str = "llama3.2:1b", safety_level: str = "SAFE"):
        """Broadcasts formulated execution plan."""
        payload = {
            "event": "agent_plan",
            "plan_steps": plan_steps,
            "model": model,
            "safety_level": safety_level,
            "timestamp": time.time()
        }
        cls._send_to_group_sync(cls.GROUP_AGENT, payload)

    @classmethod
    def emit_memory_added(cls, memory_data: Dict[str, Any]):
        """Broadcasts memory committed event to trigger retro audio chime in all listening clients."""
        payload = {
            "event": "memory_added",
            "memory": memory_data,
            "timestamp": time.time()
        }
        cls._send_to_group_sync(cls.GROUP_AGENT, payload)

    @classmethod
    def emit_agent_response(cls, text_chunk: str, is_final: bool = False, task_id: Optional[str] = None):
        """Streams agent responses chunk by chunk to UI."""
        payload = {
            "event": "agent_response",
            "task_id": task_id,
            "chunk": text_chunk,
            "is_final": is_final,
            "timestamp": time.time()
        }
        cls._send_to_group_sync(cls.GROUP_AGENT, payload)

    @classmethod
    def emit_task_started(cls, prompt: str, task_id: Optional[str] = None, source: str = "cockpit", agent: str = "Directive & Hotkey Ingestion"):
        """Broadcasts task execution start across Django Channels to Web HUD and overlays."""
        payload = {
            "event": "task_started",
            "task_id": task_id or str(uuid.uuid4()),
            "prompt": prompt,
            "source": source,
            "agent": agent,
            "thought": f"Directive received: \"{prompt}\". Initializing multi-agent sensory routing...",
            "status": "EXECUTING",
            "timestamp": time.time()
        }
        cls._send_to_group_sync(cls.GROUP_AGENT, payload)

    @classmethod
    async def emit_task_started_async(cls, prompt: str, task_id: Optional[str] = None, source: str = "cockpit", agent: str = "Directive & Hotkey Ingestion"):
        """Async broadcast of task start to all connected WebSocket clients."""
        payload = {
            "event": "task_started",
            "task_id": task_id or str(uuid.uuid4()),
            "prompt": prompt,
            "source": source,
            "agent": agent,
            "thought": f"Directive received: \"{prompt}\". Initializing multi-agent sensory routing...",
            "status": "EXECUTING",
            "timestamp": time.time()
        }
        await cls._send_to_group_async(cls.GROUP_AGENT, payload)

    @classmethod
    def emit_task_completed(cls, task_id: str, final_answer: str, category: str = "EXECUTED", plan: list = None, details: dict = None):
        """Broadcasts task completion across all listening clients."""
        payload = {
            "event": "task_completed",
            "task_id": task_id,
            "category": category,
            "final_answer": final_answer,
            "plan": plan or [],
            "details": details or {},
            "status": "COMPLETED",
            "timestamp": time.time()
        }
        cls._send_to_group_sync(cls.GROUP_AGENT, payload)

    @classmethod
    async def emit_task_completed_async(cls, task_id: str, final_answer: str, category: str = "EXECUTED", plan: list = None, details: dict = None):
        """Async broadcast of task completion across all listening clients."""
        payload = {
            "event": "task_completed",
            "task_id": task_id,
            "category": category,
            "final_answer": final_answer,
            "plan": plan or [],
            "details": details or {},
            "status": "COMPLETED",
            "timestamp": time.time()
        }
        await cls._send_to_group_async(cls.GROUP_AGENT, payload)

    @classmethod
    def emit_task_failed(cls, task_id: str, error: str):
        """Broadcasts task failure across all listening clients."""
        payload = {
            "event": "task_failed",
            "task_id": task_id,
            "error": error,
            "status": "FAILED",
            "timestamp": time.time()
        }
        cls._send_to_group_sync(cls.GROUP_AGENT, payload)

    @classmethod
    async def emit_task_failed_async(cls, task_id: str, error: str):
        """Async broadcast of task failure across all listening clients."""
        payload = {
            "event": "task_failed",
            "task_id": task_id,
            "error": error,
            "status": "FAILED",
            "timestamp": time.time()
        }
        await cls._send_to_group_async(cls.GROUP_AGENT, payload)

    # ==================== Permission Gate Broadcasts ====================

    @classmethod
    def emit_permission_request(
        cls, 
        request_id: str, 
        agent: str, 
        action: str, 
        command: str, 
        reason: str, 
        risk_level: str = "MEDIUM",
        timeout_seconds: int = 60
    ):
        """Broadcasts an interactive permission request modal to UI & Desktop overlay."""
        payload = {
            "event": "permission_request",
            "request_id": request_id,
            "agent": agent,
            "action": action,
            "command": command,
            "reason": reason,
            "risk_level": risk_level,
            "timeout_seconds": timeout_seconds,
            "timestamp": time.time()
        }
        cls._send_to_group_sync(cls.GROUP_PERMISSIONS, payload)

    @classmethod
    async def emit_permission_request_async(
        cls, 
        request_id: str, 
        agent: str, 
        action: str, 
        command: str, 
        reason: str, 
        risk_level: str = "MEDIUM",
        timeout_seconds: int = 60
    ):
        payload = {
            "event": "permission_request",
            "request_id": request_id,
            "agent": agent,
            "action": action,
            "command": command,
            "reason": reason,
            "risk_level": risk_level,
            "timeout_seconds": timeout_seconds,
            "timestamp": time.time()
        }
        await cls._send_to_group_async(cls.GROUP_PERMISSIONS, payload)

    @classmethod
    def emit_permission_resolved(cls, request_id: str, decision: str):
        payload = {
            "event": "permission_resolved",
            "request_id": request_id,
            "decision": decision,
            "timestamp": time.time()
        }
        cls._send_to_group_sync(cls.GROUP_PERMISSIONS, payload)

    # ==================== Terminal Stream Broadcasts ====================

    @classmethod
    def emit_terminal_log(cls, data: str, stream: str = "stdout"):
        """Streams terminal output lines, build outputs, or web scraping logs."""
        payload = {
            "event": "terminal_log",
            "stream": stream,
            "data": data,
            "timestamp": time.time()
        }
        cls._send_to_group_sync(cls.GROUP_TERMINAL, payload)

    @classmethod
    async def emit_terminal_log_async(cls, data: str, stream: str = "stdout"):
        payload = {
            "event": "terminal_log",
            "stream": stream,
            "data": data,
            "timestamp": time.time()
        }
        await cls._send_to_group_async(cls.GROUP_TERMINAL, payload)

    # ==================== Voice Stream Broadcasts ====================

    @classmethod
    def emit_voice_event(cls, event_type: str, data: Any):
        """Broadcasts voice transcription, listening state, or TTS playback markers."""
        payload = {
            "event": "voice_event",
            "voice_type": event_type,
            "data": data,
            "timestamp": time.time()
        }
        cls._send_to_group_sync(cls.GROUP_VOICE, payload)

    # ==================== Mobile Companion Sync & Control Broadcasts ====================

    @classmethod
    def emit_mobile_event(cls, event_name: str, data: Any):
        """Broadcasts state synchronization, mobile alerts, or sensor streams."""
        payload = {
            "event": event_name,
            "data": data,
            "timestamp": time.time()
        }
        cls._send_to_group_sync(cls.GROUP_MOBILE, payload)

    @classmethod
    async def emit_mobile_event_async(cls, event_name: str, data: Any):
        payload = {
            "event": event_name,
            "data": data,
            "timestamp": time.time()
        }
        await cls._send_to_group_async(cls.GROUP_MOBILE, payload)

    @classmethod
    def emit_emergency_halt(cls, source: str, reason: str):
        """Broadcasts emergency system stop across all active channel groups."""
        payload = {
            "event": "emergency_halt",
            "source": source,
            "reason": reason,
            "timestamp": time.time()
        }
        cls._send_to_group_sync(cls.GROUP_AGENT, payload)
        cls._send_to_group_sync(cls.GROUP_PERMISSIONS, payload)
        cls._send_to_group_sync(cls.GROUP_TERMINAL, payload)
        cls._send_to_group_sync(cls.GROUP_MOBILE, payload)

