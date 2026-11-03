import os
import sys
import io
import time
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(Path(__file__).parent / ".env")

from research_system.services.temporary_rag_service import get_temporary_rag_service

print("Testing TemporaryRagService...")
rag = get_temporary_rag_service()

test_conv_id = f"test_conv_rag_{int(time.time())}"

# 1. Test DOCX Ingestion
import docx
doc = docx.Document()
doc.add_heading("Quantum Computing Fundamentals", level=1)
doc.add_paragraph("Quantum computing harnesses the phenomena of quantum mechanics such as superposition and entanglement.")
doc.add_paragraph("A qubit can represent a 0, a 1, or any quantum proportion of both simultaneously.")
doc.add_heading("Hardware Architectures", level=2)
doc.add_paragraph("Superconducting qubits, trapped ions, and photonic circuits represent primary physical implementations.")
table = doc.add_table(rows=2, cols=2)
table.rows[0].cells[0].text = "Technology"
table.rows[0].cells[1].text = "Operating Temp"
table.rows[1].cells[0].text = "Superconducting"
table.rows[1].cells[1].text = "15 millikelvin"

docx_buf = io.BytesIO()
doc.save(docx_buf)
docx_bytes = docx_buf.getvalue()

print("\n--- Ingesting DOCX ---")
ingest_res = rag.ingest_document(
    conversation_id=test_conv_id,
    file_content=docx_bytes,
    filename="quantum_brief.docx",
    progress_callback=lambda msg, pct: print(f"[{pct}%] {msg}")
)
print("Ingestion result:", ingest_res)
assert ingest_res["status"] == "success"
assert rag.has_active_documents(test_conv_id)

# 2. Test Querying Context
time.sleep(2)  # Wait for Pinecone index propagation
print("\n--- Querying Context ---")
query = "What operating temperature is required for superconducting qubits?"
passages = rag.query_context(conversation_id=test_conv_id, query=query, top_k=2)
print(f"Retrieved {len(passages)} passages:")
for p in passages:
    print(f"- [Score: {p['score']}] (Page {p['page']}, Section: {p['section']}): {p['text']}")

assert len(passages) > 0, "No passages retrieved!"
assert "superconducting" in passages[0]["text"].lower() or "millikelvin" in passages[0]["text"].lower()

# 3. Test Refresh Deletion & Verification
print("\n--- Testing Complete Session Wipe (Refresh) ---")
clear_res = rag.clear_session(test_conv_id)
print("Clear result:", clear_res)
assert clear_res["status"] == "cleared"
assert clear_res["verified"] is True
assert not rag.has_active_documents(test_conv_id)

print("\nALL TEMPORARY RAG SERVICE UNIT TESTS PASSED!")
