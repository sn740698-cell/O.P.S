"""
O.P.S. Persistent RAG Tools
ChromaDB semantic search and document indexing.
"""

import asyncio
from typing import Dict, Any, List
from ops_core.capabilities.schemas import ToolCallRequest, ToolCallResult
from ops_core.services.rag_service import OPSRAGService


async def execute_rag_search(request: ToolCallRequest) -> ToolCallResult:
    query = request.arguments.get("query")
    n_results = request.arguments.get("n_results", 5)
    
    if not query:
        return ToolCallResult(
            tool_call_id=request.tool_call_id,
            capability=request.capability,
            status="FAILED",
            error="Missing 'query' parameter"
        )

    service = OPSRAGService()
    # Search across docs and codebase
    results = await asyncio.to_thread(service.query, query, collection_name="ops_docs", n_results=n_results)
    if not results:
        results = await asyncio.to_thread(service.query, query, collection_name="ops_codebase", n_results=n_results)
    
    return ToolCallResult(
        tool_call_id=request.tool_call_id,
        capability=request.capability,
        status="SUCCESS",
        result={"query": query, "matches": results, "count": len(results)},
        evidence={"results_count": len(results), "has_matches": len(results) > 0}
    )


async def execute_rag_ingest(request: ToolCallRequest) -> ToolCallResult:
    path = request.arguments.get("path")
    content = request.arguments.get("content") or request.arguments.get("text")
    metadata = request.arguments.get("metadata", {})
    service = OPSRAGService()
    
    if content:
        import uuid
        doc_id = f"doc_{uuid.uuid4().hex[:8]}"
        coll = service._get_collection("ops_docs")
        await asyncio.to_thread(
            coll.add,
            ids=[doc_id],
            documents=[content],
            metadatas=[metadata or {"type": "direct_text"}]
        )
        return ToolCallResult(
            tool_call_id=request.tool_call_id,
            capability=request.capability,
            status="SUCCESS",
            result={"doc_id": doc_id, "indexed_chunks": 1},
            evidence={"document_indexed": True}
        )

    if path:
        res = await asyncio.to_thread(service.ingest_file_or_directory, path)
        return ToolCallResult(
            tool_call_id=request.tool_call_id,
            capability=request.capability,
            status="SUCCESS",
            result={"path": path, "indexed_chunks": res.get("chunks", 1)},
            evidence={"document_indexed": True}
        )

    return ToolCallResult(
        tool_call_id=request.tool_call_id,
        capability=request.capability,
        status="FAILED",
        error="Either 'path' or 'content' is required for rag.index"
    )
