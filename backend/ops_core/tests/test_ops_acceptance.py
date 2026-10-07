"""
O.P.S. Comprehensive Architecture & Acceptance Test Suite
Verifies all 10 core architectural invariants and acceptance criteria using unittest.IsolatedAsyncioTestCase.
"""

import unittest
import asyncio
import os
import tempfile

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ops_backend.settings")
import django
django.setup()

from ops_core.router.fast_router import FastRouter, ExecutionMode
from ops_core.orchestration.supervisor import Supervisor
from ops_core.orchestration.planner import Planner, MissionPlan, PlanStep
from ops_core.orchestration.mission_manager import MissionManager, MissionState
from ops_core.session.session_manager import SessionManager
from ops_core.safety.safety_gate import SafetyGate, RiskLevel
from ops_core.capabilities.schemas import ToolCallRequest
from ops_core.capabilities.registry import CapabilityRegistry
from ops_core.tools.executor import ToolExecutor
from ops_core.verification.verifier import Verifier


class TestOPSAcceptanceSuite(unittest.IsolatedAsyncioTestCase):

    async def test_01_chat_fast_path(self):
        """TEST 1: Conversational query routes directly to CHAT without invoking planning or filesystem tools."""
        router = FastRouter()
        decision = await router.route("What is the difference between synchronous and asynchronous Python?")
        self.assertEqual(decision.mode, ExecutionMode.CHAT)
        self.assertFalse(decision.requires_planning)

        supervisor = Supervisor()
        response = await supervisor.handle_request("What is Python?", session_id="test_chat_sess")
        self.assertEqual(response.mode, ExecutionMode.CHAT)
        self.assertEqual(response.status, "SUCCESS")
        self.assertTrue(len(response.content) > 0)

    async def test_02_single_tool_task(self):
        """TEST 2: Direct actionable task routes to TASK mode and executes via capability registry."""
        router = FastRouter()
        decision = await router.route("Create directory test_tmp_dir")
        self.assertIn(decision.mode, [ExecutionMode.TASK, ExecutionMode.MISSION])

        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = os.path.join(tmpdir, "test_output.txt")
            executor = ToolExecutor()
            res = await executor.execute_capability(
                capability_name="filesystem.write",
                arguments={"path": test_file, "content": "ops verified output"},
                requested_by="developer"
            )
            self.assertEqual(res.status, "SUCCESS")
            self.assertTrue(os.path.exists(test_file))
            with open(test_file, "r") as f:
                self.assertEqual(f.read(), "ops verified output")

    async def test_03_full_mission_flow(self):
        """TEST 3: Complex multi-step mission executes sequentially with ground-truth verification."""
        with tempfile.TemporaryDirectory() as tmpdir:
            dir_path = os.path.join(tmpdir, "scaffold_project")
            file_path = os.path.join(dir_path, "index.js")
            
            plan = MissionPlan(
                goal="Scaffold project and create main file",
                steps=[
                    PlanStep(
                        step_id=1,
                        description="Create project directory",
                        assigned_agent="developer",
                        capability="filesystem.create_directory",
                        arguments={"path": dir_path}
                    ),
                    PlanStep(
                        step_id=2,
                        description="Create index.js",
                        assigned_agent="developer",
                        capability="filesystem.write",
                        arguments={"path": file_path, "content": "console.log('hello');"},
                        depends_on=[1]
                    )
                ]
            )

            mission_manager = MissionManager()
            record = await mission_manager.execute_mission(
                goal=plan.goal,
                plan=plan,
                session_id="test_mission_sess"
            )

            self.assertEqual(record.status, MissionState.COMPLETED)
            self.assertEqual(len(record.step_results), 2)
            self.assertTrue(os.path.exists(file_path))

    async def test_04_stop_behavior(self):
        """TEST 4: STOP halts execution but preserves session, conversation history, and context."""
        session_mgr = SessionManager()
        session = session_mgr.create_session()
        sess_id = session.session_id

        session_mgr.add_message(sess_id, "user", "Hello O.P.S.")
        session_mgr.add_message(sess_id, "assistant", "Standing by.")

        stop_res = session_mgr.stop_execution(sess_id)
        self.assertEqual(stop_res["status"], "STOPPED")
        
        retrieved = session_mgr.get_session(sess_id)
        self.assertIsNotNone(retrieved)
        self.assertEqual(len(retrieved.conversation_history), 2)
        self.assertEqual(retrieved.conversation_history[0]["content"], "Hello O.P.S.")

    async def test_05_refresh_behavior(self):
        """TEST 5: REFRESH resets active volatile context and issues a new session_id without deleting persistent memory."""
        session_mgr = SessionManager()
        old_session = session_mgr.create_session()
        old_id = old_session.session_id

        session_mgr.add_message(old_id, "user", "Temporary data.")
        
        new_session = session_mgr.refresh_session(old_id)
        self.assertNotEqual(new_session.session_id, old_id)
        self.assertEqual(len(new_session.conversation_history), 0)

    async def test_06_forbidden_safety_interception(self):
        """TEST 6: Destructive forbidden commands are blocked by Safety Gate."""
        safety_gate = SafetyGate()
        req = ToolCallRequest(
            capability="terminal.execute",
            arguments={"command": "rm -rf / --no-preserve-root"},
            requested_by="developer"
        )
        decision = await safety_gate.evaluate(req)
        self.assertEqual(decision.risk_level, RiskLevel.FORBIDDEN)
        self.assertFalse(decision.approved)

    async def test_07_ground_truth_verification_assertion(self):
        """TEST 7: Ground-truth verifier reports failure when expected file was not created."""
        verifier = Verifier()
        evidence = await verifier.verify_tool_execution(
            capability="filesystem.write",
            arguments={"path": "d:/non_existent_fake_path_12345/file.txt"},
            raw_result={"status": "FAILED"}
        )
        self.assertFalse(evidence.verified)
        self.assertTrue(len(evidence.assertions_failed) > 0)

    async def test_08_bounded_error_recovery(self):
        """TEST 8: Failing step undergoes bounded retry (max 3 retries) and safely terminates."""
        plan = MissionPlan(
            goal="Faulty step mission",
            steps=[
                PlanStep(
                    step_id=1,
                    description="Intentionally failing terminal command",
                    assigned_agent="developer",
                    capability="terminal.execute",
                    arguments={"command": "invalid_command_that_does_not_exist_ops"}
                )
            ]
        )

        mission_manager = MissionManager()
        record = await mission_manager.execute_mission(
            goal=plan.goal,
            plan=plan,
            session_id="test_fault_sess"
        )

        self.assertEqual(record.status, MissionState.FAILED)
        self.assertLessEqual(record.retry_counts.get(1, 0), 3)

    async def test_09_dangerous_permission_prompt(self):
        """TEST 9: Dangerous action (e.g. filesystem.delete) evaluates as DANGEROUS requiring confirmation."""
        req = ToolCallRequest(
            capability="filesystem.delete",
            arguments={"path": "d:/some/dangerous/path.txt"},
            requested_by="automation"
        )
        risk = SafetyGate.evaluate_risk(req)
        self.assertEqual(risk, RiskLevel.DANGEROUS)

    async def test_10_memory_layer_separation(self):
        """TEST 10: Persistent RAG index/retrieval operations remain isolated from active session refresh."""
        session_mgr = SessionManager()
        sess_1 = session_mgr.create_session()
        session_mgr.add_message(sess_1.session_id, "user", "Hello this is a volatile session prompt")

        # RAG Persistent Capability indexing
        executor = ToolExecutor()
        rag_index_res = await executor.execute_capability(
            capability_name="rag.index",
            arguments={"content": "OPS architectural truth definition: local-first deterministic AI OS", "metadata": {"source": "test_spec"}},
            requested_by="rag"
        )
        self.assertEqual(rag_index_res.status, "SUCCESS")

        # Refresh active session
        sess_2 = session_mgr.refresh_session(sess_1.session_id)
        self.assertNotEqual(sess_1.session_id, sess_2.session_id)
        self.assertEqual(len(sess_2.conversation_history), 0)

        # Query persistent RAG after session refresh
        rag_search_res = await executor.execute_capability(
            capability_name="rag.search",
            arguments={"query": "OPS architectural truth definition"},
            requested_by="rag"
        )
        self.assertEqual(rag_search_res.status, "SUCCESS")


if __name__ == "__main__":
    unittest.main()
