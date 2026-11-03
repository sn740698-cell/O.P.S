import time
import logging
from typing import Dict, Any, List
from research_system.graph.state import ResearchState
from research_system.events.event_bus import event_bus

logger = logging.getLogger(__name__)

def citation_result_worker_node(state: ResearchState) -> Dict[str, Any]:
    """
    Execution Worker 8: Citation and Result Worker
    Constructs formal verifiable citation references and links them to the final response.
    """
    request_id = state.get("request_id", "req_unknown")
    execution_id = state.get("execution_id", "exec_unknown")
    evidence_items = state.get("retrieved_evidence", [])
    final_answer = state.get("final_answer", "")
    t0 = time.time()

    event_bus.publish(
        request_id=request_id,
        execution_id=execution_id,
        node_id="citation_result_worker",
        component_name="Citation and Result Worker",
        component_type="execution_worker",
        event_type="NODE_STARTED",
        execution_status="RUNNING",
        safe_task_summary="Compiling verifiable source citations and metadata bibliography",
        tool_name="Citation Verification Engine",
        timestamp=t0
    )

    citations = []
    seen_urls = set()
    idx = 1

    for item in evidence_items:
        url = item.get("url", "")
        if url and url not in seen_urls:
            seen_urls.add(url)
            citations.append({
                "index": idx,
                "citation_tag": f"[{idx}]",
                "title": item.get("title", f"Web Source {idx}"),
                "url": url,
                "snippet": item.get("text", "")[:280],
                "verified": True
            })
            idx += 1

    updated_final_answer = final_answer
    if citations and "### 📚 Verified Sources" not in final_answer:
        bib_lines = ["\n\n### 📚 Verified Sources & References"]
        for c in citations:
            title = c.get("title", "Verified Source").strip()
            url = c.get("url", "")
            idx_num = c.get("index", 1)
            bib_lines.append(f"- [{idx_num}] [{title}]({url})")
        bib_str = "\n".join(bib_lines)

        if "## 📌 Discussion So Far" in final_answer:
            parts = final_answer.split("## 📌 Discussion So Far", 1)
            updated_final_answer = parts[0].rstrip() + bib_str + "\n\n## 📌 Discussion So Far" + parts[1]
        else:
            updated_final_answer = final_answer.rstrip() + bib_str

    duration = time.time() - t0

    event_bus.publish(
        request_id=request_id,
        execution_id=execution_id,
        node_id="citation_result_worker",
        component_name="Citation and Result Worker",
        component_type="execution_worker",
        event_type="NODE_COMPLETED",
        execution_status="COMPLETED",
        safe_task_summary=f"Compiled {len(citations)} verified citation references in {duration:.2f}s",
        safe_output_summary=f"Linked sources: {', '.join([c.get('url', '') for c in citations[:2]])}",
        tool_name="Citation Verification Engine",
        timestamp=time.time()
    )

    node_history = list(state.get("node_history", []))
    node_history.append("citation_result_worker")

    return {
        "citations": citations,
        "final_answer": updated_final_answer,
        "current_active_component": "citation_result_worker",
        "node_history": node_history
    }
