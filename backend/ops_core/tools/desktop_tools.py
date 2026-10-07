"""
O.P.S. Desktop & Application Automation Tools
Controls native applications (VLC, Spotify, VS Code) and desktop window operations.
"""

import asyncio
import os
from typing import Dict, Any
from ops_core.capabilities.schemas import ToolCallRequest, ToolCallResult
from ops_core.services.automation_service import OPSAutomationService


async def execute_desktop_launch_app(request: ToolCallRequest) -> ToolCallResult:
    app_name = request.arguments.get("app_name") or request.arguments.get("application") or request.arguments.get("name")
    if not app_name:
        return ToolCallResult(
            tool_call_id=request.tool_call_id,
            capability=request.capability,
            status="FAILED",
            error="Missing 'app_name' parameter"
        )

    service = OPSAutomationService()
    res = await asyncio.to_thread(service.launch_app, app_name)
    success = res.get("status") == "success" or res.get("success", False)

    return ToolCallResult(
        tool_call_id=request.tool_call_id,
        capability=request.capability,
        status="SUCCESS" if success else "FAILED",
        result={"app_name": app_name, "details": res},
        evidence={"process_running": success, "target": app_name},
        error=res.get("error") if not success else None
    )


async def execute_desktop_open_file(request: ToolCallRequest) -> ToolCallResult:
    path = request.arguments.get("path")
    if not path:
        return ToolCallResult(
            tool_call_id=request.tool_call_id,
            capability=request.capability,
            status="FAILED",
            error="Missing 'path' parameter"
        )

    service = OPSAutomationService()
    abs_path = os.path.abspath(os.path.expanduser(path))
    res = await asyncio.to_thread(service.open_file_or_folder, abs_path)
    success = res.get("status") == "success" or res.get("success", False)

    return ToolCallResult(
        tool_call_id=request.tool_call_id,
        capability=request.capability,
        status="SUCCESS" if success else "FAILED",
        result={"path": abs_path, "details": res},
        evidence={"exists": os.path.exists(abs_path)},
        error=res.get("error") if not success else None
    )


async def execute_desktop_hotkey(request: ToolCallRequest) -> ToolCallResult:
    keys = request.arguments.get("keys", [])
    service = OPSAutomationService()
    
    if isinstance(keys, str):
        keys = [k.strip() for k in keys.split("+")]
        
    res = await asyncio.to_thread(service.execute_desktop_hotkey, keys)
    return ToolCallResult(
        tool_call_id=request.tool_call_id,
        capability=request.capability,
        status="SUCCESS",
        result={"keys": keys, "details": res},
        evidence={"sent": True}
    )
