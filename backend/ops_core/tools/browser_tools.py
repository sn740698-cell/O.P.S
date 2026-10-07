"""
O.P.S. Playwright Browser Automation Tools
Deterministic interactive browser automation.
"""

import asyncio
from typing import Dict, Any
from ops_core.capabilities.schemas import ToolCallRequest, ToolCallResult
from ops_core.services.automation_service import OPSAutomationService


async def execute_browser_open(request: ToolCallRequest) -> ToolCallResult:
    url = request.arguments.get("url", "https://www.google.com")
    service = OPSAutomationService()
    
    res = await asyncio.to_thread(service.execute_browser_dom_task, url=url)
    success = res.get("status") == "success" or res.get("success", False)
    
    return ToolCallResult(
        tool_call_id=request.tool_call_id,
        capability=request.capability,
        status="SUCCESS" if success else "FAILED",
        result={"url": url, "details": res},
        evidence={"url_loaded": success, "target_url": url},
        error=res.get("error") if not success else None
    )


async def execute_browser_navigate(request: ToolCallRequest) -> ToolCallResult:
    return await execute_browser_open(request)


async def execute_browser_click(request: ToolCallRequest) -> ToolCallResult:
    selector = request.arguments.get("selector") or request.arguments.get("text")
    service = OPSAutomationService()
    
    res = await asyncio.to_thread(service.execute_browser_dom_task, action="click", selector=selector)
    success = res.get("status") == "success" or res.get("success", False)
    
    return ToolCallResult(
        tool_call_id=request.tool_call_id,
        capability=request.capability,
        status="SUCCESS" if success else "FAILED",
        result={"selector": selector, "details": res},
        evidence={"clicked": success},
        error=res.get("error") if not success else None
    )


async def execute_browser_type(request: ToolCallRequest) -> ToolCallResult:
    text = request.arguments.get("text")
    selector = request.arguments.get("selector")
    service = OPSAutomationService()
    
    res = await asyncio.to_thread(service.execute_browser_dom_task, action="type", text=text, selector=selector)
    success = res.get("status") == "success" or res.get("success", False)
    
    return ToolCallResult(
        tool_call_id=request.tool_call_id,
        capability=request.capability,
        status="SUCCESS" if success else "FAILED",
        result={"text": text, "selector": selector},
        evidence={"input_filled": success},
        error=res.get("error") if not success else None
    )


async def execute_browser_extract(request: ToolCallRequest) -> ToolCallResult:
    service = OPSAutomationService()
    res = await asyncio.to_thread(service.execute_browser_dom_task, action="extract")
    content = res.get("content", "")
    
    return ToolCallResult(
        tool_call_id=request.tool_call_id,
        capability=request.capability,
        status="SUCCESS",
        result={"content": content},
        evidence={"content_length": len(content)}
    )
