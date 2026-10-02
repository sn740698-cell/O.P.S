"""
Test Suite for O.P.S.: LangGraph Multi-Agent Orchestration Engine & Tool Sandbox
Tests:
1. Tool Sandbox: Safe File Read/Write Operations.
2. Tool Sandbox: Terminal Command Execution, Live Output, and Database Audit.
3. Tool Sandbox: Dangerous Command Hard-Block via Safety Gatekeeper.
4. LangGraph Multi-Agent Workflow: Developer Agent Coding Route.
5. LangGraph Multi-Agent Workflow: Browser Agent Web Research Route.
6. REST API: /api/v1/agent/run/ Endpoint Execution.
"""

import os
import sys
import json
import shutil
import tempfile
import asyncio
import unittest
from pathlib import Path

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ops_backend.settings")
import django
django.setup()

from rest_framework.test import APIClient
from channels.db import database_sync_to_async
from ops_core.services.tool_sandbox import OPSToolSandbox
from ops_core.services.permission_manager import OPSPermissionManager
from ops_core.services.agent_orchestrator import OPSMultiAgentOrchestrator
from ops_core.models import ExecutionAuditLog


class TestMultiAgentOrchestrator(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.client = APIClient()
        self.sandbox = OPSToolSandbox()
        self.orchestrator = OPSMultiAgentOrchestrator()
        self.test_dir = tempfile.mkdtemp(prefix="ops_test_sandbox_")
        # Pre-approve test tasks for non-interactive test run
        for tid in ["task-file-001", "task-term-001", "task-workflow-code", "task-workflow-web", "api-agent-task-001"]:
            OPSPermissionManager._task_whitelists[tid] = {"*"}

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    async def test_01_tool_sandbox_file_ops(self):
        """Test safe file write and slice-based reading."""
        test_file = Path(self.test_dir) / "sample.py"
        code = "line 1\nline 2\nline 3\nline 4\nline 5\n"

        # Write file
        w_res = await self.sandbox.write_file(str(test_file), code, overwrite=True, task_id="task-file-001")
        self.assertEqual(w_res.get("status"), "SUCCESS")
        self.assertGreater(w_res.get("bytes_written", 0), 0)

        # Read slice lines 2 to 4
        r_res = await self.sandbox.read_file(str(test_file), start_line=2, end_line=4)
        self.assertEqual(r_res.get("status"), "SUCCESS")
        self.assertEqual(r_res.get("total_lines"), 5)
        self.assertIn("line 2", r_res.get("content", ""))
        self.assertIn("line 4", r_res.get("content", ""))

    async def test_02_tool_sandbox_terminal_execution_and_audit(self):
        """Test safe terminal command execution and audit logging."""
        cmd = "echo OPS_SANDBOX_ONLINE"
        res = await self.sandbox.execute_terminal_command(cmd, task_id="task-term-001")

        self.assertEqual(res.get("status"), "SUCCESS")
        self.assertEqual(res.get("exit_code"), 0)
        self.assertIn("OPS_SANDBOX_ONLINE", res.get("stdout", ""))

        # Verify DB audit entry
        audit = await database_sync_to_async(
            lambda: ExecutionAuditLog.objects.filter(task_id="task-term-001").first()
        )()
        self.assertIsNotNone(audit)
        self.assertEqual(audit.action_type, "run_terminal_cmd")
        self.assertEqual(audit.status, "SUCCESS")

    async def test_03_tool_sandbox_blocked_command(self):
        """Test that destructive command is blocked by tool sandbox."""
        cmd = "rm -rf /"
        res = await self.sandbox.execute_terminal_command(cmd, task_id="task-destruct-sandbox")

        self.assertEqual(res.get("status"), "BLOCKED")
        self.assertEqual(res.get("exit_code"), -1)
        self.assertIn("blacklist", res.get("stderr", "").lower())

    async def test_04_langgraph_workflow_coding_route(self):
        """Test LangGraph routing prompt to Developer Agent and Synthesizer."""
        prompt = "Write a Python function to sort a list in ascending order"
        result = await self.orchestrator.run_task_async(prompt, task_id="task-workflow-code")

        self.assertEqual(result.get("status"), "COMPLETED")
        self.assertIn("final_answer", result)
        self.assertTrue(len(result.get("final_answer", "")) > 0)

    async def test_05_langgraph_workflow_browser_route(self):
        """Test LangGraph routing prompt to Browser Agent."""
        prompt = "Scrape and research documentation at https://example.com"
        result = await self.orchestrator.run_task_async(prompt, task_id="task-workflow-web")

        self.assertEqual(result.get("status"), "COMPLETED")
        self.assertIn("final_answer", result)
        self.assertTrue(len(result.get("final_answer", "")) > 0)

    def test_06_rest_api_agent_workflow(self):
        """Test REST API endpoint /api/v1/agent/run/."""
        res = self.client.post('/api/v1/agent/run/', {
            "prompt": "Create a simple math helper function in Python",
            "task_id": "api-agent-task-001"
        }, format='json')

        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data.get("status"), "COMPLETED")
        self.assertIn("final_answer", data)

    async def test_07_fast_router_direct_tool_path(self):
        """Test Model 1 (Qwen3 0.6B) direct tool bypass for simple commands."""
        prompt = "Open Notepad"
        result = await self.orchestrator.run_task_async(prompt, task_id="task-direct-tool")
        self.assertEqual(result.get("status"), "COMPLETED")
        self.assertEqual(result.get("target_flow"), "DIRECT_TOOL")
        self.assertIn("final_answer", result)

    async def test_08_content_generation_path(self):
        """Test Model 1 routing to Model 3 (Llama 3.2 1B) for content writing."""
        prompt = "Write a professional email requesting project extension"
        result = await self.orchestrator.run_task_async(prompt, task_id="task-content-gen")
        self.assertEqual(result.get("status"), "COMPLETED")
        self.assertEqual(result.get("target_flow"), "CONTENT_GENERATOR")
        self.assertIn("final_answer", result)

    async def test_09_complex_reasoning_planner_path(self):
        """Test Model 1 routing complex software task to Model 2 (Qwen3 1.7B)."""
        prompt = "Create a full React dashboard with authentication and PostgreSQL"
        result = await self.orchestrator.run_task_async(prompt, task_id="task-complex-plan")
        self.assertEqual(result.get("status"), "COMPLETED")
        self.assertEqual(result.get("target_flow"), "REASONING_PLANNER")
        self.assertIn("final_answer", result)


if __name__ == "__main__":
    unittest.main()
