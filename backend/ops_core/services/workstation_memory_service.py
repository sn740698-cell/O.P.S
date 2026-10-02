"""
O.P.S. Personal Workstation Memory Service (PostgreSQL)
Manages user workstation memories:
- Captures active window context (YouTube songs, Instagram reels, Google searches, apps, documents)
- Stores user-labeled favorites ("my favorite song", "AI research video", "my workout reel")
- Recalls and executes memories: automatically opens the window and plays the song/video/search on command
- Backed by persistent PostgreSQL database
"""

import os
import re
import uuid
import logging
import webbrowser
from typing import Dict, Any, List, Optional
from django.utils import timezone
from ops_core.models import UserWorkstationMemory
from ops_core.services.event_bus import OPSEventBus

logger = logging.getLogger("ops.workstation_memory")


class OPSWorkstationMemoryService:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(OPSWorkstationMemoryService, cls).__new__(cls)
        return cls._instance

    def capture_memory(
        self,
        label: str,
        category: str = "general",
        window_title: str = "",
        target_url: str = "",
        app_name: str = "",
        action_type: str = "open_url",
        content_snippet: str = "",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Creates and commits a new user memory to PostgreSQL.
        """
        clean_label = label.strip(' ".\'')
        if not clean_label:
            clean_label = "Saved Workstation Memory"

        # Check active workstation context if target_url or window_title is empty
        if not target_url or not window_title:
            try:
                from ops_core.services.automation_service import OPSAutomationService
                auto_svc = OPSAutomationService()
                if not target_url and auto_svc.last_active_url:
                    target_url = auto_svc.last_active_url
                if not window_title and auto_svc.last_active_title:
                    window_title = auto_svc.last_active_title
                if not app_name and auto_svc.last_active_app:
                    app_name = auto_svc.last_active_app
            except Exception as ex:
                logger.debug(f"Could not fetch automation service context: {ex}")

        # Auto-categorize and provide fallback URL if still empty
        url_lower = (target_url or "").lower()
        title_lower = (window_title or "").lower()
        label_lower = clean_label.lower()

        import urllib.parse

        if "youtube.com" in url_lower or "youtu.be" in url_lower or "song" in label_lower or "music" in label_lower:
            category = "media"
            action_type = "play_media"
            if not target_url:
                target_url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(clean_label)}"
            if not window_title:
                window_title = f"YouTube: {clean_label}"
        elif "instagram.com" in url_lower or "reel" in label_lower or "insta" in label_lower:
            category = "social"
            action_type = "open_url"
            if not target_url:
                target_url = "https://www.instagram.com/reels/"
            if not window_title:
                window_title = f"Instagram: {clean_label}"
        elif "google.com/search" in url_lower or "search" in label_lower:
            category = "search"
            action_type = "open_url"
            if not target_url:
                target_url = f"https://www.google.com/search?q={urllib.parse.quote(clean_label)}"
            if not window_title:
                window_title = f"Google: {clean_label}"
        elif app_name and not target_url:
            category = "app"
            action_type = "launch_app"
            if not window_title:
                window_title = f"App: {app_name}"

        mem = UserWorkstationMemory.objects.create(
            label=clean_label,
            category=category,
            window_title=window_title,
            target_url=target_url,
            app_name=app_name,
            action_type=action_type,
            content_snippet=content_snippet,
            metadata=metadata or {}
        )

        log_msg = f"[POSTGRES-MEM] Stored memory: '{clean_label}' [{category.upper()}] -> {target_url or window_title}"
        OPSEventBus.emit_terminal_log(log_msg, stream="stdout")
        logger.info(log_msg)

        result_payload = {
            "status": "success",
            "memory_id": str(mem.memory_id),
            "label": mem.label,
            "category": mem.category,
            "window_title": mem.window_title,
            "target_url": mem.target_url,
            "app_name": mem.app_name,
            "action_type": mem.action_type,
            "created_at": mem.created_at.isoformat()
        }

        # 1. Broadcast memory_added event to React HUD & WebSocket clients
        try:
            OPSEventBus.emit_memory_added(result_payload)
        except Exception as ee:
            logger.debug(f"Event bus memory broadcast failed: {ee}")

        # 2. Play 90s retro sci-fi sound directly on workstation speakers via winsound (Windows)
        def _play_retro_audio():
            try:
                import winsound
                sound_file = os.path.abspath(
                    os.path.join(os.path.dirname(__file__), "..", "..", "..", "local_agent", "sounds", "memory_added.wav")
                )
                if os.path.exists(sound_file):
                    winsound.PlaySound(sound_file, winsound.SND_FILENAME | winsound.SND_ASYNC)
                else:
                    winsound.Beep(880, 80)
                    winsound.Beep(1760, 120)
            except Exception:
                pass

        import threading
        threading.Thread(target=_play_retro_audio, daemon=True).start()

        return result_payload

    def list_all_memories(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """Returns all user memories from PostgreSQL."""
        qs = UserWorkstationMemory.objects.all()
        if category:
            qs = qs.filter(category=category)
        
        memories = []
        for m in qs:
            memories.append({
                "memory_id": str(m.memory_id),
                "label": m.label,
                "category": m.category,
                "window_title": m.window_title,
                "target_url": m.target_url,
                "app_name": m.app_name,
                "action_type": m.action_type,
                "content_snippet": m.content_snippet,
                "created_at": m.created_at.strftime("%Y-%m-%d %H:%M:%S")
            })
        return memories

    def delete_memory(self, memory_id: str) -> bool:
        """Deletes a memory from PostgreSQL."""
        try:
            deleted_count, _ = UserWorkstationMemory.objects.filter(memory_id=memory_id).delete()
            if deleted_count > 0:
                OPSEventBus.emit_terminal_log(f"[POSTGRES-MEM] Deleted memory ID: {memory_id}", stream="stdout")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to delete memory {memory_id}: {e}")
            return False

    def recall_and_execute(self, query: str) -> Dict[str, Any]:
        """
        Recalls a memory from PostgreSQL matching the user's directive (e.g. "my favorite song" or UUID)
        and automatically opens the window / plays the media.
        """
        mem = None
        # 1. Check if query is a direct UUID (memory_id)
        try:
            val = str(query).strip()
            mem = UserWorkstationMemory.objects.filter(memory_id=uuid.UUID(val)).first()
        except Exception:
            mem = None

        if not mem:
            clean_query = query.lower()
            for prefix in [
                "play ", "open ", "add ", "recall ", "go to ", "launch ",
                "from the memory", "from my memory", "from memory", "my memory",
                "please", "now"
            ]:
                clean_query = clean_query.replace(prefix, "")
            clean_query = clean_query.strip(" '\"?.")

            # Search in PostgreSQL by label
            qs = UserWorkstationMemory.objects.filter(label__icontains=clean_query)
            if qs.exists():
                mem = qs.first()
            else:
                # Word-level search
                words = [w for w in clean_query.split() if len(w) > 2]
                for w in words:
                    match = UserWorkstationMemory.objects.filter(label__icontains=w).first()
                    if match:
                        mem = match
                        break

        if not mem:
            return {
                "status": "not_found",
                "message": f"No memory found matching '{query}' in PostgreSQL memory vault."
            }

        # 2. Execute Action: Play / Open Window
        target = mem.target_url or mem.window_title or mem.app_name
        exec_details = ""

        try:
            if mem.action_type == "play_media" or "youtube" in (mem.target_url or "").lower() or "song" in mem.label.lower():
                url = mem.target_url
                if not url:
                    # Construct YouTube search & play URL
                    search_term = mem.window_title or mem.label
                    url = f"https://www.youtube.com/results?search_query={search_term.replace(' ', '+')}"
                webbrowser.open(url)
                exec_details = f"Navigated to media window: {url} and initiated automatic playback."
            elif mem.target_url:
                webbrowser.open(mem.target_url)
                exec_details = f"Opened target window URL: {mem.target_url}"
            elif mem.app_name:
                os.system(f"start {mem.app_name}")
                exec_details = f"Launched application: {mem.app_name}"
            else:
                exec_details = f"Recalled memory context: {mem.content_snippet or mem.label}"

            log_msg = f"[POSTGRES-MEM] Recalled & Executed memory '{mem.label}' -> {exec_details}"
            OPSEventBus.emit_terminal_log(log_msg, stream="stdout")
            logger.info(log_msg)

            return {
                "status": "executed",
                "memory_id": str(mem.memory_id),
                "label": mem.label,
                "category": mem.category,
                "target": target,
                "execution_details": exec_details
            }
        except Exception as e:
            logger.error(f"Failed to execute memory '{mem.label}': {e}")
            return {
                "status": "error",
                "memory_id": str(mem.memory_id),
                "label": mem.label,
                "error": str(e)
            }
