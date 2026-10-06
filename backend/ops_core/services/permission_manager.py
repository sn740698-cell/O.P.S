"""
O.P.S. In-Memory Permission Request Manager
Coordinates async pausing of agent actions awaiting human-in-the-loop decisions via WebSockets.
"""

import asyncio
import uuid
import logging
from typing import Dict, Any, Optional
from ops_core.services.event_bus import OPSEventBus

logger = logging.getLogger("ops.permission_manager")


class OPSPermissionManager:
    _instance = None
    _pending_requests: Dict[str, asyncio.Future] = {}
    _pending_metadata: Dict[str, Dict[str, Any]] = {}
    _task_whitelists: Dict[str, set] = {}  # task_id -> set of allowed actions/commands
    _approved_actions: set = set()
    _approved_targets: set = set()

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(OPSPermissionManager, cls).__new__(cls)
            cls._pending_requests = {}
            cls._pending_metadata = {}
            cls._task_whitelists = {}
            cls._approved_actions = set()
            cls._approved_targets = set()
        return cls._instance

    @classmethod
    def is_action_pre_approved(cls, action: str, command: str = "", task_id: Optional[str] = None) -> bool:
        """
        Checks if Human-in-the-Loop permission was already granted for this specific task or persistent action.
        """
        # 1. Specific persistent whitelist
        if action in cls._approved_actions:
            return True
        if command and command in cls._approved_targets:
            return True

        # 2. Task-specific whitelist (e.g. from prior ALLOW_TASK)
        if task_id and task_id in cls._task_whitelists:
            whitelist = cls._task_whitelists[task_id]
            if "*" in whitelist or action in whitelist or (command and command in whitelist):
                return True

        return False

    @classmethod
    async def request_permission(
        cls,
        agent: str,
        action: str,
        command: str,
        reason: str,
        risk_level: str = "MEDIUM",
        task_id: Optional[str] = None,
        timeout_seconds: int = 60,
        request_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Pauses the caller until the user responds via the permission WebSocket or REST endpoint, or until timeout.
        Decisions: 'ALLOW_ONCE', 'ALLOW_TASK', 'DENY', 'TIMEOUT'
        """
        # Fast-path: Check if already authorized
        if cls.is_action_pre_approved(action, command, task_id):
            logger.info(f"Action '{action}' / command '{command}' pre-approved for task {task_id}")
            return {
                "decision": "ALLOW_TASK",
                "approved": True,
                "reason": "Pre-authorized by user policy"
            }

        req_id = request_id or str(uuid.uuid4())
        loop = asyncio.get_running_loop()
        future = loop.create_future()
        cls._pending_requests[req_id] = (future, loop)
        cls._pending_metadata[req_id] = {
            "agent": agent,
            "action": action,
            "command": command,
            "task_id": task_id
        }

        # Emit over WebSockets to React UI & Desktop Overlay
        await OPSEventBus.emit_permission_request_async(
            request_id=req_id,
            agent=agent,
            action=action,
            command=command,
            reason=reason,
            risk_level=risk_level,
            timeout_seconds=timeout_seconds
        )

        try:
            decision_data = await asyncio.wait_for(future, timeout=timeout_seconds)
            decision = decision_data.get("decision", "DENY")
            approved = bool(decision_data.get("approved", "ALLOW" in decision.upper()))

            if approved:
                if decision == "ALLOW_TASK" and task_id:
                    if task_id not in cls._task_whitelists:
                        cls._task_whitelists[task_id] = set()
                    cls._task_whitelists[task_id].add(action)
                    if command:
                        cls._task_whitelists[task_id].add(command)
                elif decision == "ALLOW_ALWAYS":
                    cls._approved_actions.add(action)
                    if command:
                        cls._approved_targets.add(command)

            return {
                "decision": decision,
                "approved": approved,
                "request_id": req_id,
                "reason": f"User decision: {decision}"
            }
        except asyncio.TimeoutError:
            logger.warning(f"Permission request {req_id} timed out after {timeout_seconds}s")
            OPSEventBus.emit_permission_resolved(req_id, "TIMEOUT")
            return {
                "decision": "TIMEOUT",
                "approved": False,
                "request_id": req_id,
                "reason": "User did not respond within timeout period."
            }
        finally:
            cls._pending_requests.pop(req_id, None)
            cls._pending_metadata.pop(req_id, None)

    @classmethod
    def resolve_permission(cls, request_id: str, decision: str) -> bool:
        """
        Called when user clicks [ ALLOW_ONCE ], [ ALLOW_TASK ], or [ DENY ].
        Handles thread-safe future resolution whether invoked from async WebSocket or sync REST thread.
        """
        meta = cls._pending_metadata.get(request_id, {})
        action = meta.get("action", "")
        command = meta.get("command", "")
        task_id = meta.get("task_id")

        approved = "ALLOW" in decision.upper()

        if approved:
            if decision == "ALLOW_TASK" and task_id:
                if task_id not in cls._task_whitelists:
                    cls._task_whitelists[task_id] = set()
                if action:
                    cls._task_whitelists[task_id].add(action)
                if command:
                    cls._task_whitelists[task_id].add(command)
            elif decision == "ALLOW_ALWAYS":
                if action:
                    cls._approved_actions.add(action)
                if command:
                    cls._approved_targets.add(command)

        entry = cls._pending_requests.get(request_id)
        if entry:
            if isinstance(entry, tuple):
                future, loop = entry
            else:
                future, loop = entry, None

            res_payload = {"decision": decision, "approved": approved}
            if not future.done():
                if loop and loop.is_running():
                    try:
                        loop.call_soon_threadsafe(
                            lambda: not future.done() and future.set_result(res_payload)
                        )
                    except Exception as loop_err:
                        logger.error(f"Error resolving future threadsafe: {loop_err}")
                        if not future.done():
                            future.set_result(res_payload)
                else:
                    future.set_result(res_payload)

                OPSEventBus.emit_permission_resolved(request_id, decision)
                logger.info(f"Resolved permission request {request_id} -> {decision} (approved={approved})")
                return True

        logger.info(f"Permission request {request_id} resolved (cache/db only) -> {decision}")
        return True
