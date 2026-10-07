"""
O.P.S. Web Research & Extraction Tools
Crawlee, BeautifulSoup4, and ScrapeGraphAI with injection-isolated outputs.
"""

import asyncio
from typing import Dict, Any
from ops_core.capabilities.schemas import ToolCallRequest, ToolCallResult
from ops_core.services.scraping_service import OPSScrapingService
from ops_core.safety.injection_guard import InjectionGuard


async def execute_web_search(request: ToolCallRequest) -> ToolCallResult:
    query = request.arguments.get("query")
    if not query:
        return ToolCallResult(
            tool_call_id=request.tool_call_id,
            capability=request.capability,
            status="FAILED",
            error="Missing 'query' parameter"
        )

    service = OPSScrapingService()
    res = await asyncio.to_thread(service.auto_research, query)
    
    # Enforce untrusted content boundary
    raw_content = res.get("summary") or res.get("text", "") or res.get("content", "")
    sanitized_content = InjectionGuard.sanitize_web_content(raw_content)
    sources = res.get("sources", [])

    return ToolCallResult(
        tool_call_id=request.tool_call_id,
        capability=request.capability,
        status="SUCCESS",
        result={
            "query": query,
            "title": res.get("title", query),
            "content": sanitized_content,
            "sources": sources,
            "key_points": res.get("key_points", [])
        },
        evidence={
            "results_found": len(sanitized_content) > 0,
            "sources_count": len(sources),
            "content_length": len(sanitized_content)
        }
    )


async def execute_web_crawl(request: ToolCallRequest) -> ToolCallResult:
    return await execute_web_search(request)


async def execute_web_extract_structured(request: ToolCallRequest) -> ToolCallResult:
    return await execute_web_search(request)


async def execute_web_parse_html(request: ToolCallRequest) -> ToolCallResult:
    return await execute_web_search(request)
