"""
O.P.S. 2.0 — Temporary Document-Based RAG Service
Ephemeral document processing, Pinecone vector indexing, and session lifecycle management.
Zero permanent storage: vectors live in ephemeral Pinecone namespaces,
raw text chunks live strictly in an in-memory session cache, and everything
is permanently wiped upon conversation refresh or TTL expiration.
"""

import os
import io
import time
import uuid
import logging
import threading
from typing import Dict, Any, List, Optional, Tuple, Callable
from pathlib import Path
from dotenv import load_dotenv

# Ensure environment variables are loaded
load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")

import pypdf
import docx
from pinecone import Pinecone, ServerlessSpec
from langchain_text_splitters import RecursiveCharacterTextSplitter
from research_system.llm.ollama_client import get_ollama_client, MODEL_EMBEDDING

logger = logging.getLogger("OPS.TemporaryRAG")

PINECONE_API_KEY = os.environ.get("PINECONE_API_KEY", "")
PINECONE_INDEX_NAME = os.environ.get("PINECONE_INDEX_NAME", "ops-temporary-rag")
PINECONE_CLOUD = os.environ.get("PINECONE_CLOUD", "aws")
PINECONE_REGION = os.environ.get("PINECONE_REGION", "us-east-1")
EMBEDDING_DIMENSION = int(os.environ.get("EMBEDDING_DIMENSION", "768"))
SESSION_TTL_SECONDS = int(os.environ.get("RAG_SESSION_TTL_SECONDS", "7200"))  # 2 hours default
MAX_FILE_SIZE_BYTES = 25 * 1024 * 1024  # 25 MB max
MAX_DOCS_PER_SESSION = 5


class TemporaryRagService:
    """
    Core engine for temporary document intelligence.
    Manages session-scoped vector storage in Pinecone and ephemeral in-memory chunk caches.
    """
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if getattr(self, "_initialized", False):
            return

        self._pinecone: Optional[Pinecone] = None
        self._index = None
        self._init_pinecone()

        # Ephemeral Session Storage (strictly in-memory, NOT persisted in Postgres/SQLite)
        # _ephemeral_chunks[conv_id] = { chunk_id: { "text": ..., "page": ..., "section": ..., "doc_name": ... } }
        self._ephemeral_chunks: Dict[str, Dict[str, Dict[str, Any]]] = {}
        # _active_documents[conv_id] = { doc_id: { "doc_name": ..., "page_count": ..., "chunk_count": ..., ... } }
        self._active_documents: Dict[str, Dict[str, Dict[str, Any]]] = {}
        # Session access tracking for TTL expiration
        self._session_last_access: Dict[str, float] = {}
        self._storage_lock = threading.RLock()

        # Text splitter
        self._text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=600,
            chunk_overlap=80,
            separators=["\n\n", "\n", ". ", " ", ""]
        )

        self._initialized = True
        logger.info("[RAG SERVICE] Temporary RAG Service initialized successfully.")

    def _init_pinecone(self):
        """Initializes connection to Pinecone and ensures target index exists."""
        if not PINECONE_API_KEY:
            logger.warning("[RAG SERVICE] PINECONE_API_KEY is not set. Pinecone operations will fail until configured.")
            return

        try:
            self._pinecone = Pinecone(api_key=PINECONE_API_KEY)
            existing_indexes = [idx.name for idx in self._pinecone.list_indexes()]

            if PINECONE_INDEX_NAME not in existing_indexes:
                logger.info(f"[RAG SERVICE] Creating serverless Pinecone index '{PINECONE_INDEX_NAME}' (dim={EMBEDDING_DIMENSION})...")
                self._pinecone.create_index(
                    name=PINECONE_INDEX_NAME,
                    dimension=EMBEDDING_DIMENSION,
                    metric="cosine",
                    spec=ServerlessSpec(
                        cloud=PINECONE_CLOUD,
                        region=PINECONE_REGION
                    )
                )
                # Wait for index to become ready
                while not self._pinecone.describe_index(PINECONE_INDEX_NAME).status['ready']:
                    time.sleep(1)

            self._index = self._pinecone.Index(PINECONE_INDEX_NAME)
            logger.info(f"[RAG SERVICE] Connected to Pinecone index '{PINECONE_INDEX_NAME}'.")
        except Exception as e:
            logger.error(f"[RAG SERVICE] Failed to connect to Pinecone: {e}")
            self._index = None

    def get_namespace(self, conversation_id: str) -> str:
        """Returns the isolated, session-specific Pinecone namespace."""
        safe_conv = conversation_id.replace(" ", "_").replace("-", "_")
        return f"ops_rag_{safe_conv}"

    # --------------------------------------------------------------------------
    # Document Parsing & Content Extraction
    # --------------------------------------------------------------------------
    def extract_document(self, file_content: bytes, filename: str) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Extracts structured text from PDF, DOCX, or DOC documents.
        Returns a tuple of (sections_list, metadata).
        Each section contains: text, page_num, section_name.
        """
        ext = filename.lower().rsplit(".", 1)[-1] if "." in filename else ""
        if ext not in ["pdf", "docx", "doc"]:
            raise ValueError(f"Unsupported file format '.{ext}'. Supported formats: .pdf, .docx, .doc")

        if len(file_content) > MAX_FILE_SIZE_BYTES:
            raise ValueError(f"File size exceeds maximum allowable limit of {MAX_FILE_SIZE_BYTES // (1024 * 1024)} MB.")

        if ext == "pdf":
            return self._extract_pdf(file_content, filename)
        elif ext == "docx":
            return self._extract_docx(file_content, filename)
        elif ext == "doc":
            return self._extract_doc(file_content, filename)

    def _extract_pdf(self, file_content: bytes, filename: str) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """Extracts text from PDF with page preservation and scanned document detection."""
        try:
            reader = pypdf.PdfReader(io.BytesIO(file_content))
            num_pages = len(reader.pages)
            if num_pages == 0:
                raise ValueError("The uploaded PDF is empty (0 pages).")

            sections = []
            total_chars = 0
            image_count = 0

            for i, page in enumerate(reader.pages, 1):
                page_text = page.extract_text() or ""
                page_text = page_text.strip()
                total_chars += len(page_text)
                if hasattr(page, "images"):
                    image_count += len(page.images)

                if page_text:
                    sections.append({
                        "text": page_text,
                        "page": i,
                        "section": f"Page {i}"
                    })

            # Check for scanned / image-only PDF
            if total_chars < 30 and (image_count > 0 or num_pages > 0):
                raise ValueError(
                    "The uploaded PDF appears to be a scanned or image-only document without an extractable text layer. "
                    "O.P.S. temporary RAG currently requires text-based documents or OCR pre-processing."
                )

            if not sections:
                raise ValueError("No readable text could be extracted from this PDF.")

            metadata = {
                "filename": filename,
                "file_type": "pdf",
                "page_count": num_pages,
                "total_characters": total_chars
            }
            return sections, metadata
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"[RAG SERVICE] PDF extraction error ({filename}): {e}")
            raise ValueError(f"Failed to extract text from PDF: {str(e)}")

    def _extract_docx(self, file_content: bytes, filename: str) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """Extracts text from Word .docx preserving headings and table contents."""
        try:
            doc = docx.Document(io.BytesIO(file_content))
            sections = []
            current_heading = "Introduction / Overview"
            current_section_paragraphs = []
            estimated_page = 1
            words_in_current_page = 0
            total_chars = 0

            def _flush_section():
                nonlocal current_section_paragraphs, estimated_page
                if current_section_paragraphs:
                    combined = "\n\n".join(current_section_paragraphs).strip()
                    if combined:
                        sections.append({
                            "text": combined,
                            "page": estimated_page,
                            "section": current_heading
                        })
                    current_section_paragraphs = []

            for p in doc.paragraphs:
                p_text = p.text.strip()
                if not p_text:
                    continue

                total_chars += len(p_text)
                p_words = len(p_text.split())
                words_in_current_page += p_words
                if words_in_current_page > 350:
                    estimated_page += 1
                    words_in_current_page = 0

                # Detect heading
                if p.style and p.style.name and p.style.name.startswith("Heading"):
                    _flush_section()
                    current_heading = p_text[:80]
                else:
                    current_section_paragraphs.append(p_text)

            # Extract tables
            for table in doc.tables:
                table_lines = []
                for row in table.rows:
                    row_cells = [cell.text.strip().replace("\n", " ") for cell in row.cells]
                    row_text = " | ".join([c for c in row_cells if c])
                    if row_text:
                        table_lines.append(row_text)
                if table_lines:
                    table_content = "[Table Data]\n" + "\n".join(table_lines)
                    current_section_paragraphs.append(table_content)
                    total_chars += len(table_content)

            _flush_section()

            if not sections or total_chars < 15:
                raise ValueError("The uploaded Word document contains no readable text.")

            metadata = {
                "filename": filename,
                "file_type": "docx",
                "page_count": max(1, estimated_page),
                "total_characters": total_chars
            }
            return sections, metadata
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"[RAG SERVICE] Word DOCX extraction error ({filename}): {e}")
            raise ValueError(f"Failed to parse Word document: {str(e)}")

    def _extract_doc(self, file_content: bytes, filename: str) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """Handles legacy .doc format or instructs user to save as .docx / .pdf."""
        # Check for OLE compound file header (D0 CF 11 E0)
        if file_content.startswith(b"\xd0\xcf\x11\xe0"):
            # Attempt basic ASCII/Unicode text extraction
            try:
                import re
                text = file_content.decode("utf-8", errors="ignore")
                clean_lines = [line.strip() for line in text.split("\n") if len(line.strip()) > 30 and re.match(r"^[A-Za-z0-9\s.,;:!?()-]+$", line.strip())]
                if len(clean_lines) > 5:
                    combined = "\n\n".join(clean_lines)
                    return [{
                        "text": combined,
                        "page": 1,
                        "section": "Main Content"
                    }], {
                        "filename": filename,
                        "file_type": "doc",
                        "page_count": 1,
                        "total_characters": len(combined)
                    }
            except Exception:
                pass

        raise ValueError(
            "Legacy Word format (.doc) contains proprietary binary structures. "
            "Please convert or save the file as a modern Word document (.docx) or PDF (.pdf) for reliable processing."
        )

    # --------------------------------------------------------------------------
    # Chunking & Ingestion Pipeline
    # --------------------------------------------------------------------------
    def chunk_sections(self, sections: List[Dict[str, Any]], doc_id: str, doc_name: str) -> List[Dict[str, Any]]:
        """Splits extracted sections into granular, semantically coherent chunks."""
        chunks = []
        chunk_idx = 0

        for sec in sections:
            sec_text = sec["text"]
            page = sec.get("page", 1)
            section_title = sec.get("section", "General")

            split_texts = self._text_splitter.split_text(sec_text)
            for split_text in split_texts:
                if not split_text.strip():
                    continue

                chunk_id = f"c_{doc_id}_{chunk_idx}"
                chunks.append({
                    "chunk_id": chunk_id,
                    "doc_id": doc_id,
                    "doc_name": doc_name,
                    "page": page,
                    "section": section_title,
                    "text": split_text.strip()
                })
                chunk_idx += 1

        return chunks

    def ingest_document(
        self,
        conversation_id: str,
        file_content: bytes,
        filename: str,
        progress_callback: Optional[Callable[[str, int], None]] = None
    ) -> Dict[str, Any]:
        """
        Full 6-step ingestion workflow:
        1. Validate file & check session limits
        2. Extract content & preserve structure
        3. Chunk into meaningful passages
        4. Generate embeddings via nomic-embed-text
        5. Upsert vectors to session-specific Pinecone namespace (NO full text stored in Pinecone)
        6. Store chunk text strictly in ephemeral in-memory cache
        """
        t0 = time.time()
        self._touch_session(conversation_id)

        # 1. Validation
        with self._storage_lock:
            session_docs = self._active_documents.setdefault(conversation_id, {})
            if len(session_docs) >= MAX_DOCS_PER_SESSION:
                raise ValueError(f"Maximum document limit ({MAX_DOCS_PER_SESSION}) reached for this temporary session.")

        if progress_callback:
            progress_callback("Extracting document text...", 20)

        # 2. Extraction
        sections, metadata = self.extract_document(file_content, filename)
        doc_id = f"doc_{int(time.time())}_{uuid.uuid4().hex[:6]}"

        if progress_callback:
            progress_callback("Preparing semantically structured chunks...", 40)

        # 3. Chunking
        chunks = self.chunk_sections(sections, doc_id, filename)
        if not chunks:
            raise ValueError("No searchable chunks could be generated from this document.")

        if progress_callback:
            progress_callback(f"Generating embeddings for {len(chunks)} passages...", 65)

        # 4. Embeddings Generation
        ollama = get_ollama_client()
        vectors_to_upsert = []
        chunk_lookup = {}

        for ch in chunks:
            # Generate embedding via Ollama
            emb = ollama.embed(ch["text"], model=MODEL_EMBEDDING)
            if not emb or len(emb) != EMBEDDING_DIMENSION:
                raise RuntimeError(
                    f"Embedding generation failed: expected {EMBEDDING_DIMENSION} dimensions, "
                    f"got {len(emb) if emb else 0}."
                )

            # Metadata stored in Pinecone: MINIMAL identifiers only (NO raw text) per privacy requirement
            pinecone_metadata = {
                "doc_id": doc_id,
                "doc_name": filename,
                "chunk_id": ch["chunk_id"],
                "page": int(ch["page"]),
                "section": str(ch["section"])[:100],
                "conversation_id": conversation_id
            }

            vectors_to_upsert.append({
                "id": ch["chunk_id"],
                "values": emb,
                "metadata": pinecone_metadata
            })

            # Store the raw text strictly in the ephemeral chunk lookup
            chunk_lookup[ch["chunk_id"]] = ch

        if progress_callback:
            progress_callback(f"Indexing vectors in Pinecone namespace...", 85)

        # 5. Pinecone Indexing in Session Namespace
        namespace = self.get_namespace(conversation_id)
        if self._index is None:
            self._init_pinecone()
        if self._index is None:
            raise RuntimeError("Pinecone index is unavailable. Verify API key and connectivity.")

        # Batch upsert in batches of 50
        batch_size = 50
        for i in range(0, len(vectors_to_upsert), batch_size):
            batch = vectors_to_upsert[i : i + batch_size]
            self._index.upsert(vectors=batch, namespace=namespace)

        # 6. Ephemeral In-Memory Storage Registration
        with self._storage_lock:
            ephemeral_session = self._ephemeral_chunks.setdefault(conversation_id, {})
            ephemeral_session.update(chunk_lookup)

            doc_info = {
                "doc_id": doc_id,
                "doc_name": filename,
                "page_count": metadata.get("page_count", 1),
                "chunk_count": len(chunks),
                "total_characters": metadata.get("total_characters", 0),
                "created_at": time.time(),
                "status": "ready"
            }
            session_docs[doc_id] = doc_info

        if progress_callback:
            progress_callback("Document indexed and ready for questions.", 100)

        duration = round(time.time() - t0, 2)
        logger.info(
            f"[RAG SERVICE] Successfully ingested '{filename}' (ID: {doc_id}) into namespace '{namespace}' "
            f"in {duration}s. Chunks: {len(chunks)}, Pages: {metadata.get('page_count', 1)}."
        )

        return {
            "status": "success",
            "doc_id": doc_id,
            "filename": filename,
            "page_count": metadata.get("page_count", 1),
            "chunk_count": len(chunks),
            "duration_s": duration,
            "namespace": namespace
        }

    # --------------------------------------------------------------------------
    # Retrieval & Question Answering
    # --------------------------------------------------------------------------
    def query_context(
        self,
        conversation_id: str,
        query: str,
        top_k: int = 4,
        min_score: float = 0.35
    ) -> List[Dict[str, Any]]:
        """
        Retrieves top relevant passages for a user query from the session's Pinecone namespace.
        Retrieves original text strictly from the ephemeral in-memory chunk cache.
        """
        self._touch_session(conversation_id)
        namespace = self.get_namespace(conversation_id)

        with self._storage_lock:
            ephemeral_session = self._ephemeral_chunks.get(conversation_id)
            if not ephemeral_session:
                logger.warning(f"[RAG SERVICE] No ephemeral chunks found for session '{conversation_id}'.")
                return []

        if self._index is None:
            self._init_pinecone()
        if self._index is None:
            logger.error("[RAG SERVICE] Cannot query: Pinecone index not connected.")
            return []

        # 1. Embed query
        ollama = get_ollama_client()
        query_vector = ollama.embed(query, model=MODEL_EMBEDDING)
        if not query_vector:
            logger.error("[RAG SERVICE] Query embedding generation failed.")
            return []

        # 2. Query Pinecone namespace
        try:
            res = self._index.query(
                vector=query_vector,
                top_k=top_k,
                include_metadata=True,
                namespace=namespace
            )
        except Exception as e:
            logger.error(f"[RAG SERVICE] Pinecone query error in namespace '{namespace}': {e}")
            return []

        # 3. Retrieve original text from ephemeral chunk cache
        retrieved_passages = []
        for match in res.matches:
            if match.score < min_score:
                continue

            chunk_id = match.id
            chunk_data = ephemeral_session.get(chunk_id)

            if chunk_data:
                retrieved_passages.append({
                    "chunk_id": chunk_id,
                    "doc_id": chunk_data.get("doc_id"),
                    "doc_name": chunk_data.get("doc_name"),
                    "page": chunk_data.get("page", 1),
                    "section": chunk_data.get("section", "General"),
                    "text": chunk_data.get("text", ""),
                    "score": round(match.score, 4)
                })

        logger.info(f"[RAG SERVICE] Retrieved {len(retrieved_passages)} passages for query '{query[:40]}' in '{namespace}'.")
        return retrieved_passages

    # --------------------------------------------------------------------------
    # Session Management & Complete Deletion (Refresh Button Integration)
    # --------------------------------------------------------------------------
    def has_active_documents(self, conversation_id: str) -> bool:
        """Checks if the conversation has any active temporary documents."""
        with self._storage_lock:
            docs = self._active_documents.get(conversation_id, {})
            return len(docs) > 0

    def get_active_documents(self, conversation_id: str) -> List[Dict[str, Any]]:
        """Lists active temporary documents for the given conversation."""
        with self._storage_lock:
            docs = self._active_documents.get(conversation_id, {})
            return list(docs.values())

    def delete_document(self, conversation_id: str, doc_id: str) -> bool:
        """Removes a single document from the active temporary session and Pinecone namespace."""
        namespace = self.get_namespace(conversation_id)
        with self._storage_lock:
            ephemeral_session = self._ephemeral_chunks.get(conversation_id, {})
            # Find chunk IDs belonging to this doc
            chunks_to_remove = [cid for cid, c in ephemeral_session.items() if c.get("doc_id") == doc_id]

            for cid in chunks_to_remove:
                ephemeral_session.pop(cid, None)

            if conversation_id in self._active_documents:
                self._active_documents[conversation_id].pop(doc_id, None)

        # Delete from Pinecone
        if chunks_to_remove and self._index is not None:
            try:
                self._index.delete(ids=chunks_to_remove, namespace=namespace)
                logger.info(f"[RAG SERVICE] Deleted {len(chunks_to_remove)} vectors for doc '{doc_id}' in '{namespace}'.")
                return True
            except Exception as e:
                logger.error(f"[RAG SERVICE] Error deleting vectors for doc '{doc_id}': {e}")
                return False
        return True

    def clear_session(self, conversation_id: str) -> Dict[str, Any]:
        """
        CRITICAL REFRESH ACTION:
        Permanently wipes all temporary RAG vectors and ephemeral caches for this session:
        1. Awaits Pinecone namespace deletion
        2. Verifies deletion via describe_index_stats
        3. Clears in-memory ephemeral chunks
        4. Clears active documents list
        5. Invalidates session access timestamps
        """
        namespace = self.get_namespace(conversation_id)
        logger.info(f"[RAG REFRESH] Initiating complete temporary data wipe for namespace '{namespace}'...")

        pinecone_deleted = False
        vector_count_after = 0

        # 1. Pinecone Namespace Deletion
        if self._index is not None:
            try:
                self._index.delete(delete_all=True, namespace=namespace)
                time.sleep(1.0)  # Brief await for consistency

                # Verify deletion
                stats = self._index.describe_index_stats()
                namespaces = stats.namespaces or {}
                if namespace not in namespaces or namespaces[namespace].vector_count == 0:
                    pinecone_deleted = True
                    vector_count_after = 0
                else:
                    vector_count_after = namespaces[namespace].vector_count
                    logger.warning(f"[RAG REFRESH] Namespace '{namespace}' still reports {vector_count_after} vectors.")
            except Exception as e:
                logger.error(f"[RAG REFRESH] Pinecone namespace deletion error for '{namespace}': {e}")
                pinecone_deleted = False
        else:
            pinecone_deleted = True

        # 2. Ephemeral In-Memory Storage Purge
        with self._storage_lock:
            purged_chunks = len(self._ephemeral_chunks.pop(conversation_id, {}))
            purged_docs = len(self._active_documents.pop(conversation_id, {}))
            self._session_last_access.pop(conversation_id, None)

        logger.info(
            f"[RAG REFRESH] Session '{conversation_id}' wiped: {purged_docs} docs, "
            f"{purged_chunks} chunks removed from memory. Pinecone deleted: {pinecone_deleted}."
        )

        return {
            "status": "cleared",
            "conversation_id": conversation_id,
            "namespace": namespace,
            "pinecone_vectors_deleted": pinecone_deleted,
            "remaining_vector_count": vector_count_after,
            "purged_chunks_count": purged_chunks,
            "purged_documents_count": purged_docs,
            "verified": pinecone_deleted and (vector_count_after == 0)
        }

    def _touch_session(self, conversation_id: str):
        """Updates last accessed timestamp for TTL management."""
        self._session_last_access[conversation_id] = time.time()

    def cleanup_abandoned_sessions(self, ttl_seconds: int = SESSION_TTL_SECONDS) -> int:
        """
        Background cleanup safety: wipes expired namespaces and ephemeral caches
        if user abandoned session without clicking Refresh.
        """
        now = time.time()
        expired_sessions = []

        with self._storage_lock:
            for conv_id, last_access in list(self._session_last_access.items()):
                if now - last_access > ttl_seconds:
                    expired_sessions.append(conv_id)

        cleaned_count = 0
        for conv_id in expired_sessions:
            logger.info(f"[RAG CLEANUP] Cleaning up abandoned session '{conv_id}' (exceeded {ttl_seconds}s TTL)...")
            self.clear_session(conv_id)
            cleaned_count += 1

        return cleaned_count


# Global singleton service
temporary_rag_service = TemporaryRagService()


def get_temporary_rag_service() -> TemporaryRagService:
    """Returns the singleton TemporaryRagService instance."""
    return temporary_rag_service
