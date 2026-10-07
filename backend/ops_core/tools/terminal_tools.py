"""
O.P.S. Sandboxed Terminal & Test Tools
Executes non-interactive shell commands, captures exit codes and stdout/stderr with timeouts.
"""

import asyncio
import os
import subprocess
import time
from typing import Dict, Any
from ops_core.capabilities.schemas import ToolCallRequest, ToolCallResult


async def execute_terminal_command(request: ToolCallRequest) -> ToolCallResult:
    command = request.arguments.get("command")
    cwd = request.arguments.get("cwd", os.getcwd())
    timeout = request.arguments.get("timeout_seconds", 30)

    if not command:
        return ToolCallResult(
            tool_call_id=request.tool_call_id,
            capability=request.capability,
            status="FAILED",
            error="Missing 'command' parameter"
        )

    t0 = time.time()
    try:
        proc = await asyncio.create_subprocess_shell(
            command,
            cwd=cwd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout_bytes, stderr_bytes = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        duration_ms = int((time.time() - t0) * 1000)
        
        stdout_str = stdout_bytes.decode("utf-8", errors="replace").strip()
        stderr_str = stderr_bytes.decode("utf-8", errors="replace").strip()
        exit_code = proc.returncode

        status = "SUCCESS" if exit_code == 0 else "FAILED"
        
        return ToolCallResult(
            tool_call_id=request.tool_call_id,
            capability=request.capability,
            status=status,
            result={
                "command": command,
                "exit_code": exit_code,
                "stdout": stdout_str,
                "stderr": stderr_str,
                "cwd": cwd
            },
            evidence={
                "exit_code": exit_code,
                "duration_ms": duration_ms,
                "stdout_len": len(stdout_str),
                "stderr_len": len(stderr_str)
            },
            error=stderr_str if exit_code != 0 else None,
            duration_ms=duration_ms
        )
    except asyncio.TimeoutError:
        return ToolCallResult(
            tool_call_id=request.tool_call_id,
            capability=request.capability,
            status="FAILED",
            error=f"Command timed out after {timeout} seconds: '{command}'"
        )
    except Exception as e:
        return ToolCallResult(
            tool_call_id=request.tool_call_id,
            capability=request.capability,
            status="FAILED",
            error=f"Terminal execution error: {str(e)}"
        )


async def execute_terminal_run_tests(request: ToolCallRequest) -> ToolCallResult:
    test_framework = request.arguments.get("framework", "auto")
    cwd = request.arguments.get("cwd", os.getcwd())
    
    # Auto-detect test runner if not specified
    if test_framework == "auto":
        if os.path.exists(os.path.join(cwd, "package.json")):
            cmd = "npm test -- --run" if os.path.exists(os.path.join(cwd, "vitest.config.ts")) else "npm test"
        elif os.path.exists(os.path.join(cwd, "manage.py")):
            cmd = "python manage.py test"
        else:
            cmd = "python -m pytest"
    else:
        cmd = request.arguments.get("command", "python -m pytest")

    request.arguments["command"] = cmd
    return await execute_terminal_command(request)
