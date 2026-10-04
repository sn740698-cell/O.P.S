from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from ops_core.services.ollama_service import OPSOllamaService
from ops_core.services.automation_service import OPSAutomationService
from ops_core.services.scraping_service import OPSScrapingService
from ops_core.services.voice_service import WisprFlowVoiceService

ollama_service = OPSOllamaService()
automation_service = OPSAutomationService()
scraping_service = OPSScrapingService()
voice_service = WisprFlowVoiceService()

class HealthCheckView(APIView):
    def get(self, request):
        return Response({
            "status": "online",
            "system": "O.P.S. (Over-Engineered Programmed System)",
            "version": "0.1.0",
            "tri_models": {
                "router": {
                    "model": ollama_service.router_model,
                    "role": "Fast Router & Intent Detection (Qwen3 0.6B)"
                },
                "reasoning": {
                    "model": ollama_service.reasoning_model,
                    "role": "Main Reasoning, Planning, Code Gen & Debugging (Qwen3 1.7B)"
                },
                "conversation": {
                    "model": ollama_service.conversation_model,
                    "role": "Conversation, Content & Jarvis Persona (Llama 3.2 1B Instruct)"
                }
            },
            "voice_integration": voice_service.get_status()
        })

class IntentRouterView(APIView):
    def post(self, request):
        prompt = request.data.get("prompt", "")
        if not prompt:
            return Response({"error": "Prompt parameter is required."}, status=status.HTTP_400_BAD_REQUEST)
        result = ollama_service.route_request(prompt)
        return Response(result)

class PlanReasoningView(APIView):
    def post(self, request):
        prompt = request.data.get("prompt", "")
        context = request.data.get("context", None)
        if not prompt:
            return Response({"error": "Prompt parameter is required."}, status=status.HTTP_400_BAD_REQUEST)
        result = ollama_service.generate_reasoning_and_plan(prompt, context)
        return Response(result)

class CodeSynthesizerView(APIView):
    def post(self, request):
        task = request.data.get("task", "")
        tool_name = request.data.get("tool_name", "code_editor")
        if not task:
            return Response({"error": "Task parameter is required."}, status=status.HTTP_400_BAD_REQUEST)
        result = ollama_service.generate_code_or_debug(task, tool_name)
        return Response(result)

class OrchestrationView(APIView):
    def post(self, request):
        prompt = request.data.get("prompt", "")
        if not prompt:
            return Response({"error": "Prompt parameter is required."}, status=status.HTTP_400_BAD_REQUEST)
        result = ollama_service.orchestrate_pipeline(prompt)
        return Response(result)

class WebScraperView(APIView):
    def post(self, request):
        url = request.data.get("url", "")
        if not url:
            return Response({"error": "URL parameter is required."}, status=status.HTTP_400_BAD_REQUEST)
        result = scraping_service.scrape_url(url)
        return Response(result)

class AutomationDispatcherView(APIView):
    def post(self, request):
        action_type = request.data.get("type", "dom")  # 'dom' or 'gui'
        action = request.data.get("action", "")
        
        if action_type == "dom":
            selector = request.data.get("selector", "")
            url = request.data.get("url", "")
            res = automation_service.execute_dom_action(action, selector, url=url)
        else:
            x = request.data.get("x", 0)
            y = request.data.get("y", 0)
            text = request.data.get("text", "")
            res = automation_service.execute_gui_action(action, x, y, text)
            
        return Response(res)

class WisprVoiceStatusView(APIView):
    def get(self, request):
        return Response(voice_service.get_status())

class WisprVoiceToggleView(APIView):
    def post(self, request):
        res = voice_service.toggle_listening()
        return Response(res)

class WisprVoiceTranscriptView(APIView):
    def post(self, request):
        transcript = request.data.get("transcript", "")
        if not transcript:
            return Response({"error": "Transcript payload missing."}, status=status.HTTP_400_BAD_REQUEST)
        
        processed = voice_service.process_voice_transcript(transcript)
        # Option to automatically trigger pipeline execution upon receiving voice transcription:
        auto_dispatch = request.data.get("auto_dispatch", True)
        if auto_dispatch:
            pipeline_res = ollama_service.orchestrate_pipeline(transcript)
            processed["orchestration"] = pipeline_res
            
        return Response(processed)


# ==================== Security & Audit REST Views ====================

from ops_core.models import PermissionRequest, ExecutionAuditLog, SafetyPolicyRule
from ops_core.serializers import (
    PermissionRequestSerializer,
    ExecutionAuditLogSerializer,
    SafetyPolicyRuleSerializer
)


class ExecutionAuditLogListView(APIView):
    """List recent execution audit logs with optional filtering by agent, action, or task."""
    def get(self, request):
        task_id = request.query_params.get("task_id")
        agent_name = request.query_params.get("agent_name")
        limit = int(request.query_params.get("limit", 50))

        queryset = ExecutionAuditLog.objects.all()
        if task_id:
            queryset = queryset.filter(task_id=task_id)
        if agent_name:
            queryset = queryset.filter(agent_name=agent_name)

        serializer = ExecutionAuditLogSerializer(queryset[:limit], many=True)
        return Response({
            "count": queryset.count(),
            "logs": serializer.data
        })


class PermissionRequestListView(APIView):
    """List historical and pending permission requests."""
    def get(self, request):
        status_filter = request.query_params.get("status")
        queryset = PermissionRequest.objects.all()
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        serializer = PermissionRequestSerializer(queryset[:50], many=True)
        return Response({
            "count": queryset.count(),
            "requests": serializer.data
        })


class PermissionPendingListView(APIView):
    """List pending permission requests awaiting Human-In-The-Loop decision."""
    def get(self, request):
        pending = PermissionRequest.objects.filter(status="PENDING").order_by("-created_at")[:10]
        serializer = PermissionRequestSerializer(pending, many=True)
        return Response({
            "count": pending.count(),
            "pending": serializer.data
        })


class PermissionResolveView(APIView):
    """Resolves a pending permission request (ALLOW_ONCE, ALLOW_TASK, DENY) from Pop-Up Cockpit or Web."""
    def post(self, request):
        from ops_core.services.permission_manager import OPSPermissionManager
        request_id = request.data.get("request_id")
        decision = request.data.get("decision", "DENY")

        if not request_id:
            return Response({"error": "request_id parameter is required."}, status=status.HTTP_400_BAD_REQUEST)

        resolved_in_memory = OPSPermissionManager.resolve_permission(str(request_id), decision)

        status_val = "APPROVED" if "ALLOW" in decision.upper() else "DENIED"
        PermissionRequest.objects.filter(request_id=request_id).update(
            status=status_val,
            decision=decision,
            resolved_at=timezone.now()
        )

        return Response({
            "status": "success",
            "request_id": str(request_id),
            "decision": decision,
            "resolved_in_memory": resolved_in_memory
        })


class SafetyPolicyRuleListView(APIView):
    """List and manage active safety rules."""
    def get(self, request):
        rules = SafetyPolicyRule.objects.all()
        serializer = SafetyPolicyRuleSerializer(rules, many=True)
        return Response({"rules": serializer.data})

    def post(self, request):
        serializer = SafetyPolicyRuleSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ==================== Vector RAG & Memory REST Views ====================

from ops_core.services.rag_service import OPSRAGService
from ops_core.services.session_memory import OPSSessionMemoryManager

rag_service = OPSRAGService()
memory_manager = OPSSessionMemoryManager()


class RAGQueryView(APIView):
    """
    Semantic vector search across project codebase or memory collections.
    """
    def post(self, request):
        query = request.data.get("query", "")
        collection_name = request.data.get("collection", "ops_codebase")
        n_results = int(request.data.get("n_results", 4))

        if not query:
            return Response({"error": "Query parameter is required."}, status=status.HTTP_400_BAD_REQUEST)

        results = rag_service.query(query_text=query, collection_name=collection_name, n_results=n_results)
        return Response({
            "query": query,
            "collection": collection_name,
            "count": len(results),
            "results": results
        })


class RAGIndexDirectoryView(APIView):
    """
    Indexes a codebase directory into ChromaDB.
    """
    def post(self, request):
        directory = request.data.get("directory", "")
        collection_name = request.data.get("collection", "ops_codebase")

        if not directory:
            return Response({"error": "Directory parameter is required."}, status=status.HTTP_400_BAD_REQUEST)

        result = rag_service.index_directory(directory_path=directory, collection_name=collection_name)
        return Response(result)


class RAGStatsView(APIView):
    """
    Returns vector collection statistics and total document counts.
    """
    def get(self, request):
        stats = rag_service.get_stats()
        return Response(stats)


class SessionMemoryView(APIView):
    """
    Retrieves, records, or purges temporary conversation memory turns and isolated chatbot vector memory.
    """
    def get(self, request):
        session_id = request.query_params.get("session_id", "default_session")
        limit = request.query_params.get("limit")
        limit_int = int(limit) if limit else None
        history = memory_manager.get_recent_history(session_id=session_id, limit=limit_int)
        vector_stats = memory_manager.get_chatbot_vector_stats(session_id=session_id)
        return Response({
            "session_id": session_id,
            "turns_count": len(history),
            "history": history,
            "chatbot_vector_partition": vector_stats
        })

    def post(self, request):
        session_id = request.data.get("session_id", "default_session")
        role = request.data.get("role", "user")
        content = request.data.get("content", "")
        save_vector = request.data.get("save_to_vector_db", False)

        if not content:
            return Response({"error": "Content parameter is required."}, status=status.HTTP_400_BAD_REQUEST)

        memory_manager.add_turn(
            session_id=session_id,
            role=role,
            content=content,
            save_to_vector_db=save_vector
        )

        return Response({
            "status": "success",
            "session_id": session_id,
            "message": "Turn recorded successfully."
        })

    def delete(self, request):
        session_id = request.data.get("session_id") or request.query_params.get("session_id")
        if session_id:
            memory_manager.clear_session(session_id)
            msg = f"Temporary conversation memory & dedicated vector partition purged for session: {session_id}."
        else:
            memory_manager.clear_all_sessions()
            msg = "All temporary conversation memory and chatbot vector partitions purged."

        return Response({
            "status": "success",
            "session_id": session_id or "all",
            "message": msg
        })


class ChatbotVectorMemoryView(APIView):
    """
    Dedicated REST endpoint for the isolated 'ops_chatbot_memory' ChromaDB vector partition.
    Provides partition status, indexed turns, semantic search, and purge operations.
    """
    def get(self, request):
        session_id = request.query_params.get("session_id")
        stats = rag_service.get_stats()
        entries = rag_service.get_chatbot_memory_entries(session_id=session_id, limit=25)
        return Response({
            "status": "online",
            "partition_name": "ops_chatbot_memory",
            "partition_info": stats.get("dedicated_chatbot_partition", {}),
            "total_chatbot_vectors": stats.get("dedicated_chatbot_partition", {}).get("count", 0),
            "entries_count": len(entries),
            "entries": entries
        })

    def post(self, request):
        # Semantic search or indexing into dedicated chatbot memory partition
        action = request.data.get("action", "query")
        session_id = request.data.get("session_id")

        if action == "query":
            query = request.data.get("query", "")
            if not query:
                return Response({"error": "Query parameter is required."}, status=status.HTTP_400_BAD_REQUEST)
            results = rag_service.query_chatbot_memory(
                query_text=query,
                session_id=session_id,
                n_results=int(request.data.get("n_results", 4))
            )
            return Response({
                "partition": "ops_chatbot_memory",
                "query": query,
                "count": len(results),
                "results": results
            })
        elif action == "index":
            text = request.data.get("text", "")
            role = request.data.get("role", "user")
            sid = session_id or "default_session"
            if not text:
                return Response({"error": "Text parameter is required."}, status=status.HTTP_400_BAD_REQUEST)
            mem_id = rag_service.index_chatbot_turn(text=text, session_id=sid, role=role)
            return Response({
                "status": "success",
                "partition": "ops_chatbot_memory",
                "vector_id": mem_id
            })
        return Response({"error": f"Unknown action: {action}"}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        session_id = request.data.get("session_id") or request.query_params.get("session_id")
        purged_count = rag_service.clear_chatbot_memory(session_id=session_id)
        return Response({
            "status": "success",
            "partition": "ops_chatbot_memory",
            "purged_vectors": purged_count,
            "message": f"Purged {purged_count} vectors from ops_chatbot_memory."
        })


# ==================== LangGraph Multi-Agent REST View ====================

from ops_core.services.agent_orchestrator import OPSMultiAgentOrchestrator
from asgiref.sync import async_to_sync

agent_orchestrator = OPSMultiAgentOrchestrator()


class AgentRunWorkflowView(APIView):
    """
    Executes the full LangGraph multi-agent orchestration pipeline with session memory.
    """
    def post(self, request):
        prompt = request.data.get("prompt", "")
        task_id = request.data.get("task_id")
        session_id = request.data.get("session_id")
        source = request.data.get("source", "workstation")

        if not prompt:
            return Response({"error": "Prompt parameter is required."}, status=status.HTTP_400_BAD_REQUEST)

        # Execute async LangGraph workflow synchronously for REST client
        result = async_to_sync(agent_orchestrator.run_task_async)(prompt, task_id=task_id, session_id=session_id, source=source)
        return Response(result)


# ==================== 7-Tier Intelligence Escalation REST View ====================

from ops_core.services.escalation_engine import OPSEscalationEngine

escalation_engine = OPSEscalationEngine()


class IntelligenceEscalationView(APIView):
    """
    Executes the 7-Tier Cognitive Escalation Pipeline.
    """
    def post(self, request):
        prompt = request.data.get("prompt", "")
        session_id = request.data.get("session_id")
        force_tier = request.data.get("force_tier")

        if not prompt:
            return Response({"error": "Prompt parameter is required."}, status=status.HTTP_400_BAD_REQUEST)

        result = async_to_sync(escalation_engine.process_with_escalation)(
            prompt=prompt,
            session_id=session_id,
            force_tier=force_tier
        )
        return Response(result)


# ==================== Multimodal Vision & Voice REST Views ====================

from ops_core.services.vision_service import OPSVisionService

vision_service = OPSVisionService()


class VisionScreenshotView(APIView):
    """Captures desktop screen and returns base64 PNG image."""
    def get(self, request):
        res = vision_service.capture_screenshot()
        return Response(res)


class VisionAnalyzeView(APIView):
    """Analyzes screenshot image with natural language query."""
    def post(self, request):
        prompt = request.data.get("prompt", "Analyze what is on the screen")
        image_base64 = request.data.get("image_base64")
        res = vision_service.analyze_screen(prompt=prompt, image_base64=image_base64)
        return Response(res)


class VoiceSynthesizeView(APIView):
    """Converts text into neural spoken audio stream (Piper TTS)."""
    def post(self, request):
        text = request.data.get("text", "")
        voice_model = request.data.get("voice_model", "en_US-lessac-medium")
        if not text:
            return Response({"error": "Text parameter is required."}, status=status.HTTP_400_BAD_REQUEST)

        res = voice_service.synthesize_speech(text=text, voice_model=voice_model)
        return Response(res)


class VoiceTranscribeView(APIView):
    """Transcribes audio payload to text."""
    def post(self, request):
        audio_b64 = request.data.get("audio_base64", "")
        if not audio_b64:
            return Response({"error": "audio_base64 parameter is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            audio_bytes = base64.b64decode(audio_b64)
            res = voice_service.transcribe_audio_bytes(audio_bytes)
            return Response(res)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


# ==================== Mobile Companion Views (Iteration 7) ====================

from ops_core.services.mobile_service import OPSMobileService
from asgiref.sync import async_to_sync


class MobilePairingGenerateView(APIView):
    """Generates a 6-digit numeric PIN session and QR pairing payload."""
    def post(self, request):
        expires_in = int(request.data.get("expires_in_minutes", 10))
        host = request.get_host().split(":")[0]
        port = request.get_port()
        res = OPSMobileService.generate_pairing_session(
            expires_in_minutes=expires_in,
            host=host or "127.0.0.1",
            port=int(port) if port else 8000
        )
        return Response(res)


class MobilePairingVerifyView(APIView):
    """Verifies pairing PIN code and returns permanent device auth token."""
    def post(self, request):
        pin_code = request.data.get("pin_code", "")
        device_id = request.data.get("device_id", "")
        device_name = request.data.get("device_name", "Mobile Companion")
        device_type = request.data.get("device_type", "android")
        ip_address = request.META.get("REMOTE_ADDR", "")

        if not pin_code or not device_id:
            return Response(
                {"error": "pin_code and device_id are required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        res = OPSMobileService.verify_and_pair_device(
            pin_code=pin_code,
            device_id=device_id,
            device_name=device_name,
            device_type=device_type,
            ip_address=ip_address
        )
        if not res.get("success"):
            return Response(res, status=status.HTTP_401_UNAUTHORIZED)
        return Response(res)


class MobileDeviceListView(APIView):
    """Lists registered mobile devices or revokes device access."""
    def get(self, request):
        devices = OPSMobileService.list_devices()
        return Response({"count": len(devices), "devices": devices})

    def delete(self, request, device_id=None):
        target_id = device_id or request.data.get("device_id")
        if not target_id:
            return Response({"error": "device_id required."}, status=status.HTTP_400_BAD_REQUEST)
        revoked = OPSMobileService.revoke_device(target_id)
        return Response({"success": revoked, "device_id": target_id})


class MobilePermissionResolveView(APIView):
    """Allows authenticated mobile companion to resolve interactive security permissions."""
    def post(self, request):
        auth_header = request.headers.get("Authorization", "") or request.data.get("auth_token", "")
        request_id = request.data.get("request_id")
        decision = request.data.get("decision", "DENY")

        if not request_id:
            return Response({"error": "request_id is required."}, status=status.HTTP_400_BAD_REQUEST)

        res = OPSMobileService.resolve_remote_permission(
            auth_token=auth_header,
            request_id=request_id,
            decision=decision
        )
        if not res.get("success") and "Unauthorized" in res.get("error", ""):
            return Response(res, status=status.HTTP_401_UNAUTHORIZED)
        return Response(res)


class MobileEmergencyHaltView(APIView):
    """Allows mobile companion to trigger immediate system kill switch."""
    def post(self, request):
        auth_header = request.headers.get("Authorization", "") or request.data.get("auth_token", "")
        reason = request.data.get("reason", "Emergency Halt via Mobile Companion")

        res = OPSMobileService.trigger_emergency_halt(
            auth_token=auth_header,
            reason=reason
        )
        if not res.get("success") and "Unauthorized" in res.get("error", ""):
            return Response(res, status=status.HTTP_401_UNAUTHORIZED)
        return Response(res)


class MobileRemoteDispatchView(APIView):
    """Allows mobile companion to remotely dispatch instructions to O.P.S."""
    def post(self, request):
        auth_header = request.headers.get("Authorization", "") or request.data.get("auth_token", "")
        prompt = request.data.get("prompt", "")
        task_id = request.data.get("task_id")

        if not prompt:
            return Response({"error": "prompt parameter is required."}, status=status.HTTP_400_BAD_REQUEST)

        res = async_to_sync(OPSMobileService.dispatch_remote_task_async)(
            auth_token=auth_header,
            prompt=prompt,
            task_id=task_id
        )
        if not res.get("success") and "Unauthorized" in res.get("error", ""):
            return Response(res, status=status.HTTP_401_UNAUTHORIZED)
        return Response(res)


class MobileCameraStreamView(APIView):
    """Accepts mobile camera frames and runs visual analysis."""
    def post(self, request):
        auth_header = request.headers.get("Authorization", "") or request.data.get("auth_token", "")
        image_base64 = request.data.get("image_base64", "")
        prompt = request.data.get("prompt")

        if not image_base64:
            return Response({"error": "image_base64 is required."}, status=status.HTTP_400_BAD_REQUEST)

        res = OPSMobileService.process_camera_frame(
            auth_token=auth_header,
            image_base64=image_base64,
            prompt=prompt
        )
        if not res.get("success") and "Unauthorized" in res.get("error", ""):
            return Response(res, status=status.HTTP_401_UNAUTHORIZED)
        return Response(res)


# ==================== User Workstation Memories (PostgreSQL) REST Views ====================

from ops_core.services.workstation_memory_service import OPSWorkstationMemoryService

workstation_memory_service = OPSWorkstationMemoryService()


class UserWorkstationMemoryListView(APIView):
    """
    Lists all persistent workstation memories from PostgreSQL or captures a new memory.
    """
    def get(self, request):
        category = request.query_params.get("category")
        memories = workstation_memory_service.list_all_memories(category=category)
        return Response({
            "status": "success",
            "count": len(memories),
            "database": "PostgreSQL 18 (ops_db)",
            "memories": memories
        })

    def post(self, request):
        label = request.data.get("label", "")
        category = request.data.get("category", "general")
        window_title = request.data.get("window_title", "")
        target_url = request.data.get("target_url", "")
        app_name = request.data.get("app_name", "")
        action_type = request.data.get("action_type", "open_url")
        content_snippet = request.data.get("content_snippet", "")
        metadata = request.data.get("metadata", {})

        if not label and not target_url and not window_title:
            return Response(
                {"error": "At least label, target_url, or window_title is required to store memory."},
                status=status.HTTP_400_BAD_REQUEST
            )

        res = workstation_memory_service.capture_memory(
            label=label or window_title or "Saved Memory",
            category=category,
            window_title=window_title,
            target_url=target_url,
            app_name=app_name,
            action_type=action_type,
            content_snippet=content_snippet,
            metadata=metadata
        )
        return Response(res, status=status.HTTP_201_CREATED)


class UserWorkstationMemoryDetailView(APIView):
    """
    Deletes a specific workstation memory from PostgreSQL.
    """
    def delete(self, request, memory_id):
        deleted = workstation_memory_service.delete_memory(memory_id)
        if deleted:
            return Response({"status": "success", "message": f"Memory {memory_id} deleted from PostgreSQL."})
        return Response({"status": "error", "message": "Memory not found."}, status=status.HTTP_404_NOT_FOUND)


class UserWorkstationMemoryExecuteView(APIView):
    """
    Recalls a workstation memory from PostgreSQL and automatically executes the action
    (opens window and plays the song, navigates to reel, opens search, etc.).
    """
    def post(self, request):
        query = request.data.get("query", "")
        memory_id = request.data.get("memory_id", "")

        if not query and not memory_id:
            return Response({"error": "query or memory_id required."}, status=status.HTTP_400_BAD_REQUEST)

        res = workstation_memory_service.recall_and_execute(query or memory_id)
        return Response(res)






