"""
O.P.S. Local Vector Memory & RAG Subsystem (ChromaDB)
Provides local embedding, semantic search across codebase, documentation,
and long-term agent memory without external API dependencies.
"""

import os
import re
import uuid
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from django.conf import settings
import chromadb
from chromadb.config import Settings

logger = logging.getLogger("ops.rag")

# Supported file extensions for codebase indexing
CODE_EXTENSIONS = {
    ".py", ".js", ".jsx", ".ts", ".tsx", ".html", ".css", 
    ".json", ".md", ".yaml", ".yml", ".sql", ".sh", ".bat"
}

IGNORED_DIRECTORIES = {
    "venv", ".venv", "node_modules", ".git", "__pycache__", 
    ".idea", ".vscode", "build", "dist", "chroma_storage"
}


class OPSRAGService:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(OPSRAGService, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, storage_dir: Optional[str] = None):
        if getattr(self, '_initialized', False):
            return

        storage_path = storage_dir or getattr(
            settings, 'CHROMA_STORAGE_DIR', Path(__file__).resolve().parent.parent.parent / 'chroma_storage'
        )
        os.makedirs(storage_path, exist_ok=True)

        self.client = chromadb.PersistentClient(path=str(storage_path))
        
        # Primary Collections
        self.codebase_collection = self.client.get_or_create_collection(
            name="ops_codebase",
            metadata={"description": "Indexed project codebase source files"}
        )
        self.memory_collection = self.client.get_or_create_collection(
            name="ops_memory",
            metadata={"description": "Long-term conversation memories and facts"}
        )
        self.docs_collection = self.client.get_or_create_collection(
            name="ops_docs",
            metadata={"description": "System documentation and external scraped articles"}
        )
        # Dedicated Isolated Section for Chatbot Conversational Memory
        self.chatbot_memory_collection = self.client.get_or_create_collection(
            name="ops_chatbot_memory",
            metadata={"description": "Dedicated vector memory partition exclusively for chatbot conversations, contextual turns, and session follow-up recall"}
        )
        self._initialized = True
        logger.info(f"ChromaDB RAG Service initialized at {storage_path} with isolated ops_chatbot_memory partition")

    def _get_collection(self, collection_name: str):
        if collection_name in ["ops_chatbot_memory", "chatbot_memory", "chatbot"]:
            return self.chatbot_memory_collection
        elif collection_name == "ops_memory":
            return self.memory_collection
        elif collection_name == "ops_docs":
            return self.docs_collection
        return self.codebase_collection

    def chunk_code(self, content: str, chunk_size: int = 50, overlap: int = 10) -> List[Dict[str, Any]]:
        """
        Splits source code into overlapping line chunks preserving line numbers.
        """
        lines = content.splitlines()
        if not lines:
            return []

        chunks = []
        total_lines = len(lines)
        start = 0

        while start < total_lines:
            end = min(start + chunk_size, total_lines)
            chunk_text = "\n".join(lines[start:end])
            if chunk_text.strip():
                chunks.append({
                    "text": chunk_text,
                    "start_line": start + 1,
                    "end_line": end
                })
            if end >= total_lines:
                break
            start += chunk_size - overlap

        return chunks

    def index_file(self, file_path: str, collection_name: str = "ops_codebase") -> Dict[str, Any]:
        """
        Indexes a single file into the specified ChromaDB collection.
        """
        path = Path(file_path).resolve()
        if not path.is_file():
            return {"status": "error", "message": f"File not found: {file_path}"}

        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            if not content.strip():
                return {"status": "skipped", "message": "File is empty"}

            collection = self._get_collection(collection_name)
            
            # Remove any existing chunks for this file
            try:
                collection.delete(where={"file_path": str(path)})
            except Exception:
                pass

            chunks = self.chunk_code(content)
            if not chunks:
                return {"status": "skipped", "message": "No indexable content found"}

            ids = []
            documents = []
            metadatas = []

            for i, ch in enumerate(chunks):
                chunk_id = f"{path.name}_{i}_{uuid.uuid4().hex[:6]}"
                ids.append(chunk_id)
                documents.append(ch["text"])
                metadatas.append({
                    "file_path": str(path),
                    "file_name": path.name,
                    "extension": path.suffix.lower(),
                    "start_line": ch["start_line"],
                    "end_line": ch["end_line"]
                })

            collection.add(
                ids=ids,
                documents=documents,
                metadatas=metadatas
            )

            return {
                "status": "success",
                "file_path": str(path),
                "chunks_indexed": len(ids)
            }
        except Exception as e:
            logger.error(f"Failed to index file {file_path}: {e}")
            return {"status": "error", "message": str(e)}

    def index_directory(
        self, 
        directory_path: str, 
        collection_name: str = "ops_codebase",
        allowed_extensions: Optional[set] = None
    ) -> Dict[str, Any]:
        """
        Recursively indexes all allowed code and markdown files in a directory.
        """
        target_dir = Path(directory_path).resolve()
        if not target_dir.is_dir():
            return {"status": "error", "message": f"Directory not found: {directory_path}"}

        extensions = allowed_extensions or CODE_EXTENSIONS
        indexed_files = 0
        total_chunks = 0
        errors = []

        for root, dirs, files in os.walk(target_dir):
            # Prune ignored directories
            dirs[:] = [d for d in dirs if d not in IGNORED_DIRECTORIES and not d.startswith(".")]

            for file in files:
                ext = Path(file).suffix.lower()
                if ext in extensions:
                    file_path = os.path.join(root, file)
                    res = self.index_file(file_path, collection_name=collection_name)
                    if res.get("status") == "success":
                        indexed_files += 1
                        total_chunks += res.get("chunks_indexed", 0)
                    elif res.get("status") == "error":
                        errors.append({"file": file_path, "error": res.get("message")})

        return {
            "status": "success",
            "directory": str(target_dir),
            "indexed_files": indexed_files,
            "total_chunks": total_chunks,
            "errors": errors
        }

    def query(
        self, 
        query_text: str, 
        collection_name: str = "ops_codebase", 
        n_results: int = 4,
        where_filter: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Performs semantic vector search across the specified collection.
        """
        collection = self._get_collection(collection_name)
        if collection.count() == 0:
            return []

        try:
            results = collection.query(
                query_texts=[query_text],
                n_results=min(n_results, collection.count()),
                where=where_filter
            )

            hits = []
            if results and results.get("documents") and len(results["documents"]) > 0:
                docs = results["documents"][0]
                metas = results["metadatas"][0] if results.get("metadatas") else [{}] * len(docs)
                dists = results["distances"][0] if results.get("distances") else [0.0] * len(docs)
                ids = results["ids"][0] if results.get("ids") else [""] * len(docs)

                for doc, meta, dist, chunk_id in zip(docs, metas, dists, ids):
                    hits.append({
                        "id": chunk_id,
                        "text": doc,
                        "metadata": meta,
                        "distance": dist,
                        "similarity_score": round(1.0 - (dist if dist is not None else 0.5), 4)
                    })
            return hits
        except Exception as e:
            logger.error(f"Vector search query failed: {e}")
            return []

    def index_memory_item(self, text: str, memory_id: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Stores a semantic memory fact or conversation turn in ops_memory collection."""
        mem_id = memory_id or f"mem_{uuid.uuid4().hex[:8]}"
        self.memory_collection.add(
            ids=[mem_id],
            documents=[text],
            metadatas=[metadata or {"timestamp": str(uuid.uuid4())}]
        )
        return mem_id

    # ==================== Dedicated Chatbot Vector Database Partition ====================

    def index_chatbot_turn(self, text: str, session_id: str, role: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Stores a dialogue turn exclusively in the dedicated ops_chatbot_memory partition.
        Keeps chatbot conversations isolated from codebase indexing and system documentation.
        """
        mem_id = f"chat_{session_id[:16]}_{uuid.uuid4().hex[:8]}"
        meta = metadata.copy() if metadata else {}
        meta.update({
            "session_id": str(session_id),
            "role": str(role),
            "type": "chatbot_dialogue",
            "timestamp": str(meta.get("timestamp") or uuid.uuid4().hex[:8])
        })
        self.chatbot_memory_collection.add(
            ids=[mem_id],
            documents=[text],
            metadatas=[meta]
        )
        return mem_id

    def query_chatbot_memory(self, query_text: str, session_id: Optional[str] = None, n_results: int = 4) -> List[Dict[str, Any]]:
        """
        Performs semantic vector search across only the dedicated chatbot memory partition.
        Optionally filters by session_id to preserve contextual privacy.
        """
        where_filter = {"session_id": session_id} if session_id else None
        return self.query(
            query_text=query_text,
            collection_name="ops_chatbot_memory",
            n_results=n_results,
            where_filter=where_filter
        )

    def get_chatbot_memory_entries(self, session_id: Optional[str] = None, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Retrieves recent entries directly from the dedicated ops_chatbot_memory partition.
        """
        try:
            where_filter = {"session_id": session_id} if session_id else None
            data = self.chatbot_memory_collection.get(
                where=where_filter,
                limit=limit,
                include=["documents", "metadatas"]
            )
            entries = []
            if data and data.get("ids"):
                for idx, (doc, meta) in enumerate(zip(data["documents"], data["metadatas"])):
                    entries.append({
                        "id": data["ids"][idx],
                        "text": doc,
                        "session_id": meta.get("session_id", "unknown"),
                        "role": meta.get("role", "unknown"),
                        "timestamp": meta.get("timestamp", "")
                    })
            return entries
        except Exception as e:
            logger.error(f"Failed to retrieve chatbot memory entries: {e}")
            return []

    def clear_chatbot_memory(self, session_id: Optional[str] = None) -> int:
        """
        Purges records exclusively from the dedicated chatbot vector partition.
        If session_id is provided, only removes turns for that specific session.
        """
        try:
            if session_id:
                data = self.chatbot_memory_collection.get(where={"session_id": session_id})
                if data and data.get("ids"):
                    self.chatbot_memory_collection.delete(ids=data["ids"])
                    logger.info(f"Purged {len(data['ids'])} vectors from ops_chatbot_memory for session '{session_id}'")
                    return len(data["ids"])
                return 0
            else:
                count = self.chatbot_memory_collection.count()
                ids = self.chatbot_memory_collection.get()["ids"]
                if ids:
                    self.chatbot_memory_collection.delete(ids=ids)
                logger.info(f"Purged entire ops_chatbot_memory collection ({count} vectors)")
                return count
        except Exception as e:
            logger.warning(f"Failed to clear ops_chatbot_memory partition: {e}")
            return 0

    def get_stats(self) -> Dict[str, Any]:
        """Returns statistics on all ChromaDB collections including the dedicated chatbot partition."""
        cb_count = self.codebase_collection.count()
        chat_count = self.chatbot_memory_collection.count()
        mem_count = self.memory_collection.count()
        docs_count = self.docs_collection.count()
        return {
            "collections": {
                "ops_codebase": cb_count,
                "ops_chatbot_memory": chat_count,
                "ops_memory": mem_count,
                "ops_docs": docs_count,
            },
            "dedicated_chatbot_partition": {
                "name": "ops_chatbot_memory",
                "count": chat_count,
                "status": "ISOLATED_PARTITION_ONLINE",
                "embedding_model": "all-MiniLM-L6-v2",
                "dimension": 384
            },
            "total_embeddings": cb_count + chat_count + mem_count + docs_count
        }

    def reset_collection(self, collection_name: str):
        """Clears all records in a collection."""
        collection = self._get_collection(collection_name)
        ids = collection.get()["ids"]
        if ids:
            collection.delete(ids=ids)
