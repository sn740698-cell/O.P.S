"""
O.P.S. Unified Tool Executor
Enforces the mandatory execution path:
Agent -> Capability Registry -> Tool Schema -> Safety Gate -> Executor -> Ground Truth Verifier -> Evidence Result
"""

import time
import uuid
import logging
from typing import Dict, Any, Optional

from ops_core.capabilities.schemas import ToolCallRequest, ToolCallResult, RiskLevel
from ops_core.capabilities.registry import CapabilityRegistry
from ops_core.safety.safety_gate import SafetyGate
from ops_core.verification.verifier import Verifier
from ops_core.core.events import OPSEventType, create_event
from ops_core.services.event_bus import OPSEventBus
from ops_core.core.errors import OPSError, OPSErrorCode

# Import specific tool handlers
from ops_core.tools.filesystem_tools import (
    execute_filesystem_read, execute_filesystem_write, execute_filesystem_create_directory,
    execute_filesystem_delete, execute_filesystem_move, execute_filesystem_list_directory
)
from ops_core.tools.terminal_tools import execute_terminal_command, execute_terminal_run_tests
from ops_core.tools.browser_tools import (
    execute_browser_open, execute_browser_navigate, execute_browser_click,
    execute_browser_type, execute_browser_extract
)
from ops_core.tools.web_tools import (
    execute_web_search, execute_web_crawl, execute_web_extract_structured, execute_web_parse_html
)
from ops_core.tools.desktop_tools import (
    execute_desktop_launch_app, execute_desktop_open_file, execute_desktop_hotkey
)
from ops_core.tools.rag_tools import execute_rag_search, execute_rag_ingest

logger = logging.getLogger("ops.tools.executor")


class ToolExecutor:
    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ToolExecutor, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if getattr(self, "_initialized", False):
            return
        self.registry = CapabilityRegistry()
        self._bind_executors()
        self._initialized = True

    def _bind_executors(self):
        """Binds tool execution functions to their capability names."""
        self.registry.register_executor("filesystem.read", execute_filesystem_read)
        self.registry.register_executor("filesystem.write", execute_filesystem_write)
        self.registry.register_executor("filesystem.create_directory", execute_filesystem_create_directory)
        self.registry.register_executor("filesystem.delete", execute_filesystem_delete)
        self.registry.register_executor("filesystem.move", execute_filesystem_move)
        self.registry.register_executor("filesystem.list_directory", execute_filesystem_list_directory)

        self.registry.register_executor("terminal.execute", execute_terminal_command)
        self.registry.register_executor("terminal.run_tests", execute_terminal_run_tests)

        self.registry.register_executor("browser.open", execute_browser_open)
        self.registry.register_executor("browser.navigate", execute_browser_navigate)
        self.registry.register_executor("browser.click", execute_browser_click)
        self.registry.register_executor("browser.type", execute_browser_type)
        self.registry.register_executor("browser.extract", execute_browser_extract)

        self.registry.register_executor("web.search", execute_web_search)
        self.registry.register_executor("web.crawl", execute_web_crawl)
        self.registry.register_executor("web.extract_structured", execute_web_extract_structured)
        self.registry.register_executor("web.parse_html", execute_web_parse_html)

        self.registry.register_executor("desktop.launch_app", execute_desktop_launch_app)
        self.registry.register_executor("desktop.open_file", execute_desktop_open_file)
        self.registry.register_executor("desktop.hotkey", execute_desktop_hotkey)

        self.registry.register_executor("rag.search", execute_rag_search)
        self.registry.register_executor("rag.ingest", execute_rag_ingest)
        self.registry.register_executor("rag.index", execute_rag_ingest)

    async def execute_capability(
        self,
        capability_name: str,
        arguments: Dict[str, Any],
        requested_by: str,
        task_id: Optional[str] = None,
        mission_id: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> ToolCallResult:
        """
        Executes a registered capability with mandatory Safety Gate authorization and Verifier check.
        """
        cap_def = self.registry.get(capability_name)
        if not cap_def:
            return ToolCallResult(
                tool_call_id=f"call_{uuid.uuid4().hex[:8]}",
                capability=capability_name,
                status="FAILED",
                error=f"Unregistered capability: '{capability_name}'"
            )

        tool_call_id = f"call_{uuid.uuid4().hex[:8]}"
        request = ToolCallRequest(
            tool_call_id=tool_call_id,
            capability=capability_name,
            arguments=arguments,
            risk=cap_def.risk,
            requested_by=requested_by,
            task_id=task_id,
            mission_id=mission_id,
            session_id=session_id,
            verification_method=cap_def.verification_method
        )

        # 0. Emit TOOL_REQUESTED
        await OPSEventBus.emit_ops_event_async(create_event(
            event_type=OPSEventType.TOOL_REQUESTED,
            session_id=session_id or "default",
            task_id=task_id,
            mission_id=mission_id,
            agent_id=requested_by,
            agent_name=requested_by.title(),
            capability=capability_name,
            tool=capability_name,
            status="QUEUED",
            message=f"Tool [{capability_name}] requested by {requested_by.title()}"
        ))

        # 1. Safety Gate Evaluation & Authorization
        try:
            await SafetyGate.authorize_or_prompt(request)
        except OPSError as e:
            logger.warning(f"Tool call {tool_call_id} [{capability_name}] rejected by Safety Gate: {e.message}")
            await OPSEventBus.emit_ops_event_async(create_event(
                event_type=OPSEventType.APPROVAL_DENIED if e.code == OPSErrorCode.PERMISSION_DENIED else OPSEventType.ERROR_OCCURRED,
                session_id=session_id or "default",
                task_id=task_id,
                mission_id=mission_id,
                agent_id=requested_by,
                capability=capability_name,
                tool=capability_name,
                status="BLOCKED" if e.code == OPSErrorCode.SAFETY_BLOCK else "DECLINED",
                message=e.message
            ))
            return ToolCallResult(
                tool_call_id=tool_call_id,
                capability=capability_name,
                status="BLOCKED" if e.code == OPSErrorCode.SAFETY_BLOCK else "DECLINED",
                error=e.message
            )

        # 2. Get Executor Handler
        executor_fn = self.registry.get_executor(capability_name)
        if not executor_fn:
            return ToolCallResult(
                tool_call_id=tool_call_id,
                capability=capability_name,
                status="FAILED",
                error=f"No executor registered for capability: '{capability_name}'"
            )

        # 3. Emit TOOL_STARTED
        await OPSEventBus.emit_ops_event_async(create_event(
            event_type=OPSEventType.TOOL_STARTED,
            session_id=session_id or "default",
            task_id=task_id,
            mission_id=mission_id,
            agent_id=requested_by,
            agent_name=requested_by.title(),
            capability=capability_name,
            tool=capability_name,
            status="RUNNING",
            message=f"Executing capability [{capability_name}]",
            metadata={"arguments": arguments}
        ))

        # 4. Execute Tool
        t0 = time.time()
        try:
            result = await executor_fn(request)
            result.duration_ms = int((time.time() - t0) * 1000)
        except Exception as e:
            logger.error(f"Error executing tool {capability_name}: {e}", exc_info=True)
            result = ToolCallResult(
                tool_call_id=tool_call_id,
                capability=capability_name,
                status="FAILED",
                error=f"Execution error: {str(e)}",
                duration_ms=int((time.time() - t0) * 1000)
            )

        # 5. Emit Tool Completion / Failure
        await OPSEventBus.emit_ops_event_async(create_event(
            event_type=OPSEventType.TOOL_COMPLETED if result.status == "SUCCESS" else OPSEventType.TOOL_FAILED,
            session_id=session_id or "default",
            task_id=task_id,
            mission_id=mission_id,
            agent_id=requested_by,
            capability=capability_name,
            tool=capability_name,
            status="COMPLETED" if result.status == "SUCCESS" else "FAILED",
            message=f"Tool [{capability_name}] finished in {result.duration_ms}ms with status: {result.status}"
        ))

        # 6. Independent Ground-Truth Verification
        await OPSEventBus.emit_ops_event_async(create_event(
            event_type=OPSEventType.VERIFICATION_STARTED,
            session_id=session_id or "default",
            task_id=task_id,
            mission_id=mission_id,
            agent_id="verifier",
            agent_name="Ground-Truth Verifier",
            capability=capability_name,
            status="RUNNING",
            message=f"Asserting physical ground-truth state for [{capability_name}]"
        ))

        is_verified = Verifier.verify_tool_result(request, result)
        if not is_verified and result.status == "SUCCESS":
            result.status = "FAILED"
            if not result.error:
                result.error = "Operation failed physical ground-truth verification check."

        await OPSEventBus.emit_ops_event_async(create_event(
            event_type=OPSEventType.VERIFICATION_PASSED if is_verified else OPSEventType.VERIFICATION_FAILED,
            session_id=session_id or "default",
            task_id=task_id,
            mission_id=mission_id,
            agent_id="verifier",
            agent_name="Ground-Truth Verifier",
            capability=capability_name,
            status="COMPLETED" if is_verified else "FAILED",
            message="Physical state verified successfully." if is_verified else f"Ground-truth verification failed: {result.error}"
        ))

        return result
