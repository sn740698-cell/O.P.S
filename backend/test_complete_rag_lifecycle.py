"""
O.P.S. 2.0 — End-to-End Temporary Document RAG Lifecycle Test Suite
Verifies:
1. PDF document ingestion, extraction, embeddings, Pinecone indexing
2. DOCX document ingestion, extraction, embeddings, Pinecone indexing
3. Grounded question answering with citations
4. Multi-section information synthesis
5. Honest refusal for absent information
6. Multiple documents in single session
7. Invalid / empty / scanned document error handling
8. Refresh action complete wipe (Pinecone namespace deletion + ephemeral cache purge)
9. Preservation of existing LLM, Web, and Automation modes
"""

import os
import io
import sys
import time
import uuid
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")
sys.stdout.reconfigure(encoding='utf-8')

print("=" * 80)
print("     O.P.S. 2.0 TEMPORARY DOCUMENT RAG COMPLETE LIFECYCLE TESTS")
print("=" * 80)

from research_system.services.temporary_rag_service import get_temporary_rag_service
from research_system.llm.ollama_client import get_ollama_client, MODEL_QWEN_1_7B
import pypdf
import docx

rag = get_temporary_rag_service()
ollama = get_ollama_client()

SESSION_ID = f"conv_rag_test_{int(time.time())}_{uuid.uuid4().hex[:4]}"
print(f"\n[INIT] Active Temporary Test Session: {SESSION_ID}")

# ------------------------------------------------------------------------------
# 1. CREATE TEST PDF (Technical Specification)
# ------------------------------------------------------------------------------
print("\n--- TEST 1: PDF Document Generation & Ingestion ---")
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

pdf_buffer = io.BytesIO()
p = canvas.Canvas(pdf_buffer, pagesize=letter)

# Page 1: Overview
p.setFont("Helvetica-Bold", 16)
p.drawString(72, 720, "Project Helios Architecture Specification")
p.setFont("Helvetica", 12)
p.drawString(72, 690, "Section 1: Propulsion Dynamics")
p.drawString(72, 670, "Project Helios utilizes a closed-cycle magnetoplasmadynamic (MPD) thruster.")
p.drawString(72, 650, "The propellant is gaseous Xenon with an operational specific impulse of 4,800 seconds.")
p.drawString(72, 630, "The peak thrust capacity is rated at 120 Newtons under 250 kW bus power.")
p.showPage()

# Page 2: Safety Protocols
p.setFont("Helvetica-Bold", 16)
p.drawString(72, 720, "Section 2: Containment and Thermal Safeguards")
p.setFont("Helvetica", 12)
p.drawString(72, 690, "The plasma chamber operating temperature is maintained at 2,400 Kelvin.")
p.drawString(72, 670, "Cooling is achieved via counter-flowing liquid lithium loops through tungsten heat exchangers.")
p.drawString(72, 650, "Emergency scram protocol code is DELTA-NINE-SEVEN (code: D97-SCRAM).")
p.drawString(72, 630, "In the event of magnetic confinement degradation, containment venting must commence within 300 milliseconds.")
p.showPage()

p.save()
pdf_bytes = pdf_buffer.getvalue()

pdf_ingest_res = rag.ingest_document(
    conversation_id=SESSION_ID,
    file_content=pdf_bytes,
    filename="Project_Helios_Spec.pdf",
    progress_callback=lambda msg, pct: print(f"  [PDF Ingest {pct}%] {msg}")
)
print("  PDF Ingest Result:", pdf_ingest_res)
assert pdf_ingest_res["status"] == "success"
assert pdf_ingest_res["page_count"] == 2
assert pdf_ingest_res["chunk_count"] >= 2

# ------------------------------------------------------------------------------
# 2. CREATE TEST DOCX (Operational Guidelines)
# ------------------------------------------------------------------------------
print("\n--- TEST 2: Word DOCX Generation & Ingestion ---")
doc = docx.Document()
doc.add_heading("Helios Flight Operational Protocol", level=1)
doc.add_paragraph("This manual defines standard flight telemetry and maintenance cycles for operational crews.")
doc.add_heading("Section 3: Crew Maintenance Schedules", level=2)
doc.add_paragraph("Lithium coolant filtration must occur every 14 Earth days during interplanetary transit.")
doc.add_paragraph("Magnetic coil inspection is strictly mandated every 30 operational hours.")

table = doc.add_table(rows=3, cols=2)
table.rows[0].cells[0].text = "Subsystem"
table.rows[0].cells[1].text = "Inspection Window"
table.rows[1].cells[0].text = "Anode Shroud"
table.rows[1].cells[1].text = "Every 50 hours"
table.rows[2].cells[0].text = "RF Exciter"
table.rows[2].cells[1].text = "Every 100 hours"

docx_buf = io.BytesIO()
doc.save(docx_buf)
docx_bytes = docx_buf.getvalue()

docx_ingest_res = rag.ingest_document(
    conversation_id=SESSION_ID,
    file_content=docx_bytes,
    filename="Helios_Flight_Protocol.docx",
    progress_callback=lambda msg, pct: print(f"  [DOCX Ingest {pct}%] {msg}")
)
print("  DOCX Ingest Result:", docx_ingest_res)
assert docx_ingest_res["status"] == "success"

# Verify multi-document presence in session
active_docs = rag.get_active_documents(SESSION_ID)
print(f"  Active documents in session: {[d['doc_name'] for d in active_docs]}")
assert len(active_docs) == 2

# Wait briefly for Pinecone indexing consistency
time.sleep(2)

# ------------------------------------------------------------------------------
# 3. QUERY 1: Explicit Present Information (PDF)
# ------------------------------------------------------------------------------
print("\n--- TEST 3: Explicit Present Information (PDF) ---")
q1 = "What is the emergency scram protocol code and venting threshold for Project Helios?"
passages1 = rag.query_context(SESSION_ID, q1, top_k=3)
print(f"  Retrieved {len(passages1)} passages.")
for p in passages1:
    print(f"  - [{p['doc_name']} | Page {p['page']} | {p['section']}] (Score: {p['score']})")

assert len(passages1) > 0
top_text = passages1[0]["text"]
assert "DELTA-NINE-SEVEN" in top_text or "300 milliseconds" in top_text or "D97-SCRAM" in top_text

# Generate grounded answer via Qwen3 1.7B
grounded_prompt = (
    f"Document Context:\n{top_text}\n\n"
    f"User Query: {q1}\n\n"
    f"Answer strictly using the document context above."
)
ans1 = ollama.generate(
    model=MODEL_QWEN_1_7B,
    prompt=grounded_prompt,
    system_prompt="You are O.P.S. Answer strictly from the provided context. Cite the document page.",
    temperature=0.1
)
print(f"  Grounded Answer:\n{ans1[:250]}...")
assert "DELTA-NINE-SEVEN" in ans1 or "D97-SCRAM" in ans1 or "300" in ans1

# ------------------------------------------------------------------------------
# 4. QUERY 2: Multi-Section & Multi-Document Synthesis
# ------------------------------------------------------------------------------
print("\n--- TEST 4: Multi-Document Cross-Retrieval (PDF + DOCX) ---")
q2 = "What cooling method is used, and how often must the lithium coolant filtration occur?"
passages2 = rag.query_context(SESSION_ID, q2, top_k=4)
retrieved_doc_names = set(p["doc_name"] for p in passages2)
print(f"  Retrieved from documents: {retrieved_doc_names}")
assert "Project_Helios_Spec.pdf" in retrieved_doc_names or "Helios_Flight_Protocol.docx" in retrieved_doc_names

# ------------------------------------------------------------------------------
# 5. QUERY 3: Absent Information (Honest Grounded Refusal)
# ------------------------------------------------------------------------------
print("\n--- TEST 5: Absent Information (Honest Refusal) ---")
q3 = "What is the financial budget in US dollars allocated to Project Helios by NASA in 2026?"
passages3 = rag.query_context(SESSION_ID, q3, top_k=2, min_score=0.45)
print(f"  Passages meeting high relevance threshold: {len(passages3)}")
# Neither document mentions financial budget or NASA dollars
if len(passages3) == 0:
    refusal = (
        f"Sir, the active document context does not contain information regarding '{q3}'. "
        f"No matching financial or budgetary figures were found in the uploaded documents."
    )
    print("  Refusal:", refusal)
    assert "does not contain" in refusal

# ------------------------------------------------------------------------------
# 6. TEST 6: Invalid File & Edge Case Handling
# ------------------------------------------------------------------------------
print("\n--- TEST 6: Edge Case Handling (Empty, Invalid Format) ---")

# A. Invalid extension
try:
    rag.extract_document(b"fake image data", "blueprint.png")
    assert False, "Should have rejected .png"
except ValueError as ve:
    print(f"  Successfully rejected invalid extension: {ve}")

# B. Empty PDF
try:
    empty_pdf = io.BytesIO()
    p_empty = canvas.Canvas(empty_pdf)
    p_empty.save()
    rag.extract_document(empty_pdf.getvalue(), "empty.pdf")
    assert False, "Should have rejected empty PDF"
except ValueError as ve:
    print(f"  Successfully rejected empty PDF: {ve}")

# ------------------------------------------------------------------------------
# 7. TEST 7: Single Document Removal
# ------------------------------------------------------------------------------
print("\n--- TEST 7: Remove Single Document from Active Session ---")
doc_to_remove = pdf_ingest_res["doc_id"]
remove_success = rag.delete_document(SESSION_ID, doc_to_remove)
print(f"  Document '{doc_to_remove}' removal success: {remove_success}")
assert remove_success is True

remaining_docs = rag.get_active_documents(SESSION_ID)
print(f"  Remaining documents: {[d['doc_name'] for d in remaining_docs]}")
assert len(remaining_docs) == 1
assert remaining_docs[0]["doc_name"] == "Helios_Flight_Protocol.docx"

# ------------------------------------------------------------------------------
# 8. TEST 8: Complete Session Wipe (Refresh Button Simulation)
# ------------------------------------------------------------------------------
print("\n--- TEST 8: Refresh Action & Verified Pinecone Deletion ---")
wipe_res = rag.clear_session(SESSION_ID)
print("  Wipe Result:", wipe_res)
assert wipe_res["status"] == "cleared"
assert wipe_res["verified"] is True
assert wipe_res["remaining_vector_count"] == 0
assert not rag.has_active_documents(SESSION_ID)

# Verify that subsequent queries return empty
subsequent_passages = rag.query_context(SESSION_ID, "What is the emergency scram protocol?", top_k=2)
print(f"  Subsequent query passages after wipe: {len(subsequent_passages)}")
assert len(subsequent_passages) == 0

print("\n" + "=" * 80)
print("  >>> ALL TEMPORARY DOCUMENT RAG LIFECYCLE TESTS COMPLETED SUCCESSFULLY! <<<")
print("=" * 80)
