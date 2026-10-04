"""
O.P.S. Temporary Chat & Session Memory Manager
Provides:
- In-Memory Conversation Context (RAM only, temporary for current chat session)
- Contextual Follow-up & Pronoun Resolution ("him", "her", "it", "that", "this", "tell me more")
- Zero Permanent Storage (Cleared on page refresh or user purge)
"""

import time
import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from ops_core.services.rag_service import OPSRAGService

logger = logging.getLogger("ops.memory")


class OPSSessionMemoryManager:
    _instance = None
    _active_sessions: Dict[str, List[Dict[str, Any]]] = {}

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(OPSSessionMemoryManager, cls).__new__(cls)
            cls._active_sessions = {}
        return cls._instance

    def __init__(self, max_recent_turns: int = 12):
        self.max_recent_turns = max_recent_turns
        self.rag_service = OPSRAGService()

    def add_turn(
        self, 
        session_id: str, 
        role: str, 
        content: str, 
        metadata: Optional[Dict[str, Any]] = None,
        save_to_vector_db: bool = True
    ):
        """
        Adds a conversation turn to active memory and automatically indexes into the
        dedicated vector database partition (ops_chatbot_memory).
        """
        if not session_id:
            session_id = "default_session"

        if session_id not in self._active_sessions:
            self._active_sessions[session_id] = []

        entry = {
            "role": role,
            "content": content,
            "timestamp": time.time(),
            "metadata": metadata or {}
        }
        self._active_sessions[session_id].append(entry)

        # Enforce sliding window in memory
        if len(self._active_sessions[session_id]) > self.max_recent_turns:
            self._active_sessions[session_id] = self._active_sessions[session_id][-self.max_recent_turns:]

        # Opt-in vector storage specifically in the dedicated ops_chatbot_memory partition
        if save_to_vector_db:
            try:
                self.rag_service.index_chatbot_turn(
                    text=f"[{role.upper()}]: {content}",
                    session_id=session_id,
                    role=role,
                    metadata={"timestamp": str(entry["timestamp"])}
                )
            except Exception as e:
                logger.warning(f"Failed to index turn into dedicated chatbot vector partition: {e}")

    def get_recent_history(self, session_id: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Returns recent conversation turns for the given session from RAM."""
        history = self._active_sessions.get(session_id, [])
        if limit:
            return history[-limit:]
        return history

    def get_formatted_history(self, session_id: str, limit: int = 6) -> str:
        """
        Returns a formatted multi-turn string for injection into LLM context:
        User: Who is Brad Pitt?
        O.P.S.: [•] Brad Pitt is an American actor...
        """
        turns = self.get_recent_history(session_id, limit=limit)
        if not turns:
            return ""

        formatted_lines = []
        for t in turns:
            speaker = "User" if t["role"] == "user" else "O.P.S."
            # Clean content snippet
            text = t["content"]
            if len(text) > 400:
                text = text[:400] + "..."
            formatted_lines.append(f"{speaker}: {text}")

        return "\n".join(formatted_lines)

    @staticmethod
    def _extract_entity_from_turn(role: str, content: str) -> Optional[str]:
        """
        Extracts the primary subject/entity discussed in a previous turn.
        """
        if role == 'user':
            c = re.sub(
                r'^(who\s+is|who\s+was|what\s+is|what\s+are|tell\s+me\s+about|explain|search\s+for|search)\s+',
                '',
                content,
                flags=re.IGNORECASE
            ).strip(' ?."\'')
            if len(c) > 1 and not any(c.lower().startswith(p) for p in ['how', 'why', 'where', 'when', 'can you']):
                return c
        elif role == 'assistant':
            m = re.search(r'\[•\]\s*(?:DOSSIER|IDENTITY|CONCEPT|LIVE WIRE):\s*([A-Za-z0-9\s]+?)(?:\s+(?:is|was|refers to|represents|born|—|-|\()|$)', content)
            if m and len(m.group(1).strip().split()) <= 5:
                return m.group(1).strip()
            m2 = re.search(r'(?:\[•\]\s*)?([A-Z][a-zA-Z\s]+?)\s+(?:is|was|refers to|represents)\b', content)
            if m2 and len(m2.group(1).strip().split()) <= 4:
                return m2.group(1).strip()
            m_full = re.search(r'\[•\]\s*(?:DOSSIER|IDENTITY|CONCEPT|LIVE WIRE):\s*([^\n.,]+)', content)
            if m_full:
                candidate = m_full.group(1).strip()
                if len(candidate.split()) <= 4:
                    return candidate
        return None

    def resolve_contextual_query(self, session_id: str, prompt: str) -> Tuple[str, Optional[str]]:
        """
        Understands follow-up questions referencing previous messages.
        Resolves pronouns ('him', 'her', 'it', 'that', 'this', 'them', 'his', 'their')
        and follow-up phrases ('tell me more', 'more details', 'continue', 'what else').

        Example:
        Previous: "Who is Brad Pitt?"
        Current: "Tell me more about him."
        Returns: ("Tell me more about Brad Pitt", "Brad Pitt")
        """
        history = self.get_recent_history(session_id, limit=6)
        if not history:
            return prompt, None

        pronoun_pattern = r'\b(him|her|it|its|that|this|them|his|their|whose)\b'
        followup_verbs = [
            'tell me more', 'more details', 'more about', 'what else',
            'continue', 'explain further', 'elaborate', 'what did he',
            'what did she', 'who was he', 'who was she', 'where is he', 'where is she',
            'tell more', 'give more info', 'give more information', 'expand',
            'tell more about the chat', 'tell me more about the chat', 'tell more about it',
            'tell me more about it', 'give me more info', 'more info', 'go on', 'deep dive'
        ]
        p_lower = prompt.lower().strip()

        is_followup = (
            bool(re.search(pronoun_pattern, p_lower)) or 
            any(p_lower.startswith(v) for v in followup_verbs) or 
            p_lower in followup_verbs or
            bool(re.search(r'tell\s+.*more', p_lower)) or
            bool(re.search(r'give\s+.*more\s+info', p_lower)) or
            bool(re.search(r'explain\s+.*more', p_lower))
        )

        if not is_followup:
            return prompt, None

        # Search backwards through conversation history to find the most recent entity/subject
        # First check user queries backwards as they are typically concise ("Who is Brad Pitt?")
        entity = None
        for turn in reversed(history):
            if turn['role'] == 'user':
                candidate = self._extract_entity_from_turn(turn['role'], turn['content'])
                if candidate and len(candidate.split()) <= 4:
                    entity = candidate
                    break

        if not entity:
            for turn in reversed(history):
                candidate = self._extract_entity_from_turn(turn['role'], turn['content'])
                if candidate:
                    entity = candidate
                    break

        # Fallback to semantic search in dedicated vector database partition
        if not entity:
            try:
                vector_hits = self.rag_service.query_chatbot_memory(prompt, session_id=session_id, n_results=4)
                for hit in vector_hits:
                    meta = hit.get("metadata", {})
                    candidate = self._extract_entity_from_turn(meta.get("role", "user"), hit.get("text", ""))
                    if candidate and len(candidate.split()) <= 4:
                        entity = candidate
                        break
            except Exception as e:
                logger.warning(f"Vector search fallback for pronoun resolution failed: {e}")

        if not entity:
            return prompt, None

        # Resolve pronoun or phrase with the entity name
        resolved = prompt
        if re.search(r'\b(his|their|its)\b', resolved, flags=re.IGNORECASE):
            resolved = re.sub(r'\b(his|their|its)\b', f"{entity}'s", resolved, flags=re.IGNORECASE)
        if re.search(r'\b(him|her|it|that|this|them)\b', resolved, flags=re.IGNORECASE):
            resolved = re.sub(r'\b(him|her|it|that|this|them)\b', entity, resolved, flags=re.IGNORECASE)
        elif any(p_lower.startswith(v) for v in followup_verbs) or p_lower in followup_verbs:
            if entity.lower() not in resolved.lower():
                clean_resolved = resolved.rstrip('.?! ')
                resolved = f"{clean_resolved} about {entity}"

        logger.info(f"[Session Memory] Resolved follow-up directive: '{prompt}' -> '{resolved}' (Entity: '{entity}')")
        return resolved, entity

    def build_enriched_context(
        self, 
        session_id: str, 
        query: str, 
        include_codebase_rag: bool = False,
        rag_hits: int = 3
    ) -> Dict[str, Any]:
        """
        Synthesizes active conversation history for LLM injection.
        """
        recent_turns = self.get_recent_history(session_id, limit=6)
        history_str = self.get_formatted_history(session_id, limit=6)
        
        vector_context = []
        if include_codebase_rag:
            code_results = self.rag_service.query(query, collection_name="ops_codebase", n_results=rag_hits)
            vector_context = code_results

        rag_str = "\n\n".join([
            f"--- Snippet from {h.get('metadata', {}).get('file_name', 'memory')} (Lines {h.get('metadata', {}).get('start_line', 1)}-{h.get('metadata', {}).get('end_line', 1)}) ---\n{h.get('text', '')}"
            for h in vector_context
        ])

        return {
            "session_id": session_id,
            "recent_turns_count": len(recent_turns),
            "formatted_history": history_str,
            "formatted_rag_context": rag_str
        }

    def clear_session(self, session_id: str):
        """Clears in-memory buffer for a session and purges isolated chatbot vector memory for this session."""
        if session_id in self._active_sessions:
            del self._active_sessions[session_id]
            logger.info(f"[Session Memory] RAM buffer purged for session: '{session_id}'")
        
        # Purge any vectors in the dedicated chatbot collection for this session
        try:
            self.rag_service.clear_chatbot_memory(session_id=session_id)
        except Exception as e:
            logger.warning(f"Failed to clear chatbot vector partition for session {session_id}: {e}")

    def clear_all_sessions(self):
        """Purges all sessions from RAM and wipes the dedicated chatbot vector partition."""
        self._active_sessions.clear()
        try:
            self.rag_service.clear_chatbot_memory()
        except Exception as e:
            logger.warning(f"Failed to clear chatbot vector partition: {e}")
        logger.info("[Session Memory] All temporary session memories and vector partition purged.")

    def get_chatbot_vector_stats(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Returns statistics and entries from the dedicated chatbot vector partition."""
        stats = self.rag_service.get_stats()
        entries = self.rag_service.get_chatbot_memory_entries(session_id=session_id, limit=10)
        return {
            "partition": "ops_chatbot_memory",
            "session_id": session_id,
            "total_chatbot_vectors": stats.get("dedicated_chatbot_partition", {}).get("count", 0),
            "recent_entries": entries
        }
