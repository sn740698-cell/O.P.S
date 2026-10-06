"""
O.P.S. Session & Context Manager
Authoritative implementation based on: O.P.S. Pop-up Cockpit — Architecture & Build Specification

Responsibilities:
1. Maintains active multi-turn session state in RAM (current_application, current_page, current_query, selected_object, current_topic, last_failed_location).
2. Resolves contextual follow-up prompts ("it", "him", "play it", "first result", "try Documents", "tell me more").
3. Enforces context priority: Explicit User Statement > Immediate Messages > Session State > Stored Vector Memory.
4. Implements the Refresh contract: resets active conversational context, generates fresh session ID, leaves long-term knowledge base intact.
"""

import time
import re
import uuid
import logging
from typing import List, Dict, Any, Optional, Tuple
from ops_core.services.rag_service import OPSRAGService

logger = logging.getLogger("ops.session_memory")


class OPSSessionMemoryManager:
    """
    Singleton Session & Context Manager for the O.P.S. Pop-up Cockpit.
    """
    _instance = None
    _active_sessions: Dict[str, Dict[str, Any]] = {}

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(OPSSessionMemoryManager, cls).__new__(cls)
            cls._active_sessions = {}
        return cls._instance

    def __init__(self, max_recent_turns: int = 15):
        self.max_recent_turns = max_recent_turns
        self.rag_service = OPSRAGService()

    def _ensure_session(self, session_id: str) -> Dict[str, Any]:
        """Initializes a new structured session object if not already present."""
        if not session_id:
            session_id = f"sess_{int(time.time())}_{uuid.uuid4().hex[:6]}"

        if session_id not in self._active_sessions:
            self._active_sessions[session_id] = {
                "session_id": session_id,
                "created_at": time.time(),
                "updated_at": time.time(),
                "status": "active",
                "current_context": {
                    "application": None,
                    "page": None,
                    "query": None,
                    "selected_object": None,
                    "topic": None,
                    "last_resource": None,
                    "last_failed_location": None,
                    "last_action": None,
                },
                "recent_messages": [],
                "recent_results": [],
                "active_task": None
            }
        return self._active_sessions[session_id]

    def add_turn(
        self,
        session_id: str,
        user_prompt: str,
        assistant_response: str,
        plan_steps: Optional[List[str]] = None,
        tool_logs: Optional[List[str]] = None,
        structured_data: Optional[Dict[str, Any]] = None,
        save_to_vector_db: bool = True
    ):
        """
        Records a completed conversation turn and updates the explicit session state.
        """
        sess = self._ensure_session(session_id)
        sess["updated_at"] = time.time()

        turn_entry = {
            "turn_id": str(uuid.uuid4()),
            "user_prompt": user_prompt,
            "assistant_response": assistant_response,
            "plan_steps": plan_steps or [],
            "tool_logs": tool_logs or [],
            "structured_data": structured_data or {},
            "timestamp": time.time()
        }

        sess["recent_messages"].append(turn_entry)

        # Enforce sliding window
        if len(sess["recent_messages"]) > self.max_recent_turns:
            sess["recent_messages"] = sess["recent_messages"][-self.max_recent_turns:]

        # Update explicit session state from user prompt and response
        self._update_explicit_state(session_id, user_prompt, assistant_response, structured_data)

        # Optionally store in semantic memory for long-term recall
        if save_to_vector_db:
            try:
                self.rag_service.index_chatbot_turn(
                    text=f"[USER]: {user_prompt}\n[OPS]: {assistant_response}",
                    session_id=session_id,
                    role="conversation",
                    metadata={"timestamp": str(turn_entry["timestamp"])}
                )
            except Exception as e:
                logger.debug(f"Vector memory notice: {e}")

    def _update_explicit_state(
        self,
        session_id: str,
        user_prompt: str,
        assistant_response: str,
        structured_data: Optional[Dict[str, Any]] = None
    ):
        """Extracts and updates explicit application, query, topic, and resource state."""
        sess = self._ensure_session(session_id)
        ctx = sess["current_context"]
        p_lower = user_prompt.lower()
        r_lower = assistant_response.lower()

        # 1. Track Application & Web Services
        canonical_apps = {
            "youtube": "YouTube",
            "instagram": "Instagram",
            "insta": "Instagram",
            "spotify": "Spotify",
            "vlc": "VLC",
            "vscode": "VS Code",
            "vs code": "VS Code",
            "calculator": "Calculator",
            "calc": "Calculator",
            "chrome": "Chrome",
            "gemini": "Gemini",
            "claude": "Claude",
            "whatsapp": "WhatsApp"
        }
        for key, name in canonical_apps.items():
            if key in p_lower:
                ctx["application"] = name
                break

        # 2. Track Search Queries & Subpages
        if "youtube" in (ctx.get("application") or "").lower():
            if "search" in p_lower:
                q_match = re.search(r"(?:search\s+for|search|find|play)?\s*([a-zA-Z0-9_\-\. ]+)", user_prompt, re.IGNORECASE)
                if q_match:
                    q = q_match.group(1).replace("youtube", "").replace("search for", "").strip()
                    if q:
                        ctx["query"] = q
                        ctx["page"] = "search_results"
            if "reels" in p_lower:
                ctx["page"] = "reels"

        if "instagram" in (ctx.get("application") or "").lower():
            if "reels" in p_lower:
                ctx["page"] = "reels"
            elif "chat" in p_lower or "message" in p_lower:
                ctx["page"] = "direct"

        # 3. Track Selected Objects ("first result", "second result", "first video")
        if "first result" in p_lower or "first one" in p_lower:
            ctx["selected_object"] = "first result"
        elif "second result" in p_lower or "second one" in p_lower:
            ctx["selected_object"] = "second result"

        # 4. Track Topics (for Web research)
        if any(p_lower.startswith(k) for k in ["who is", "what is", "tell me about", "explain", "research", "compare"]):
            topic_match = re.sub(r"^(?:who\s+is|what\s+is|what\s+are|tell\s+me\s+about|explain|research|compare)\s+", "", user_prompt, flags=re.IGNORECASE).strip(" ?.")
            if topic_match:
                ctx["topic"] = topic_match

        # 5. Track Files and Locations
        file_match = re.search(r"([a-zA-Z0-9_\-\. ]+\.(?:pdf|txt|docx|xlsx|py|json|md|mp4|mkv))", user_prompt, re.IGNORECASE)
        if file_match:
            ctx["last_resource"] = file_match.group(1).strip()

        for loc in ["downloads", "documents", "desktop", "videos", "music", "pictures"]:
            if loc in p_lower:
                if "couldn't find" in r_lower or "not found" in r_lower or "failed" in r_lower:
                    ctx["last_failed_location"] = loc.capitalize()

    def resolve_contextual_prompt(self, session_id: str, prompt: str) -> str:
        """
        Resolves ambiguous follow-up prompts into full actionable instructions using active session state.
        
        Examples:
        - Active app: YouTube, Prompt: "Search for Believer" -> "Open YouTube and search for Believer"
        - Active app: YouTube, Query: Believer, Prompt: "Open the first result" -> "In YouTube search for Believer, open the first result"
        - Active video open, Prompt: "Play it" -> "Play the active YouTube video"
        - Active topic: LangGraph, Prompt: "Tell me more about it" -> "Tell me more about LangGraph"
        - Failed in Downloads, Prompt: "Try Documents" -> "Open [last_resource] from Documents"
        """
        sess = self._ensure_session(session_id)
        ctx = sess.get("current_context", {})
        p_clean = prompt.strip()
        p_lower = p_clean.lower()

        # Rule 1: Explicit statements always take priority (no resolution needed if complete)
        if any(k in p_lower for k in ["open youtube", "open instagram", "who is", "what is", "open vlc", "create folder"]):
            return prompt

        app = ctx.get("application")
        query = ctx.get("query")
        obj = ctx.get("selected_object")
        topic = ctx.get("topic")
        last_res = ctx.get("last_resource")

        # Follow-up Case A: "Search for [query]" with active application
        if app and p_lower.startswith(("search for ", "search ", "find ")):
            q = re.sub(r"^(?:search\s+for|search|find)\s+", "", p_clean, flags=re.IGNORECASE).strip()
            if q and app.lower() not in p_lower:
                resolved = f"In {app}, search for {q}"
                logger.info(f"Resolved follow-up prompt: '{prompt}' -> '{resolved}'")
                return resolved

        # Follow-up Case B: "Open the first result" / "the second one"
        if ("first result" in p_lower or "first one" in p_lower or "second result" in p_lower) and app:
            target = "first result" if ("first" in p_lower) else "second result"
            if query:
                resolved = f"In {app} search results for '{query}', open the {target}"
            else:
                resolved = f"In {app}, open the {target}"
            logger.info(f"Resolved follow-up prompt: '{prompt}' -> '{resolved}'")
            return resolved

        # Follow-up Case C: "Play it"
        if p_lower in ["play it", "play", "start playback", "resume"]:
            if app:
                resolved = f"In {app}, play the current media"
                logger.info(f"Resolved follow-up prompt: '{prompt}' -> '{resolved}'")
                return resolved

        # Follow-up Case D: "Tell me more about it" / "his recent performance" / "how does it work"
        if ("about it" in p_lower or "tell me more" in p_lower or "how does it" in p_lower or "his " in p_lower or "her " in p_lower) and topic:
            resolved = f"Tell me more about {topic}: {prompt}"
            logger.info(f"Resolved follow-up prompt: '{prompt}' -> '{resolved}'")
            return resolved

        # Follow-up Case E: "Try Documents" / "Look in Videos instead"
        if any(loc in p_lower for loc in ["documents", "downloads", "desktop", "videos"]) and last_res:
            loc = next(l for l in ["documents", "downloads", "desktop", "videos"] if l in p_lower)
            resolved = f"Open {last_res} from {loc.capitalize()}"
            logger.info(f"Resolved follow-up prompt: '{prompt}' -> '{resolved}'")
            return resolved

        # Follow-up Case F: "Go back"
        if p_lower in ["go back", "back", "navigate back"]:
            if app:
                return f"In {app}, navigate back to the previous page"

        # Default: Return original prompt unchanged
        return prompt

    def reset_session(self, session_id: str) -> str:
        """
        Implements the Refresh contract:
        - Wipes active conversational and task context in RAM.
        - Generates a fresh, clean session ID.
        - Does NOT delete persistent knowledge base records in ChromaDB.
        """
        new_session_id = f"sess_{int(time.time())}_{uuid.uuid4().hex[:6]}"
        
        # Clear previous session in memory
        if session_id in self._active_sessions:
            del self._active_sessions[session_id]

        # Initialize clean session
        self._ensure_session(new_session_id)
        logger.info(f"O.P.S. Active Session Reset: Old={session_id} -> New={new_session_id}")
        return new_session_id

    def get_session_state(self, session_id: str) -> Dict[str, Any]:
        """Returns the full session state object."""
        return self._ensure_session(session_id)
