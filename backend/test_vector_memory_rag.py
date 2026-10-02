"""
Test Suite for O.P.S. Iteration 3: Vector Memory & Local RAG Subsystem (ChromaDB)
Tests:
1. Codebase Single File and Directory Chunking & Vector Indexing.
2. Semantic Vector Search with Similarity Scores & Line Number Metadata.
3. Long-Term Semantic Memory Item Indexing and Recall.
4. Multi-Tier Session Memory (Level 1 Sliding Window + Level 2 RAG Context Enrichment).
5. REST API Endpoints for RAG Query, Directory Indexing, Collection Stats, and Memory.
"""

import os
import sys
import json
import shutil
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ops_backend.settings")
import django
django.setup()

from rest_framework.test import APIClient
from ops_core.services.rag_service import OPSRAGService
from ops_core.services.session_memory import OPSSessionMemoryManager


class TestIteration3VectorRAG(unittest.TestCase):

    def setUp(self):
        self.client = APIClient()
        self.rag = OPSRAGService()
        self.memory = OPSSessionMemoryManager()
        self.test_dir = tempfile.mkdtemp(prefix="ops_test_rag_")

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_01_codebase_file_and_directory_indexing(self):
        """Test indexing source files into ChromaDB codebase collection."""
        sample_code = """# Sample O.P.S. Math Module
def calculate_hyperparameter_decay(initial_lr, decay_rate, step):
    \"\"\"Calculates exponential learning rate decay.\"\"\"
    return initial_lr * (decay_rate ** step)

def optimize_agent_latency(batch_size, thread_count):
    \"\"\"Calculates optimal worker concurrency.\"\"\"
    return min(batch_size * 2, thread_count * 4)
"""
        test_file = Path(self.test_dir) / "math_utils.py"
        with open(test_file, "w", encoding="utf-8") as f:
            f.write(sample_code)

        res = self.rag.index_file(str(test_file), collection_name="ops_codebase")
        self.assertEqual(res.get("status"), "success")
        self.assertGreaterEqual(res.get("chunks_indexed", 0), 1)

        # Directory indexing
        dir_res = self.rag.index_directory(self.test_dir, collection_name="ops_codebase")
        self.assertEqual(dir_res.get("status"), "success")
        self.assertGreaterEqual(dir_res.get("indexed_files", 0), 1)

    def test_02_semantic_vector_query(self):
        """Test semantic query retrieval and scoring."""
        sample_code = """
class SecureDatabaseGateway:
    def connect_with_ssl(self, host, port, cert_path):
        return f"Connected to {host}:{port} with SSL certificate {cert_path}"
"""
        test_file = Path(self.test_dir) / "db_gateway.py"
        with open(test_file, "w", encoding="utf-8") as f:
            f.write(sample_code)
        self.rag.index_file(str(test_file), collection_name="ops_codebase")

        hits = self.rag.query("How do I connect to the database securely with SSL?", n_results=2)
        self.assertGreaterEqual(len(hits), 1)
        top_hit = hits[0]
        self.assertIn("SecureDatabaseGateway", top_hit.get("text", ""))
        self.assertIn("similarity_score", top_hit)
        self.assertEqual(top_hit.get("metadata", {}).get("file_name"), "db_gateway.py")

    def test_03_memory_item_indexing_and_recall(self):
        """Test indexing long-term user facts and semantic search over memory."""
        self.rag.index_memory_item(
            text="User's primary GPU is NVIDIA RTX 4090 and default local model is Qwen 2.5 Coder",
            memory_id="fact_gpu_spec",
            metadata={"category": "hardware_preference"}
        )

        mem_hits = self.rag.query("What GPU and coding model does the user prefer?", collection_name="ops_memory", n_results=1)
        self.assertGreaterEqual(len(mem_hits), 1)
        self.assertIn("RTX 4090", mem_hits[0].get("text", ""))

    def test_04_session_memory_sliding_window_and_enrichment(self):
        """Test active conversation sliding window and rich multi-tier context compilation."""
        session_id = "test_sess_001"
        self.memory.clear_session(session_id)

        # Add 5 conversation turns
        for i in range(5):
            self.memory.add_turn(session_id, "user", f"Step {i} question")
            self.memory.add_turn(session_id, "assistant", f"Step {i} answer")

        history = self.memory.get_recent_history(session_id)
        self.assertEqual(len(history), 10)

        # Build enriched context for a new question
        enriched = self.memory.build_enriched_context(
            session_id=session_id,
            query="database connection",
            include_codebase_rag=True,
            rag_hits=2
        )

        self.assertEqual(enriched.get("session_id"), session_id)
        self.assertIn("Step 4", enriched.get("formatted_history", ""))
        self.assertIn("formatted_rag_context", enriched)

    def test_05_rest_api_rag_and_memory(self):
        """Test REST endpoints for RAG queries, stats, indexing, and memory."""
        # 1. RAG Stats
        res_stats = self.client.get('/api/v1/rag/stats/')
        self.assertEqual(res_stats.status_code, 200)
        self.assertIn("collections", res_stats.json())

        # 2. RAG Query
        res_query = self.client.post('/api/v1/rag/query/', {
            "query": "learning rate decay formula",
            "collection": "ops_codebase",
            "n_results": 2
        }, format='json')
        self.assertEqual(res_query.status_code, 200)
        self.assertIn("results", res_query.json())

        # 3. Session Memory API (POST turn)
        res_mem_post = self.client.post('/api/v1/memory/', {
            "session_id": "api_test_sess",
            "role": "user",
            "content": "Configure Python 3.14 backend for O.P.S.",
            "save_to_vector_db": True
        }, format='json')
        self.assertEqual(res_mem_post.status_code, 200)

        # 4. Session Memory API (GET history)
        res_mem_get = self.client.get('/api/v1/memory/?session_id=api_test_sess')
        self.assertEqual(res_mem_get.status_code, 200)
        self.assertGreaterEqual(res_mem_get.json().get("turns_count", 0), 1)


if __name__ == "__main__":
    unittest.main()
