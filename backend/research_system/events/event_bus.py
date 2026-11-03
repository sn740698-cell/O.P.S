import json
import time
import logging
import queue
from typing import Dict, Any, List, Optional, Set

logger = logging.getLogger(__name__)

class EventBus:
    """
    Central Real-Time Event Bus for O.P.S. 2.0 Web Research and Continuous Chat.
    Connects LangGraph execution events and text streams directly to Server-Sent Events (SSE)
    and persistent storage, with support for cancellation and conversation lifecycle management.
    Uses thread-safe queue.Queue to support synchronous multi-threaded WSGI streaming.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(EventBus, cls).__new__(cls)
            cls._subscribers = {}       # channel_key (request_id or conversation_id) -> list of queue.Queue
            cls._history = {}           # channel_key -> list of event dicts
            cls._cancelled_conversations = set()  # set of cancelled conversation_ids
            cls._request_to_conv = {}   # request_id -> conversation_id mapping
        return cls._instance

    def publish(
        self,
        request_id: str,
        execution_id: str,
        node_id: str,
        component_name: str,
        component_type: str,
        event_type: str,
        execution_status: str,
        safe_task_summary: str,
        safe_output_summary: Optional[str] = None,
        tool_name: Optional[str] = None,
        error_details: Optional[str] = None,
        timestamp: Optional[float] = None,
        conversation_id: Optional[str] = None,
        **extra
    ) -> Dict[str, Any]:
        """
        Publishes a structured LangGraph node event to all live SSE subscribers and persists it.
        """
        if request_id and conversation_id:
            self._request_to_conv[request_id] = conversation_id
        elif request_id and not conversation_id:
            conversation_id = self._request_to_conv.get(request_id)
        now = timestamp if timestamp is not None else time.time()
        event = {
            "request_id": request_id,
            "execution_id": execution_id,
            "conversation_id": conversation_id,
            "node_id": node_id,
            "component_name": component_name,
            "component_type": component_type,
            "event_type": event_type,
            "execution_status": execution_status,
            "timestamp": now,
            "tool_name": tool_name,
            "safe_task_summary": safe_task_summary,
            "safe_output_summary": safe_output_summary,
            "error_details": error_details,
            **extra
        }

        # Cache in memory history for request_id and conversation_id
        for key in filter(None, [request_id, conversation_id]):
            if event_type == "REQUEST_STARTED" and key == conversation_id:
                self._history[key] = []
            if key not in self._history:
                self._history[key] = []
            self._history[key].append(event)

        # Notify active SSE subscriber queues
        delivered_queues = set()
        for key in filter(None, [request_id, conversation_id]):
            for q in self._subscribers.get(key, []):
                if q not in delivered_queues:
                    delivered_queues.add(q)
                    try:
                        q.put_nowait(event)
                    except Exception as e:
                        logger.warning(f"Failed to push to SSE queue: {e}")

        # Persist to database if Django models are accessible
        try:
            from research_system.models import NodeExecutionEvent, ResearchSession
            session = ResearchSession.objects.filter(request_id=request_id).first()
            conv_id = conversation_id or (session.conversation_id if session else None)
            NodeExecutionEvent.objects.create(
                session=session,
                conversation_id=conv_id,
                request_id=request_id,
                execution_id=execution_id,
                node_id=node_id,
                component_name=component_name,
                component_type=component_type,
                event_type=event_type,
                execution_status=execution_status,
                timestamp=now,
                tool_name=tool_name,
                safe_task_summary=safe_task_summary,
                safe_output_summary=safe_output_summary,
                error_details=error_details,
            )
        except Exception:
            pass

        return event

    def publish_text_chunk(
        self,
        request_id: str,
        execution_id: str,
        chunk: str,
        conversation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Publishes a streaming assistant text chunk for real-time typewriter rendering.
        """
        if request_id and conversation_id:
            self._request_to_conv[request_id] = conversation_id
        elif request_id and not conversation_id:
            conversation_id = self._request_to_conv.get(request_id)

        event = {
            "event_type": "text_chunk",
            "request_id": request_id,
            "execution_id": execution_id,
            "conversation_id": conversation_id,
            "chunk": chunk,
            "timestamp": time.time()
        }

        # Cache in memory history for request_id and conversation_id so late subscribers don't lose chunks
        for key in filter(None, [request_id, conversation_id]):
            if key not in self._history:
                self._history[key] = []
            self._history[key].append(event)
            if len(self._history[key]) > 600:
                self._history[key] = self._history[key][-600:]

        delivered_queues = set()
        for key in filter(None, [request_id, conversation_id]):
            for q in self._subscribers.get(key, []):
                if q not in delivered_queues:
                    delivered_queues.add(q)
                    try:
                        q.put_nowait(event)
                    except Exception as e:
                        logger.warning(f"Failed to push text chunk to SSE queue: {e}")

        return event

    def cancel_conversation(self, conversation_id: str):
        """
        Marks a conversation as cancelled, halting further external actions and writes.
        """
        self._cancelled_conversations.add(conversation_id)
        # Notify subscribers
        cancel_event = {
            "event_type": "response_cancelled",
            "conversation_id": conversation_id,
            "status": "cancelled",
            "timestamp": time.time()
        }
        for q in self._subscribers.get(conversation_id, []):
            try:
                q.put_nowait(cancel_event)
            except Exception:
                pass

    def is_cancelled(self, conversation_id: str) -> bool:
        """
        Returns True if the conversation execution was cancelled.
        """
        return conversation_id in self._cancelled_conversations

    def reset_cancellation(self, conversation_id: str):
        """
        Clears the cancellation flag for a conversation so new directives can execute cleanly.
        """
        self._cancelled_conversations.discard(conversation_id)

    def purge_conversation(self, conversation_id: str):
        """
        Permanently purges in-memory event queues and history for a deleted conversation.
        """
        self._cancelled_conversations.discard(conversation_id)
        if conversation_id in self._subscribers:
            del self._subscribers[conversation_id]
        if conversation_id in self._history:
            del self._history[conversation_id]
        # Clean up request_to_conv mappings for this conversation
        stale_requests = [req for req, conv in self._request_to_conv.items() if conv == conversation_id]
        for req in stale_requests:
            del self._request_to_conv[req]

    def subscribe(self, channel_key: str) -> queue.Queue:
        """
        Registers a new subscriber queue for the specified request_id or conversation_id.
        Replays existing events so newly connected SSE streams catch up.
        """
        q = queue.Queue(maxsize=2000)
        if channel_key not in self._subscribers:
            self._subscribers[channel_key] = []
        self._subscribers[channel_key].append(q)

        # Replay past events for this channel
        for past_event in self._history.get(channel_key, []):
            try:
                q.put_nowait(past_event)
            except queue.Full:
                pass

        return q

    def unsubscribe(self, channel_key: str, q: queue.Queue):
        """
        Unregisters an SSE subscriber queue.
        """
        if channel_key in self._subscribers:
            try:
                self._subscribers[channel_key].remove(q)
                if not self._subscribers[channel_key]:
                    del self._subscribers[channel_key]
            except ValueError:
                pass

    def get_events(self, channel_key: str) -> List[Dict[str, Any]]:
        return list(self._history.get(channel_key, []))


event_bus = EventBus()
