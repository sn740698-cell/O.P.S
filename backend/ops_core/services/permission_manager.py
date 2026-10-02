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
    _task_whitelists: Dict[str, set] = {}  # task_id -> set of allowed actions/commands

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(OPSPermissionManager, cls).__new__(cls)
            cls._pending_requests = {}
            cls._task_whitelists = {}
        return cls._instance

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
        Pauses the caller until the user responds via the permission WebSocket or until timeout.
        Decisions: 'ALLOW_ONCE', 'ALLOW_TASK', 'DENY', 'TIMEOUT'
        """
        # Check if already approved for this task session
        if task_id and task_id in cls._task_whitelists:
            if "*" in cls._task_whitelists[task_id] or action in cls._task_whitelists[task_id] or command in cls._task_whitelists[task_id]:
                logger.info(f"Action '{action}' / command '{command}' pre-approved for task {task_id}")
                return {"decision": "ALLOW_TASK", "approved": True, "reason": "Pre-authorized by task policy"}

        req_id = request_id or str(uuid.uuid4())
        loop = asyncio.get_running_loop()
        future = loop.create_future()
        cls._pending_requests[req_id] = future

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

            if decision == "ALLOW_TASK" and task_id:
                if task_id not in cls._task_whitelists:
                    cls._task_whitelists[task_id] = set()
                cls._task_whitelists[task_id].add(action)
                cls._task_whitelists[task_id].add(command)

            approved = decision in ["ALLOW_ONCE", "ALLOW_TASK"]
            return {
                "decision": decision,
                "approved": approved,
                "request_id": req_id,
                "reason": "User decision: " + decision
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

    @classmethod
    def resolve_permission(cls, request_id: str, decision: str) -> bool:
        """
        Called by PermissionConsumer when user clicks [ DENY ], [ ALLOW ONCE ], or [ ALLOW TASK ].
        """
        future = cls._pending_requests.get(request_id)
        if future and not future.done():
            future.set_result({"decision": decision})
            OPSEventBus.emit_permission_resolved(request_id, decision)
            logger.info(f"Resolved permission request {request_id} -> {decision}")
            return True
        logger.warning(f"Could not resolve permission {request_id}: not found or already completed.")
        return False
