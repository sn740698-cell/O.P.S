"""
Test Suite for O.P.S.: 7-Tier Intelligence Escalation Engine
Tests:
1. Tier 1: Active Conversation State & Immediate Memory Resolution.
2. Tier 2: Project Vector RAG Search & Code Retrieval Resolution.
3. Tier 4: LangGraph Multi-Agent Team Autonomous Orchestration.
4. Tier 6: External Cloud AI Fallback & Local Privacy Synthesis.
5. REST API: /api/v1/intelligence/escalate/ Endpoint Execution & Trace.
"""

import os
import sys
import json
import asyncio
import unittest

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ops_backend.settings")
import django
django.setup()

from rest_framework.test import APIClient
from ops_core.services.escalation_engine import OPSEscalationEngine, OPSEscalationTier
from ops_core.services.session_memory import OPSSessionMemoryManager
from ops_core.services.rag_service import OPSRAGService
from ops_core.services.permission_manager import OPSPermissionManager


class TestIntelligenceEscalation(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.client = APIClient()
        self.engine = OPSEscalationEngine()
        self.memory = OPSSessionMemoryManager()
        self.rag = OPSRAGService()
        # Pre-approve test sessions
        for sid in ["test_escalate_mem", "test_escalate_rag", "test_escalate_agent", "api_escalate_sess"]:
            OPSPermissionManager._task_whitelists[sid] = {"*"}

    async def test_01_tier1_conversation_memory_resolution(self):
        """Test resolving query directly from active conversation buffer."""
        session_id = "test_escalate_mem"
        self.memory.clear_session(session_id)
        self.memory.add_turn(session_id, "user", "Set backend port to 8000")
        self.memory.add_turn(session_id, "assistant", "Django backend configured for port 8000")

        result = await self.engine.process_with_escalation(
            prompt="What was the last thing you said?",
            session_id=session_id
        )

        self.assertEqual(result.get("status"), "RESOLVED")
        self.assertEqual(result.get("resolved_tier"), OPSEscalationTier.TIER_1_MEMORY)
        self.assertIn("Django backend configured for port 8000", result.get("response", ""))

    async def test_02_tier2_vector_rag_resolution(self):
        """Test resolving code query directly from ChromaDB vector search."""
        session_id = "test_escalate_rag"
        self.rag.codebase_collection.add(
            ids=["crypto_func_01"],
            documents=["def initialize_quantum_encryption(key_size=4096):\n    return f'Initialized with {key_size} bits'"],
            metadatas=[{"file_name": "crypto.py", "start_line": 1, "end_line": 2}]
        )

        result = await self.engine.process_with_escalation(
            prompt="Find where initialize_quantum_encryption is defined",
            session_id=session_id
        )

        self.assertEqual(result.get("status"), "RESOLVED")
        self.assertEqual(result.get("resolved_tier"), OPSEscalationTier.TIER_2_RAG)
        self.assertIn("initialize_quantum_encryption", result.get("response", ""))

    async def test_03_tier4_langgraph_multi_agent_resolution(self):
        """Test resolving multi-agent task through LangGraph orchestration."""
        session_id = "test_escalate_agent"
        result = await self.engine.process_with_escalation(
            prompt="Write a Python function to calculate factorial of a number",
            session_id=session_id
        )

        self.assertEqual(result.get("status"), "RESOLVED")
        self.assertIn(result.get("resolved_tier"), [OPSEscalationTier.TIER_4_MULTI_AGENT, OPSEscalationTier.TIER_6_CLOUD_AI])
        self.assertTrue(len(result.get("response", "")) > 0)

    async def test_04_tier6_cloud_ai_fallback_resolution(self):
        """Test external cloud AI escalation fallback when forced."""
        result = await self.engine.process_with_escalation(
            prompt="Analyze architectural differences between monolithic and microkernel AI OS designs",
            force_tier=OPSEscalationTier.TIER_6_CLOUD_AI
        )

        self.assertEqual(result.get("status"), "RESOLVED")
        self.assertEqual(result.get("resolved_tier"), OPSEscalationTier.TIER_6_CLOUD_AI)
        self.assertIn("O.P.S. Intelligence Fallback Resolution", result.get("response", ""))

    def test_05_rest_api_intelligence_escalation(self):
        """Test REST API endpoint /api/v1/intelligence/escalate/."""
        res = self.client.post('/api/v1/intelligence/escalate/', {
            "prompt": "Explain O.P.S. architecture",
            "session_id": "api_escalate_sess"
        }, format='json')

        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data.get("status"), "RESOLVED")
        self.assertIn("resolved_tier", data)
        self.assertIn("escalation_trace", data)


if __name__ == "__main__":
    unittest.main()
