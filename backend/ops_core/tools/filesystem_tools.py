"""
O.P.S. Deterministic Filesystem Tools
Safe local filesystem operations with path validation and slice notation.
"""

import os
import shutil
from typing import Dict, Any
from ops_core.capabilities.schemas import ToolCallRequest, ToolCallResult
from ops_core.core.errors import OPSError, OPSErrorCode


async def execute_filesystem_read(request: ToolCallRequest) -> ToolCallResult:
    path = request.arguments.get("path")
    if not path:
        return ToolCallResult(
            tool_call_id=request.tool_call_id,
            capability=request.capability,
            status="FAILED",
            error="Missing 'path' parameter"
        )
    
    abs_path = os.path.abspath(os.path.expanduser(path))
    if not os.path.exists(abs_path):
        return ToolCallResult(
            tool_call_id=request.tool_call_id,
            capability=request.capability,
            status="FAILED",
            error=f"File not found: {path}",
            evidence={"exists": False, "path": abs_path}
        )

    start_line = request.arguments.get("start_line", 1)
    end_line = request.arguments.get("end_line", 500)
    
    try:
        with open(abs_path, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
        
        slice_lines = lines[max(0, start_line - 1):end_line]
        content = "".join(slice_lines)
        
        return ToolCallResult(
            tool_call_id=request.tool_call_id,
            capability=request.capability,
            status="SUCCESS",
            result={"path": abs_path, "content": content, "total_lines": len(lines)},
            evidence={"exists": True, "size_bytes": os.path.getsize(abs_path), "lines_read": len(slice_lines)}
        )
    except Exception as e:
        return ToolCallResult(
            tool_call_id=request.tool_call_id,
            capability=request.capability,
            status="FAILED",
            error=f"Read error: {str(e)}"
        )


async def execute_filesystem_write(request: ToolCallRequest) -> ToolCallResult:
    path = request.arguments.get("path")
    content = request.arguments.get("content", "")
    if not path:
        return ToolCallResult(
            tool_call_id=request.tool_call_id,
            capability=request.capability,
            status="FAILED",
            error="Missing 'path' parameter"
        )

    abs_path = os.path.abspath(os.path.expanduser(path))
    try:
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        with open(abs_path, "w", encoding="utf-8") as f:
            f.write(content)
        
        return ToolCallResult(
            tool_call_id=request.tool_call_id,
            capability=request.capability,
            status="SUCCESS",
            result={"path": abs_path, "bytes_written": len(content.encode("utf-8"))},
            evidence={"exists": os.path.exists(abs_path), "size": os.path.getsize(abs_path)}
        )
    except Exception as e:
        return ToolCallResult(
            tool_call_id=request.tool_call_id,
            capability=request.capability,
            status="FAILED",
            error=f"Write error: {str(e)}"
        )


async def execute_filesystem_create_directory(request: ToolCallRequest) -> ToolCallResult:
    path = request.arguments.get("path")
    if not path:
        return ToolCallResult(
            tool_call_id=request.tool_call_id,
            capability=request.capability,
            status="FAILED",
            error="Missing 'path' parameter"
        )

    abs_path = os.path.abspath(os.path.expanduser(path))
    try:
        os.makedirs(abs_path, exist_ok=True)
        return ToolCallResult(
            tool_call_id=request.tool_call_id,
            capability=request.capability,
            status="SUCCESS",
            result={"path": abs_path, "created": True},
            evidence={"exists": os.path.isdir(abs_path)}
        )
    except Exception as e:
        return ToolCallResult(
            tool_call_id=request.tool_call_id,
            capability=request.capability,
            status="FAILED",
            error=f"Directory creation error: {str(e)}"
        )


async def execute_filesystem_delete(request: ToolCallRequest) -> ToolCallResult:
    path = request.arguments.get("path")
    if not path:
        return ToolCallResult(
            tool_call_id=request.tool_call_id,
            capability=request.capability,
            status="FAILED",
            error="Missing 'path' parameter"
        )

    abs_path = os.path.abspath(os.path.expanduser(path))
    if not os.path.exists(abs_path):
        return ToolCallResult(
            tool_call_id=request.tool_call_id,
            capability=request.capability,
            status="SUCCESS",
            result={"path": abs_path, "deleted": False, "note": "Already absent"},
            evidence={"not_exists": True}
        )

    try:
        if os.path.isdir(abs_path):
            shutil.rmtree(abs_path)
        else:
            os.remove(abs_path)
        
        return ToolCallResult(
            tool_call_id=request.tool_call_id,
            capability=request.capability,
            status="SUCCESS",
            result={"path": abs_path, "deleted": True},
            evidence={"not_exists": not os.path.exists(abs_path)}
        )
    except Exception as e:
        return ToolCallResult(
            tool_call_id=request.tool_call_id,
            capability=request.capability,
            status="FAILED",
            error=f"Delete error: {str(e)}"
        )


async def execute_filesystem_move(request: ToolCallRequest) -> ToolCallResult:
    source = request.arguments.get("source")
    destination = request.arguments.get("destination")
    if not source or not destination:
        return ToolCallResult(
            tool_call_id=request.tool_call_id,
            capability=request.capability,
            status="FAILED",
            error="Missing 'source' or 'destination' parameter"
        )

    src_abs = os.path.abspath(os.path.expanduser(source))
    dst_abs = os.path.abspath(os.path.expanduser(destination))
    
    try:
        shutil.move(src_abs, dst_abs)
        return ToolCallResult(
            tool_call_id=request.tool_call_id,
            capability=request.capability,
            status="SUCCESS",
            result={"source": src_abs, "destination": dst_abs},
            evidence={"dst_exists": os.path.exists(dst_abs), "src_not_exists": not os.path.exists(src_abs)}
        )
    except Exception as e:
        return ToolCallResult(
            tool_call_id=request.tool_call_id,
            capability=request.capability,
            status="FAILED",
            error=f"Move error: {str(e)}"
        )


async def execute_filesystem_list_directory(request: ToolCallRequest) -> ToolCallResult:
    path = request.arguments.get("path", ".")
    abs_path = os.path.abspath(os.path.expanduser(path))
    if not os.path.isdir(abs_path):
        return ToolCallResult(
            tool_call_id=request.tool_call_id,
            capability=request.capability,
            status="FAILED",
            error=f"Directory not found: {path}"
        )

    try:
        entries = os.listdir(abs_path)
        items = []
        for e in entries:
            full = os.path.join(abs_path, e)
            items.append({
                "name": e,
                "is_dir": os.path.isdir(full),
                "size_bytes": os.path.getsize(full) if not os.path.isdir(full) else 0
            })
        return ToolCallResult(
            tool_call_id=request.tool_call_id,
            capability=request.capability,
            status="SUCCESS",
            result={"path": abs_path, "items": items, "count": len(items)},
            evidence={"count": len(items)}
        )
    except Exception as e:
        return ToolCallResult(
            tool_call_id=request.tool_call_id,
            capability=request.capability,
            status="FAILED",
            error=f"List directory error: {str(e)}"
        )
