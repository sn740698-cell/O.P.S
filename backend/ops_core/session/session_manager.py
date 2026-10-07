"""
O.P.S. Canonical Session Manager
Enforces strict separation between Active Session Memory and Persistent Knowledge.
Implements the mandatory STOP vs REFRESH invariant.
"""

import time
import uuid
import logging
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from ops_core.orchestration.mission_manager import MissionManager

from ops_core.core.events import OPSEventType, create_event
from ops_core.services.event_bus import OPSEventBus

logger = logging.getLogger("ops.session.manager")


class ActiveSession(BaseModel):
    session_id: str
    created_at: float = Field(default_factory=time.time)
    updated_at: float = Field(default_factory=time.time)
    
    # Active Session State (Volatile / Reset on Refresh)
    conversation_history: List[Dict[str, Any]] = Field(default_factory=list)
    current_task: Optional[str] = None
    current_mission_id: Optional[str] = None
    current_agent: Optional[str] = None
    current_tool: Optional[str] = None
    current_plan: Optional[Dict[str, Any]] = None
    pending_approvals: List[str] = Field(default_factory=list)
    temporary_context: Dict[str, Any] = Field(default_factory=dict)
    errors: List[str] = Field(default_factory=list)
    is_active: bool = True


class SessionManager:
    _instance = None
    _sessions: Dict[str, ActiveSession] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SessionManager, cls).__new__(cls)
            cls._sessions = {}
        return cls._instance

    def create_session(self) -> ActiveSession:
        """Creates a fresh active session."""
        session_id = f"sess_{uuid.uuid4().hex[:10]}"
        session = ActiveSession(session_id=session_id)
        self._sessions[session_id] = session
        logger.info(f"Created new active session: {session_id}")
        OPSEventBus.emit_ops_event(create_event(
            event_type=OPSEventType.SESSION_CREATED,
            session_id=session_id,
            message="New session created."
        ))
        return session

    def get_or_create_session(self, session_id: Optional[str] = None) -> ActiveSession:
        """Retrieves existing active session or creates a new one."""
        if session_id and session_id in self._sessions:
            session = self._sessions[session_id]
            session.updated_at = time.time()
            return session
        return self.create_session()

    def get_session(self, session_id: str) -> Optional[ActiveSession]:
        return self._sessions.get(session_id)

    def add_message(self, session_id: str, role: str, content: str, metadata: Optional[Dict[str, Any]] = None):
        session = self.get_or_create_session(session_id)
        msg = {
            "role": role,
            "content": content,
            "timestamp": time.time(),
            "metadata": metadata or {}
        }
        session.conversation_history.append(msg)
        session.updated_at = time.time()

    def stop_execution(self, session_id: str) -> Dict[str, Any]:
        """
        STOP:
        - Stops current execution (aborts running mission/task)
        - Preserves current session & ID
        - Preserves conversation history
        - Preserves context and mission state
        - Allows continuation later
        """
        session = self.get_session(session_id)
        if not session:
            return {"status": "NOT_FOUND", "message": "Session not found."}

        # Cancel running mission if active
        if session.current_mission_id:
            mission_manager = MissionManager()
            mission_manager.cancel_mission(session.current_mission_id)

        session.current_task = None
        session.current_agent = None
        session.current_tool = None
        session.updated_at = time.time()
        
        OPSEventBus.emit_ops_event(create_event(
            event_type=OPSEventType.SESSION_STOPPED,
            session_id=session_id,
            status="PAUSED",
            message="Active execution stopped. Session and conversation context preserved."
        ))

        logger.info(f"Session {session_id} execution stopped (Session & Context preserved).")
        return {
            "status": "STOPPED",
            "session_id": session_id,
            "message": "Execution stopped. Session and conversation context preserved.",
            "history_length": len(session.conversation_history)
        }

    def refresh_session(self, session_id: str) -> ActiveSession:
        """
        REFRESH:
        - Resets active session
        - Clears conversation, tasks, missions, plans, temporary context
        - Clears pending approvals
        - Generates a NEW session ID
        - NEVER deletes ChromaDB, persistent embeddings, or project files
        """
        # Cancel any active mission in old session
        old_session = self.get_session(session_id)
        if old_session and old_session.current_mission_id:
            mission_manager = MissionManager()
            mission_manager.cancel_mission(old_session.current_mission_id)
            old_session.is_active = False

        OPSEventBus.emit_ops_event(create_event(
            event_type=OPSEventType.SESSION_RESET,
            session_id=session_id,
            status="IDLE",
            message="Active session reset. Persistent memory remains intact."
        ))

        # Create brand new session
        new_session = self.create_session()
        logger.info(f"Refreshed session: {session_id} -> {new_session.session_id} (Persistent memory preserved).")
        return new_session
