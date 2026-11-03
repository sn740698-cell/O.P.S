import time
import logging
import re
from typing import Dict, Any, List
from research_system.graph.state import ResearchState
from research_system.events.event_bus import event_bus

logger = logging.getLogger(__name__)

def _chunk_text(text: str, max_chunk_size: int = 500, overlap: int = 50) -> List[str]:
    """
    Chunks clean text into digestible semantic passages with mild overlap.
    """
    words = text.split()
    if not words:
        return []
    chunks = []
    i = 0
    while i < len(words):
        chunk_words = words[i:i + max_chunk_size]
        chunks.append(" ".join(chunk_words))
        i += (max_chunk_size - overlap)
    return chunks

def content_processing_worker_node(state: ResearchState) -> Dict[str, Any]:
    """
    Execution Worker 6: Content Processing Worker
    Cleans, normalizes, chunks, and prepares extracted documents for evidence analysis.
    """
    request_id = state.get("request_id", "req_unknown")
    execution_id = state.get("execution_id", "exec_unknown")
    extracted_contents = state.get("extracted_contents", [])
    t0 = time.time()

    event_bus.publish(
        request_id=request_id,
        execution_id=execution_id,
        node_id="content_processing_worker",
        component_name="Content Processing Worker",
        component_type="execution_worker",
        event_type="NODE_STARTED",
        execution_status="RUNNING",
        safe_task_summary=f"Chunking and normalizing text from {len(extracted_contents)} documents",
        tool_name="Deterministic Text Chunking Engine",
        timestamp=t0
    )

    all_chunks = []
    chunk_counter = 1

    for doc_idx, doc in enumerate(extracted_contents, start=1):
        clean_text = doc.get("clean_text", "")
        url = doc.get("url", "")
        title = doc.get("title", f"Document {doc_idx}")
        raw_chunks = _chunk_text(clean_text, max_chunk_size=300, overlap=40)

        for chunk_text in raw_chunks:
            if len(chunk_text.strip()) > 30:
                all_chunks.append({
                    "chunk_id": f"chk_{chunk_counter}",
                    "source_index": doc_idx,
                    "url": url,
                    "title": title,
                    "text": chunk_text
                })
                chunk_counter += 1

    duration = time.time() - t0

    event_bus.publish(
        request_id=request_id,
        execution_id=execution_id,
        node_id="content_processing_worker",
        component_name="Content Processing Worker",
        component_type="execution_worker",
        event_type="NODE_COMPLETED",
        execution_status="COMPLETED",
        safe_task_summary=f"Produced {len(all_chunks)} semantic chunks in {duration:.2f}s",
        safe_output_summary=f"Prepared {len(all_chunks)} passages ready for evidence retrieval",
        tool_name="Deterministic Text Chunking Engine",
        timestamp=time.time()
    )

    node_history = list(state.get("node_history", []))
    node_history.append("content_processing_worker")

    return {
        "processed_chunks": all_chunks,
        "current_active_component": "content_processing_worker",
        "node_history": node_history
    }
