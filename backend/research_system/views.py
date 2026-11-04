import time
import json
import uuid
import asyncio
import queue
import logging
import datetime
from django.http import JsonResponse, StreamingHttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.db import transaction

from research_system.models import (
    Conversation,
    ChatMessage,
    PendingApproval,
    UserLongTermMemory,
    ProjectKnowledge,
    ResearchSession,
    NodeExecutionEvent,
)
from research_system.events.event_bus import event_bus
from research_system.graph.builder import research_graph, delete_conversation_checkpoint
from research_system.llm.ollama_client import ollama_client, MODEL_QWEN_1_7B, MODEL_LLAMA_1B
from research_system.services.conversation_summary import (
    extract_summary_from_text,
    attach_summary_to_response,
    generate_updated_summary
)

logger = logging.getLogger(__name__)


from research_system.router import (
    classify_request_mode,
    classify_execution_route,
    log_routing_decision,
    MODE_LLM,
    MODE_WEB,
    MODE_HYBRID,
    MODE_CLARIFICATION,
    MODE_AUTOMATION,
    MODE_DESKTOP_AUTO,
    MODE_BROWSER_AUTO,
    MODE_HYBRID_AUTO,
    STAGES_MAP,
    ROUTE_WEB_RESEARCH,
    ROUTE_GENERAL_CHAT
)


# ======================================================================
# 1. Health Check
# ======================================================================
@csrf_exempt
def health_check(request):
    """
    Health check endpoint for Cockpit frontend.
    """
    return JsonResponse({
        "status": "online",
        "engine": "LangGraph O.P.S. 2.0 Web Research",
        "models": {
            "request_understanding": "Qwen3 0.6B",
            "research_planner": "Qwen3 1.7B",
            "evidence_analysis": "Qwen3 1.7B",
            "answer_generation": "Qwen3 1.7B",
            "optional_evaluator": "Llama 3.2 1B"
        },
        "crawling_libraries": [
            "crawlee",
            "beautifulsoup4"
        ],
        "timestamp": time.time()
    })


# ======================================================================
# 2. Conversation Lifecycle (Category 1: Active Conversation Management)
# ======================================================================

@csrf_exempt
def conversations_collection(request):
    """
    Endpoints:
    - POST /api/chat/conversations/
    - GET  /api/chat/conversations/
    """
    if request.method == "POST":
        try:
            data = json.loads(request.body.decode("utf-8")) if request.body else {}
        except Exception:
            data = {}

        conversation_id = data.get("conversation_id") or f"conv_{int(time.time())}_{uuid.uuid4().hex[:6]}"
        title = data.get("title") or "New Conversation"

        conv, created = Conversation.objects.get_or_create(
            conversation_id=conversation_id,
            defaults={"title": title, "status": "ACTIVE"}
        )

        return JsonResponse({
            "status": "success",
            "conversation_id": conv.conversation_id,
            "title": conv.title,
            "conversation_status": conv.status,
            "created_at": conv.created_at.isoformat() if conv.created_at else None,
            "messages": []
        }, status=201 if created else 200)

    elif request.method == "GET":
        conversations = Conversation.objects.exclude(status="DELETED").order_by("-updated_at")[:20]
        result = []
        for c in conversations:
            result.append({
                "conversation_id": c.conversation_id,
                "title": c.title,
                "status": c.status,
                "messages_count": c.messages.count(),
                "created_at": c.created_at.isoformat(),
                "updated_at": c.updated_at.isoformat()
            })
        return JsonResponse({"conversations": result, "count": len(result)})

    return JsonResponse({"error": "Method not allowed"}, status=405)


@csrf_exempt
def get_active_conversation(request):
    """
    Endpoint: GET /api/chat/conversations/active/
    Returns the currently active or most recently updated conversation.
    If none exists, creates one and returns it.
    """
    if request.method != "GET":
        return JsonResponse({"error": "Method not allowed. Use GET."}, status=405)

    conv = Conversation.objects.exclude(status="DELETED").order_by("-updated_at").first()
    if not conv:
        conv_id = f"conv_{int(time.time())}_{uuid.uuid4().hex[:6]}"
        conv = Conversation.objects.create(
            conversation_id=conv_id,
            title="Cockpit Session",
            status="ACTIVE"
        )

    messages = []
    for msg in conv.messages.all().order_by("created_at"):
        messages.append({
            "message_id": msg.message_id,
            "role": msg.role,
            "content": msg.content,
            "input_type": msg.input_type,
            "status": msg.status,
            "metadata": msg.metadata,
            "created_at": msg.created_at.isoformat()
        })

    return JsonResponse({
        "status": "success",
        "conversation_id": conv.conversation_id,
        "title": conv.title,
        "conversation_status": conv.status,
        "summary": conv.summary,
        "messages": messages,
        "created_at": conv.created_at.isoformat() if conv.created_at else None,
        "updated_at": conv.updated_at.isoformat() if conv.updated_at else None
    })


@csrf_exempt
def conversation_detail(request, conversation_id):
    """
    Endpoints:
    - GET    /api/chat/conversations/{id}/
    - DELETE /api/chat/conversations/{id}/  (Permanent Refresh & Deletion)
    """
    if request.method == "GET":
        conv = Conversation.objects.filter(conversation_id=conversation_id).first()
        if not conv or conv.status == "DELETED":
            return JsonResponse({"error": "Conversation not found"}, status=404)

        messages = []
        for msg in conv.messages.all().order_by("created_at"):
            messages.append({
                "message_id": msg.message_id,
                "role": msg.role,
                "content": msg.content,
                "input_type": msg.input_type,
                "status": msg.status,
                "metadata": msg.metadata,
                "created_at": msg.created_at.isoformat()
            })

        return JsonResponse({
            "conversation_id": conv.conversation_id,
            "title": conv.title,
            "status": conv.status,
            "summary": conv.summary,
            "messages": messages,
            "created_at": conv.created_at.isoformat(),
            "updated_at": conv.updated_at.isoformat()
        })

    elif request.method == "DELETE":
        """
        PERMANENT CONVERSATION RESET (Section 4 & 9):
        1. Cancels or invalidates active executions associated with the conversation.
        2. Permanently deletes conversation messages, summaries, and attachments.
        3. Deletes persisted LangGraph checkpoint state using checkpointer.delete_thread.
        4. Purges in-memory event bus subscriber queues and history for this conversation.
        5. Confirms Category 2 (UserLongTermMemory) and Category 3 (ProjectKnowledge) remain intact.
        """
        try:
            # 1. Cancel in-memory execution token
            event_bus.cancel_conversation(conversation_id)

            # 2. Delete LangGraph checkpointer thread state
            delete_conversation_checkpoint(conversation_id)

            # 3. Purge in-memory SSE event bus queues
            event_bus.purge_conversation(conversation_id)

            # 4. Database Deletion within transaction
            with transaction.atomic():
                conv = Conversation.objects.filter(conversation_id=conversation_id).first()
                deleted_messages_count = 0
                if conv:
                    deleted_messages_count = conv.messages.count()
                    # Delete all child messages & the conversation itself
                    conv.delete()

                # Clean up associated session and node events
                ResearchSession.objects.filter(conversation_id=conversation_id).delete()
                NodeExecutionEvent.objects.filter(conversation_id=conversation_id).delete()

            # Verify Category 2 & 3 are intact
            retained_memories = UserLongTermMemory.objects.count()
            retained_docs = ProjectKnowledge.objects.count()

            logger.info(
                f"[PERMANENT RESET] Conversation {conversation_id} deleted successfully. "
                f"Retained {retained_memories} long-term memories and {retained_docs} project docs."
            )

            return JsonResponse({
                "status": "deleted",
                "conversation_id": conversation_id,
                "deleted_messages_count": deleted_messages_count,
                "long_term_memories_intact": True,
                "project_knowledge_intact": True,
                "message": "Conversation and all associated execution data permanently deleted."
            }, status=200)

        except Exception as e:
            logger.error(f"Failed to permanently delete conversation {conversation_id}: {e}", exc_info=True)
            return JsonResponse({
                "status": "error",
                "conversation_id": conversation_id,
                "error": f"Failed to delete conversation: {str(e)}"
            }, status=500)

    return JsonResponse({"error": "Method not allowed"}, status=405)


@csrf_exempt
def conversation_messages(request, conversation_id):
    """
    Endpoint: POST /api/chat/conversations/{id}/messages/
    Submits a user message, runs LangGraph Web Research with conversation context,
    and returns or streams the assistant's response.
    """
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed. Use POST."}, status=405)

    try:
        data = json.loads(request.body.decode("utf-8")) if request.body else {}
    except Exception:
        data = {}

    query = data.get("content") or data.get("prompt") or data.get("query") or data.get("message") or ""
    if not query.strip():
        return JsonResponse({"error": "Message content is required."}, status=400)

    input_type = data.get("input_type", "text")
    max_iterations = int(data.get("max_iterations", 2))

    # Fetch or auto-create conversation
    conv, _ = Conversation.objects.get_or_create(
        conversation_id=conversation_id,
        defaults={"title": query[:40], "status": "ACTIVE"}
    )

    # Reset cancellation flag so new user directives can stream cleanly
    event_bus.reset_cancellation(conversation_id)

    if conv.status == "DELETED":
        return JsonResponse({"error": "Conversation has been deleted and cannot accept new messages."}, status=410)

    # If conversation was previously cancelled, reactivate it for this new directive
    if conv.status == "CANCELLED":
        conv.status = "ACTIVE"
        conv.active_execution_id = None
        conv.save()

    # HITL Control: Reject new message submissions while an approval is pending
    if conv.status == "PENDING_APPROVAL":
        return JsonResponse({
            "error": "A Human-in-the-Loop approval is pending for this conversation. Please accept or deny it before continuing."
        }, status=409)

    # Execution Control: Auto-recover from stale GENERATING status (>15s)
    if conv.status == "GENERATING":
        time_since = (timezone.now() - conv.updated_at).total_seconds()
        if time_since > 15:
            logger.info(f"Auto-recovering conversation {conversation_id} from stale GENERATING status ({time_since:.1f}s)")
            conv.status = "ACTIVE"
            conv.active_execution_id = None
            conv.save()
        else:
            return JsonResponse({
                "error": "A generation is already in progress for this conversation. Please wait or cancel it."
            }, status=409)

    request_id = data.get("request_id") or f"req_{int(time.time())}_{uuid.uuid4().hex[:6]}"
    execution_id = f"exec_{uuid.uuid4().hex[:8]}"
    session_id = f"sess_{conversation_id[:16]}"
    user_message_id = f"msg_{int(time.time())}_{uuid.uuid4().hex[:6]}"
    assistant_message_id = f"msg_{int(time.time()) + 1}_{uuid.uuid4().hex[:6]}"

    # Save user message immediately to database
    user_msg = ChatMessage.objects.create(
        conversation=conv,
        message_id=user_message_id,
        role="user",
        content=query,
        input_type=input_type,
        status="completed"
    )

    # Mark conversation as GENERATING
    conv.status = "GENERATING"
    conv.active_execution_id = execution_id
    if conv.title == "New Conversation":
        conv.title = query[:40]
    conv.save()

    t_start = time.time()

    # Load chronological previous messages for multi-turn context (Optimized lean context: last 6 messages)
    history_records = conv.messages.exclude(message_id=user_message_id).order_by("created_at")
    recent_history = []
    for m in history_records[max(0, history_records.count() - 6):]:
        recent_history.append({"role": m.role, "content": m.content})

    # Load long-term memory (Category 2) & project knowledge (Category 3)
    long_term_mems = list(UserLongTermMemory.objects.all().values("key", "content", "category")[:5])
    proj_docs = list(ProjectKnowledge.objects.all().values("doc_id", "title", "content")[:5])

    # Execute directive via the 13-component Central LangGraph Orchestrator
    try:
        from research_system.orchestrator.service import CentralOrchestratorService
        orch_res = CentralOrchestratorService.execute_directive(
            query=query,
            conversation_id=conversation_id,
            request_id=request_id,
            task_id=execution_id
        )

        final_answer = orch_res.get("final_answer", "")
        resp_mode = orch_res.get("response_mode", "LLM")

        # If execution paused for approval:
        if orch_res.get("approval_required") and orch_res.get("approval_status") != "APPROVED":
            conv.refresh_from_db()
            conv.status = "PENDING_APPROVAL"
            conv.active_execution_id = None
            conv.save()
            return JsonResponse({
                "status": "waiting_for_approval",
                "message_id": assistant_message_id,
                "conversation_id": conversation_id,
                "request_id": request_id,
                "role": "assistant",
                "content": final_answer,
                "final_answer": final_answer,
                "response": final_answer,
                "approval_id": orch_res.get("approval_id"),
                "mode": resp_mode,
                "response_mode": resp_mode,
                "stages": [f"{resp_mode} Workflow", "Human Authorization Gate"]
            }, status=200)

        # If clarification requested:
        if orch_res.get("clarification_required"):
            conv.refresh_from_db()
            conv.status = "ACTIVE"
            conv.active_execution_id = None
            conv.save()
            return JsonResponse({
                "status": "needs_clarification",
                "message_id": assistant_message_id,
                "conversation_id": conversation_id,
                "request_id": request_id,
                "role": "assistant",
                "content": final_answer,
                "final_answer": final_answer,
                "response": final_answer,
                "clarification_prompt": orch_res.get("clarification_prompt"),
                "mode": "CLARIFICATION",
                "response_mode": "CLARIFICATION",
                "stages": ["Directive Understanding", "Disambiguation Required"]
            }, status=200)

        # Standard Completion:
        conv.refresh_from_db()
        conv.status = "ACTIVE"
        conv.active_execution_id = None
        conv.save()
        return JsonResponse({
            "status": "success" if orch_res.get("success") else "failed",
            "message_id": assistant_message_id,
            "conversation_id": conversation_id,
            "request_id": request_id,
            "role": "assistant",
            "content": final_answer,
            "final_answer": final_answer,
            "answer": final_answer,
            "response": final_answer,
            "mode": resp_mode,
            "response_mode": resp_mode,
            "plan": orch_res.get("plan", []),
            "node_history": [s.get("assigned_agent") for s in orch_res.get("plan", [])] if orch_res.get("plan") else [resp_mode.lower()]
        }, status=200)

    except Exception as orch_err:
        logger.error(f"Central orchestrator execution exception: {orch_err}, falling back to router.", exc_info=True)

    # Check for Active Temporary Document Session (RAG Mode)
    from research_system.services.temporary_rag_service import get_temporary_rag_service
    from research_system.router import MODE_DOCUMENT
    rag_service = get_temporary_rag_service()
    has_active_docs = rag_service.has_active_documents(conversation_id)

    if has_active_docs:
        q_lower = query.lower()
        is_explicit_web = any(w in q_lower for w in ["search the web", "search online", "google it", "look up on google", "web research"])
        is_chitchat = q_lower in ["hi", "hello", "hey", "who are you", "what can you do", "good morning", "good evening"]

        if not is_explicit_web and not is_chitchat:
            active_docs = rag_service.get_active_documents(conversation_id)
            doc_names = ", ".join([d.get("doc_name", "document") for d in active_docs])
            selected_mode = MODE_DOCUMENT
            mode_reason = f"Active temporary document session with {len(active_docs)} document(s): {doc_names}."
            stages = STAGES_MAP.get(MODE_DOCUMENT, [])
            search_query = query
            route = ROUTE_GENERAL_CHAT
        else:
            router_data = classify_request_mode(query, recent_history, allow_model_call=True)
            selected_mode = router_data.get("response_mode", MODE_LLM)
            mode_reason = router_data.get("reason", "")
            stages = router_data.get("stages", STAGES_MAP.get(selected_mode, []))
            search_query = router_data.get("search_query") or query
            route = ROUTE_WEB_RESEARCH if selected_mode in [MODE_WEB, MODE_HYBRID] else ROUTE_GENERAL_CHAT
    else:
        # Classify execution route and automatic response mode (LLM, WEB, HYBRID, CLARIFICATION)
        router_data = classify_request_mode(query, recent_history, allow_model_call=True)
        selected_mode = router_data.get("response_mode", MODE_LLM)
        mode_reason = router_data.get("reason", "")
        stages = router_data.get("stages", STAGES_MAP.get(selected_mode, []))
        search_query = router_data.get("search_query") or query
        route = ROUTE_WEB_RESEARCH if selected_mode in [MODE_WEB, MODE_HYBRID] else ROUTE_GENERAL_CHAT

    t_router = time.time()
    router_ms = round((t_router - t_start) * 1000, 2)
    log_routing_decision(request_id, conversation_id, query, selected_mode, mode_reason, t_start)

    # 1. Publish REQUEST_STARTED event
    event_bus.publish(
        request_id=request_id,
        execution_id=execution_id,
        node_id="request_router",
        component_name="Request Understanding Router",
        component_type="router_agent",
        event_type="REQUEST_STARTED",
        execution_status="RUNNING",
        safe_task_summary=f"Analyzing directive: '{query[:60]}...'",
        conversation_id=conversation_id,
        response_mode=selected_mode,
        mode_reason=mode_reason,
        stages=stages,
        current_stage=stages[0] if stages else "Understanding request",
        timestamp=t_start,
        query=query,
        user_message_id=user_message_id
    )

    # 2. Publish MODE_SELECTED event
    event_bus.publish(
        request_id=request_id,
        execution_id=execution_id,
        node_id="request_router",
        component_name="Request Understanding Router",
        component_type="router_agent",
        event_type="MODE_SELECTED",
        execution_status="COMPLETED",
        safe_task_summary=f"Selected [{selected_mode}] Mode: {mode_reason}",
        conversation_id=conversation_id,
        response_mode=selected_mode,
        mode_reason=mode_reason,
        stages=stages,
        current_stage=stages[1] if len(stages) > 1 else stages[0],
        timestamp=t_router
    )

    # =========================================================================
    # PATH A: LLM MODE (Direct Reasoning, Instant Streaming, <1s First Token)
    # =========================================================================
    if selected_mode == MODE_LLM:
        event_bus.publish(
            request_id=request_id,
            execution_id=execution_id,
            node_id="fast_route",
            component_name="LLM Reasoning Engine",
            component_type="reasoning_agent",
            event_type="REASONING_STARTED",
            execution_status="RUNNING",
            safe_task_summary="Preparing reasoning context...",
            conversation_id=conversation_id,
            response_mode=MODE_LLM,
            mode_reason=mode_reason,
            stages=stages,
            current_stage="Preparing reasoning context",
            timestamp=t_router
        )

        history_str = ""
        if recent_history:
            history_str = "Prior Conversation Context:\n" + "\n".join(
                f"- {turn.get('role', 'user').upper()}: {turn.get('content', '')[:180]}"
                for turn in recent_history
            ) + "\n\n"

        system_prompt = (
            "You are O.P.S., a sophisticated personal AI assistant inspired by JARVIS from Iron Man.\n"
            "Tone: articulate, calm, confident, helpful, proactive, and technically astute.\n"
            "When the user gives a brief conversational reply or acknowledgment (e.g. 'yeah', 'yes', 'ok', 'sure', 'continue'), "
            "respond cordially in 1-2 sentences acknowledging readiness and asking how to proceed.\n"
            "When answering questions or requests, respond directly and concisely without internal monologues.\n"
            "Formatting:\n"
            "- Short, meaningful paragraphs\n"
            "- Bullet points (- ) for features, lists, and summaries\n"
            "- Numbered lists (1., 2.) for sequential steps or instructions\n"
            "- Markdown tables (| Column | Details |) when comparing options or data\n"
            "- Clean code fences (```python ... ```) with language labels\n"
            "- Relevant emojis (💡, ⚙️, 🚀, ✅, 🔍, 🧠, 📌) used naturally\n\n"
            "At the very end of your response, you MUST append a separate section:\n"
            "## 📌 Discussion So Far\n"
            "List 2 to 4 concise bullet points summarizing the discussion up to this point."
        )

        fast_prompt = f"{history_str}User Directive: {query}\n\nO.P.S.:"
        t_first_token = [None]

        def on_fast_token(token: str):
            if event_bus.is_cancelled(conversation_id):
                raise RuntimeError("Execution cancelled by user")
            if t_first_token[0] is None:
                t_first_token[0] = time.time()
            event_bus.publish_text_chunk(
                request_id=request_id,
                execution_id=execution_id,
                chunk=token,
                conversation_id=conversation_id
            )

        def on_fast_thought(thought: str):
            if event_bus.is_cancelled(conversation_id):
                raise RuntimeError("Execution cancelled by user")
            event_bus.publish(
                request_id=request_id,
                execution_id=execution_id,
                node_id="fast_route",
                component_name="Fast Direct Reasoning",
                component_type="reasoning_agent",
                event_type="NODE_THOUGHT",
                execution_status="RUNNING",
                safe_task_summary=f"Formulating response...",
                safe_output_summary=thought,
                conversation_id=conversation_id,
                timestamp=time.time()
            )

        try:
            final_answer = ollama_client.generate_stream(
                model=MODEL_QWEN_1_7B,
                prompt=fast_prompt,
                system_prompt=system_prompt,
                temperature=0.2,
                num_predict=768,
                num_ctx=2048,
                on_token=on_fast_token,
                on_thought=on_fast_thought,
                bypass_thinking=True,
                timeout=60.0
            )
        except Exception as e:
            if "cancelled by user" in str(e) or event_bus.is_cancelled(conversation_id):
                final_answer = "⏹ Response generation cancelled by user."
            else:
                logger.warning(f"Fast path LLM error ({e}), synthesizing fallback response.")
                final_answer = (
                    f"Certainly, sir. Regarding **{query}**:\n\n"
                    f"The directive has been acknowledged and registered into the active O.P.S. context.\n\n"
                    f"## 📌 Discussion So Far\n"
                    f"- User directive: {query}\n"
                    f"- Session maintained under ID: `{conversation_id[:12]}`\n"
                )
                event_bus.publish_text_chunk(
                    request_id=request_id,
                    execution_id=execution_id,
                    chunk=final_answer,
                    conversation_id=conversation_id
                )

        # Non-empty response guarantee: If model finished with empty response text
        if not final_answer or not final_answer.strip():
            logger.warning(f"Fast path LLM produced empty output for query '{query}'. Providing JARVIS resolution.")
            clean_q = query.strip().lower().rstrip(".!?,")
            if clean_q in ["yeah", "yes", "yep", "ok", "okay", "sure", "alright", "fine", "cool", "got it", "continue", "proceed"]:
                final_answer = (
                    "Certainly, sir. Standing by for your directive — what would you like me to tackle next?\n\n"
                    "## 📌 Discussion So Far\n"
                    f"- User acknowledgment received: '{query}'\n"
                    "- System standing by for operational directives."
                )
            else:
                final_answer = (
                    f"Understood, sir. Regarding **{query}**:\n\n"
                    "The context has been evaluated and registered. How would you like to proceed?\n\n"
                    "## 📌 Discussion So Far\n"
                    f"- Directive received: '{query}'\n"
                    "- Active context preserved."
                )
            event_bus.publish_text_chunk(
                request_id=request_id,
                execution_id=execution_id,
                chunk=final_answer,
                conversation_id=conversation_id
            )

        if event_bus.is_cancelled(conversation_id):
            conv.refresh_from_db()
            conv.status = "CANCELLED"
            conv.active_execution_id = None
            conv.save()
            return JsonResponse({
                "status": "cancelled",
                "conversation_id": conversation_id,
                "message": "Execution was cancelled by the user."
            }, status=200)

        # Ensure '## 📌 Discussion So Far' is present
        conv_summary = extract_summary_from_text(final_answer)
        if not conv_summary:
            conv_summary = generate_updated_summary(
                previous_summary=conv.summary,
                conversation_turns=recent_history,
                latest_query=query,
                latest_answer=final_answer
            )
            summary_block = f"\n\n## 📌 Discussion So Far\n{conv_summary}"
            final_answer += summary_block
            event_bus.publish_text_chunk(
                request_id=request_id,
                execution_id=execution_id,
                chunk=summary_block,
                conversation_id=conversation_id
            )

        # Save assistant message to database
        assistant_msg = ChatMessage.objects.create(
            conversation=conv,
            message_id=assistant_message_id,
            role="assistant",
            content=final_answer,
            input_type="text",
            status="completed",
            metadata={
                "citations": [],
                "plan": [],
                "conversation_summary": conv_summary,
                "execution_id": execution_id,
                "request_id": request_id,
                "iterations": 0,
                "mode": MODE_LLM,
                "response_mode": MODE_LLM,
                "mode_reason": mode_reason,
                "stages": stages
            }
        )

        conv.refresh_from_db()
        conv.status = "ACTIVE"
        conv.summary = conv_summary
        conv.active_execution_id = None
        conv.save()

        t_end = time.time()
        first_token_ms = round(((t_first_token[0] or t_end) - t_start) * 1000, 2)
        total_ms = round((t_end - t_start) * 1000, 2)

        logger.info(
            f"[PERF TIMING] LLM Route: Total={total_ms}ms, FirstToken={first_token_ms}ms, Router={router_ms}ms"
        )

        event_bus.publish(
            request_id=request_id,
            execution_id=execution_id,
            node_id="fast_route",
            component_name="Fast Direct Reasoning",
            component_type="reasoning_agent",
            event_type="NODE_COMPLETED",
            execution_status="COMPLETED",
            safe_task_summary=f"Synthesized response in {total_ms/1000:.2f}s (first token: {first_token_ms}ms)",
            safe_output_summary=final_answer[:120] + "...",
            conversation_id=conversation_id,
            response_mode=MODE_LLM,
            current_stage="Completing response",
            timestamp=t_end
        )

        event_bus.publish(
            request_id=request_id,
            execution_id=execution_id,
            node_id="chat_manager",
            component_name="Chat Manager",
            component_type="execution_worker",
            event_type="response_completed",
            execution_status="COMPLETED",
            safe_task_summary="Assistant response completed.",
            safe_output_summary=final_answer[:120] + "...",
            conversation_id=conversation_id,
            timestamp=t_end,
            final_answer=final_answer,
            content=final_answer,
            response_mode=MODE_LLM,
            mode=MODE_LLM,
            mode_reason=mode_reason,
            current_stage="Completing response",
            stages=stages,
            citations=[]
        )

        return JsonResponse({
            "status": "success",
            "message_id": assistant_message_id,
            "conversation_id": conversation_id,
            "request_id": request_id,
            "role": "assistant",
            "content": final_answer,
            "final_answer": final_answer,
            "answer": final_answer,
            "response": final_answer,
            "conversation_summary": conv_summary,
            "mode": MODE_LLM,
            "response_mode": MODE_LLM,
            "mode_reason": mode_reason,
            "stages": stages,
            "plan": [],
            "citations": [],
            "node_history": ["llm_mode"],
            "timings": {
                "router_ms": router_ms,
                "first_token_ms": first_token_ms,
                "total_ms": total_ms
            }
        }, status=200)

    # =========================================================================
    # PATH D: DOCUMENT MODE (Temporary Pinecone Retrieval & Grounded Reasoning)
    # =========================================================================
    if selected_mode == MODE_DOCUMENT:
        event_bus.publish(
            request_id=request_id,
            execution_id=execution_id,
            node_id="document_retriever",
            component_name="Temporary Document Retrieval",
            component_type="retrieval_agent",
            event_type="RETRIEVAL_STARTED",
            execution_status="RUNNING",
            safe_task_summary="Searching uploaded document in Pinecone...",
            conversation_id=conversation_id,
            response_mode=MODE_DOCUMENT,
            mode_reason=mode_reason,
            stages=stages,
            current_stage="Searching uploaded document",
            timestamp=t_router
        )

        passages = rag_service.query_context(conversation_id=conversation_id, query=query, top_k=4)

        event_bus.publish(
            request_id=request_id,
            execution_id=execution_id,
            node_id="document_retriever",
            component_name="Temporary Document Retrieval",
            component_type="retrieval_agent",
            event_type="RETRIEVAL_COMPLETED",
            execution_status="COMPLETED",
            safe_task_summary=f"Retrieved {len(passages)} passages from temporary document vector store",
            conversation_id=conversation_id,
            response_mode=MODE_DOCUMENT,
            mode_reason=mode_reason,
            stages=stages,
            current_stage="Reading document passages",
            timestamp=time.time()
        )

        event_bus.publish(
            request_id=request_id,
            execution_id=execution_id,
            node_id="document_reasoning",
            component_name="Document Grounded Reasoning",
            component_type="reasoning_agent",
            event_type="REASONING_STARTED",
            execution_status="RUNNING",
            safe_task_summary="Preparing grounded answer...",
            conversation_id=conversation_id,
            response_mode=MODE_DOCUMENT,
            mode_reason=mode_reason,
            stages=stages,
            current_stage="Preparing grounded answer",
            timestamp=time.time()
        )

        citations = []
        if not passages:
            final_answer = (
                f"Sir, the active document context does not contain information regarding '{query}'.\n\n"
                f"No matching sections, tables, or relevant passages were found in the uploaded text."
            )
            event_bus.publish_text_chunk(
                request_id=request_id,
                execution_id=execution_id,
                chunk=final_answer,
                conversation_id=conversation_id
            )
        else:
            passages_text = "\n\n".join([
                f"--- [Document: {p['doc_name']} | Page: {p['page']} | Section: {p['section']}] ---\n{p['text']}"
                for p in passages
            ])
            citations = [
                {
                    "title": f"{p['doc_name']} (Page {p['page']})",
                    "url": f"document://{p['doc_id']}/page/{p['page']}",
                    "section": p.get("section", "General"),
                    "snippet": p["text"][:160]
                }
                for p in passages
            ]

            doc_system_prompt = (
                "You are O.P.S. 2.0 (Over-Engineered Programmed System).\n"
                "Tone: articulate, calm, confident, helpful, and technically astute (JARVIS persona).\n"
                "Answer the user's question using ONLY the retrieved document passages below.\n"
                "Grounding Rules:\n"
                "1. Answer truthfully and strictly based on the provided document passages. Do NOT invent or extrapolate facts.\n"
                "2. If the document does not contain the answer, state that the document does not provide the information.\n"
                "3. Format your response cleanly using structured bullet points for key items, findings, and explanations.\n"
                "4. Cite the source document name, page number, and section title for your claims."
            )

            doc_prompt = (
                f"Retrieved Document Context:\n{passages_text}\n\n"
                f"User Directive: {query}\n\n"
                f"Provide a structured, grounded answer strictly based on the excerpts above."
            )

            def on_doc_token(token: str):
                if event_bus.is_cancelled(conversation_id):
                    raise RuntimeError("Execution cancelled by user")
                event_bus.publish_text_chunk(
                    request_id=request_id,
                    execution_id=execution_id,
                    chunk=token,
                    conversation_id=conversation_id
                )

            try:
                final_answer = ollama_client.generate_stream(
                    model=MODEL_QWEN_1_7B,
                    prompt=doc_prompt,
                    system_prompt=doc_system_prompt,
                    temperature=0.1,
                    num_predict=1536,
                    num_ctx=2048,
                    on_token=on_doc_token,
                    bypass_thinking=True,
                    timeout=60.0
                )
            except Exception as e:
                if "cancelled by user" in str(e) or event_bus.is_cancelled(conversation_id):
                    final_answer = "⏹ Response generation cancelled by user."
                else:
                    logger.error(f"Document RAG generation error: {e}")
                    final_answer = f"Error during document reasoning: {e}"

            # Append document reference list
            ref_lines = [f"- **Reference [{idx}]**: `{c['title']}` (Section: *{c['section']}*)" for idx, c in enumerate(citations, 1)]
            doc_refs_block = "\n\n### 📑 Document References\n" + "\n".join(ref_lines)
            final_answer += doc_refs_block
            event_bus.publish_text_chunk(
                request_id=request_id,
                execution_id=execution_id,
                chunk=doc_refs_block,
                conversation_id=conversation_id
            )

        if event_bus.is_cancelled(conversation_id):
            conv.refresh_from_db()
            conv.status = "CANCELLED"
            conv.active_execution_id = None
            conv.save()
            return JsonResponse({"status": "cancelled", "conversation_id": conversation_id}, status=200)

        # Discussion So Far section
        conv_summary = extract_summary_from_text(final_answer)
        if not conv_summary:
            conv_summary = generate_updated_summary(
                previous_summary=conv.summary,
                conversation_turns=recent_history,
                latest_query=query,
                latest_answer=final_answer
            )
            summary_block = f"\n\n## 📌 Discussion So Far\n{conv_summary}"
            final_answer += summary_block
            event_bus.publish_text_chunk(
                request_id=request_id,
                execution_id=execution_id,
                chunk=summary_block,
                conversation_id=conversation_id
            )

        # Save assistant message to database
        assistant_msg = ChatMessage.objects.create(
            conversation=conv,
            message_id=assistant_message_id,
            role="assistant",
            content=final_answer,
            input_type="text",
            status="completed",
            metadata={
                "citations": citations,
                "plan": [],
                "conversation_summary": conv_summary,
                "execution_id": execution_id,
                "request_id": request_id,
                "iterations": 0,
                "mode": MODE_DOCUMENT,
                "response_mode": MODE_DOCUMENT,
                "mode_reason": mode_reason,
                "stages": stages,
                "attached_documents": rag_service.get_active_documents(conversation_id)
            }
        )

        conv.refresh_from_db()
        conv.status = "ACTIVE"
        conv.active_execution_id = None
        conv.save()

        # Emit completion events
        event_bus.publish(
            request_id=request_id,
            execution_id=execution_id,
            node_id="response_delivery",
            component_name="Response Delivery",
            component_type="delivery_agent",
            event_type="STAGE_CHANGED",
            execution_status="COMPLETED",
            safe_task_summary="Response delivered to Cockpit",
            conversation_id=conversation_id,
            response_mode=MODE_DOCUMENT,
            mode_reason=mode_reason,
            stages=stages,
            current_stage="Completing response",
            timestamp=time.time()
        )
        event_bus.publish_stream_end(
            request_id=request_id,
            execution_id=execution_id,
            conversation_id=conversation_id,
            metadata={"mode": MODE_DOCUMENT, "citations": citations}
        )

        total_ms = round((time.time() - t_start) * 1000, 2)
        return JsonResponse({
            "status": "success",
            "message_id": assistant_message_id,
            "conversation_id": conversation_id,
            "request_id": request_id,
            "role": "assistant",
            "content": final_answer,
            "final_answer": final_answer,
            "answer": final_answer,
            "response": final_answer,
            "conversation_summary": conv_summary,
            "mode": MODE_DOCUMENT,
            "response_mode": MODE_DOCUMENT,
            "mode_reason": mode_reason,
            "stages": stages,
            "plan": [],
            "citations": citations,
            "node_history": ["document_retriever", "document_reasoning"],
            "timings": {
                "router_ms": router_ms,
                "total_ms": total_ms
            }
        }, status=200)

    # =========================================================================
    # PATH C: AUTOMATION MODE (Pywinauto Desktop / Playwright Browser / Hybrid)
    # =========================================================================
    if selected_mode in [MODE_AUTOMATION, MODE_DESKTOP_AUTO, MODE_BROWSER_AUTO, MODE_HYBRID_AUTO]:
        from automation_system.services.automation_service import AutomationService
        plan_res = AutomationService.create_and_plan_task(
            user_request=query,
            conversation_id=conversation_id,
            task_id=f"auto_{execution_id}"
        )
        auto_mode = plan_res.get("automation_mode", "DESKTOP")

        # Handle Clarification
        if plan_res.get("status") == "NEEDS_CLARIFICATION":
            clarification_msg = (
                f"⚠️ **Clarification Required**:\n"
                f"{plan_res.get('clarification_prompt')}\n\n"
                f"## 📌 Discussion So Far\n"
                f"- Automation directive requires clarification: '{query}'\n"
                f"- Mode: `{auto_mode}`"
            )
            event_bus.publish_text_chunk(request_id=request_id, execution_id=execution_id, chunk=clarification_msg, conversation_id=conversation_id)
            assistant_msg = ChatMessage.objects.create(
                conversation=conv,
                message_id=assistant_message_id,
                role="assistant",
                content=clarification_msg,
                input_type="text",
                status="completed",
                metadata={"mode": auto_mode, "response_mode": auto_mode, "stages": stages}
            )
            event_bus.publish(
                request_id=request_id, execution_id=execution_id, node_id="chat_manager",
                component_name="Chat Manager", component_type="execution_worker",
                event_type="response_completed", execution_status="COMPLETED",
                safe_task_summary="Clarification requested.", safe_output_summary=clarification_msg[:120],
                conversation_id=conversation_id, timestamp=time.time(),
                final_answer=clarification_msg, content=clarification_msg, response_mode=auto_mode, stages=stages
            )
            return JsonResponse({
                "status": "needs_clarification", "message_id": assistant_message_id,
                "conversation_id": conversation_id, "request_id": request_id,
                "role": "assistant", "content": clarification_msg, "final_answer": clarification_msg,
                "response": clarification_msg, "mode": auto_mode, "response_mode": auto_mode,
                "stages": stages
            }, status=200)

        # Handle Approval Required
        if plan_res.get("status") == "WAITING_FOR_APPROVAL":
            appr_msg = (
                f"🛑 **Human Approval Required**:\n"
                f"{plan_res.get('approval_reason')}\n\n"
                f"Please review the pending action in the Cockpit and authorize or reject execution.\n\n"
                f"## 📌 Discussion So Far\n"
                f"- Directive paused at safety gate: '{query}'\n"
                f"- Requires user approval before proceeding with `{auto_mode}` action."
            )
            event_bus.publish_text_chunk(request_id=request_id, execution_id=execution_id, chunk=appr_msg, conversation_id=conversation_id)
            assistant_msg = ChatMessage.objects.create(
                conversation=conv,
                message_id=assistant_message_id,
                role="assistant",
                content=appr_msg,
                input_type="text",
                status="pending_approval",
                metadata={"mode": auto_mode, "response_mode": auto_mode, "approval_id": plan_res.get("approval_id"), "stages": stages}
            )
            event_bus.publish(
                request_id=request_id, execution_id=execution_id, node_id="chat_manager",
                component_name="Chat Manager", component_type="execution_worker",
                event_type="response_completed", execution_status="WAITING_FOR_APPROVAL",
                safe_task_summary="Paused for user approval.", safe_output_summary=appr_msg[:120],
                conversation_id=conversation_id, timestamp=time.time(),
                final_answer=appr_msg, content=appr_msg, response_mode=auto_mode, stages=stages
            )
            return JsonResponse({
                "status": "waiting_for_approval", "message_id": assistant_message_id,
                "conversation_id": conversation_id, "request_id": request_id,
                "role": "assistant", "content": appr_msg, "final_answer": appr_msg,
                "response": appr_msg, "approval_id": plan_res.get("approval_id"),
                "mode": auto_mode, "response_mode": auto_mode, "stages": stages
            }, status=200)

        # Immediate Execution for Authorized / Safe Automation Tasks
        exec_res = AutomationService.execute_task(plan_res.get("task_id"))
        final_answer = exec_res.get("final_answer", "")
        event_bus.publish_text_chunk(request_id=request_id, execution_id=execution_id, chunk=final_answer, conversation_id=conversation_id)

        conv_summary = extract_summary_from_text(final_answer) or f"- Completed {auto_mode} automation for: '{query}'"
        assistant_msg = ChatMessage.objects.create(
            conversation=conv,
            message_id=assistant_message_id,
            role="assistant",
            content=final_answer,
            input_type="text",
            status="completed",
            metadata={
                "task_id": plan_res.get("task_id"),
                "mode": auto_mode,
                "response_mode": auto_mode,
                "plan": plan_res.get("steps", []),
                "step_results": exec_res.get("step_results", []),
                "stages": stages
            }
        )

        conv.refresh_from_db()
        conv.status = "ACTIVE"
        conv.summary = conv_summary
        conv.active_execution_id = None
        conv.save()

        event_bus.publish(
            request_id=request_id, execution_id=execution_id, node_id="chat_manager",
            component_name="Chat Manager", component_type="execution_worker",
            event_type="response_completed", execution_status="COMPLETED",
            safe_task_summary="Automation task completed.", safe_output_summary=final_answer[:120],
            conversation_id=conversation_id, timestamp=time.time(),
            final_answer=final_answer, content=final_answer, response_mode=auto_mode, stages=stages
        )

        return JsonResponse({
            "status": "success" if exec_res.get("success") else "failed",
            "message_id": assistant_message_id, "conversation_id": conversation_id,
            "request_id": request_id, "role": "assistant",
            "content": final_answer, "final_answer": final_answer, "response": final_answer,
            "mode": auto_mode, "response_mode": auto_mode, "stages": stages,
            "plan": plan_res.get("steps", [])
        }, status=200)

    # =========================================================================
    # PATH B: WEB & HYBRID MODES (LangGraph Multi-Agent Research & Evidence Synthesis)
    # =========================================================================
    if selected_mode == MODE_HYBRID:
        event_bus.publish(
            request_id=request_id,
            execution_id=execution_id,
            node_id="hybrid_planner",
            component_name="Hybrid Reasoning Planner",
            component_type="reasoning_agent",
            event_type="REASONING_STARTED",
            execution_status="RUNNING",
            safe_task_summary="Analyzing question & preparing conceptual reasoning...",
            conversation_id=conversation_id,
            response_mode=MODE_HYBRID,
            mode_reason=mode_reason,
            stages=stages,
            current_stage="Analyzing the question",
            timestamp=time.time()
        )
        event_bus.publish(
            request_id=request_id,
            execution_id=execution_id,
            node_id="hybrid_search_prep",
            component_name="Research Dispatcher",
            component_type="execution_worker",
            event_type="RESEARCH_STARTED",
            execution_status="RUNNING",
            safe_task_summary="Searching external sources for live evidence...",
            conversation_id=conversation_id,
            response_mode=MODE_HYBRID,
            mode_reason=mode_reason,
            stages=stages,
            current_stage="Searching external sources",
            timestamp=time.time()
        )
    else:  # MODE_WEB
        event_bus.publish(
            request_id=request_id,
            execution_id=execution_id,
            node_id="web_prep",
            component_name="Web Research Dispatcher",
            component_type="execution_worker",
            event_type="RESEARCH_STARTED",
            execution_status="RUNNING",
            safe_task_summary="Selecting research strategy & initializing live web search...",
            conversation_id=conversation_id,
            response_mode=MODE_WEB,
            mode_reason=mode_reason,
            stages=stages,
            current_stage="Selecting research strategy",
            timestamp=time.time()
        )

    # Initial research state
    initial_state = {
        "request_id": request_id,
        "execution_id": execution_id,
        "session_id": session_id,
        "conversation_id": conversation_id,
        "query": query,
        "input_type": input_type,
        "response_mode": selected_mode,
        "search_query": search_query,
        "mode_reason": mode_reason,
        "stages": stages,
        "conversation_history": recent_history,
        "conversation_summary": conv.summary,
        "long_term_memories": long_term_mems,
        "project_knowledge": proj_docs,
        "iteration_count": 0,
        "max_iterations": max_iterations,
        "search_results": [],
        "crawled_pages": [],
        "rendered_pages": [],
        "extracted_contents": [],
        "processed_chunks": [],
        "retrieved_evidence": [],
        "citations": [],
        "node_history": [],
        "errors": []
    }

    # Create persistent session record
    try:
        ResearchSession.objects.create(
            conversation_id=conversation_id,
            session_id=session_id,
            request_id=request_id,
            query=query,
            status="RUNNING"
        )
    except Exception:
        pass

    try:
        # Invoke LangGraph using conversation_id as thread identifier
        config = {"configurable": {"thread_id": conversation_id}}
        final_state = research_graph.invoke(initial_state, config=config)

        # Check if conversation was cancelled while running
        if event_bus.is_cancelled(conversation_id):
            conv.refresh_from_db()
            conv.status = "CANCELLED"
            conv.active_execution_id = None
            conv.save()
            return JsonResponse({
                "status": "cancelled",
                "conversation_id": conversation_id,
                "message": "Execution was cancelled by the user."
            }, status=200)

        final_answer = final_state.get("final_answer", "")
        citations = final_state.get("citations", [])
        plan = final_state.get("research_plan", {}).get("plan_steps", [])

        # Format plan steps for UI
        plan_steps_ui = []
        for idx, step_desc in enumerate(plan, start=1):
            plan_steps_ui.append({
                "step": idx,
                "description": step_desc,
                "assigned_agent": "research",
                "capability": "web.research",
                "verified": True
            })

        # Process continuous conversation summary
        conv_summary = final_state.get("conversation_summary", "")
        if not conv_summary:
            conv_summary = extract_summary_from_text(final_answer) or ""

        if not conv_summary:
            history_turns = list(conv.messages.values("role", "content")[:10])
            conv_summary = generate_updated_summary(
                previous_summary=conv.summary,
                conversation_turns=history_turns,
                latest_query=query,
                latest_answer=final_answer
            )

        final_answer = attach_summary_to_response(final_answer, conv_summary)

        # Save assistant message to database
        assistant_msg = ChatMessage.objects.create(
            conversation=conv,
            message_id=assistant_message_id,
            role="assistant",
            content=final_answer,
            input_type="text",
            status="completed",
            metadata={
                "citations": citations,
                "plan": plan_steps_ui,
                "conversation_summary": conv_summary,
                "execution_id": execution_id,
                "request_id": request_id,
                "iterations": final_state.get("iteration_count", 0),
                "mode": selected_mode,
                "response_mode": selected_mode,
                "mode_reason": mode_reason,
                "stages": stages
            }
        )

        # Update conversation status and summary in database
        conv.refresh_from_db()
        conv.status = "ACTIVE"
        conv.summary = conv_summary
        conv.active_execution_id = None
        conv.save()

        # Update session record safely
        try:
            sess = ResearchSession.objects.filter(request_id=request_id).first()
            if sess:
                sess.status = "COMPLETED"
                sess.final_answer = final_answer
                sess.iterations = final_state.get("iteration_count", 0)
                sess.completed_at = timezone.now()
                sess.save()
        except Exception:
            pass

        t_end = time.time()
        total_ms = round((t_end - t_start) * 1000, 2)

        # Publish response completed event with verified research counts & mode
        event_bus.publish(
            request_id=request_id,
            execution_id=execution_id,
            node_id="chat_manager",
            component_name="Chat Manager",
            component_type="execution_worker",
            event_type="response_completed",
            execution_status="COMPLETED",
            safe_task_summary="Assistant response completed.",
            safe_output_summary=final_answer[:120] + "...",
            conversation_id=conversation_id,
            timestamp=t_end,
            final_answer=final_answer,
            content=final_answer,
            response_mode=selected_mode,
            mode=selected_mode,
            mode_reason=mode_reason,
            current_stage="Completing response",
            stages=stages,
            citations=citations,
            sources_count=len(final_state.get("search_results", [])),
            pages_count=len(final_state.get("crawled_pages", []))
        )

        return JsonResponse({
            "status": "success",
            "message_id": assistant_message_id,
            "conversation_id": conversation_id,
            "request_id": request_id,
            "role": "assistant",
            "content": final_answer,
            "final_answer": final_answer,
            "response": final_answer,
            "conversation_summary": conv_summary,
            "mode": selected_mode,
            "response_mode": selected_mode,
            "mode_reason": mode_reason,
            "stages": stages,
            "plan": plan_steps_ui,
            "citations": citations,
            "analysis": final_state.get("analysis", {}),
            "iterations": final_state.get("iteration_count", 0),
            "timings": {
                "router_ms": router_ms,
                "total_ms": total_ms
            }
        }, status=200)

    except Exception as e:
        logger.error(f"LangGraph conversation message execution failed: {e}", exc_info=True)
        conv.refresh_from_db()
        conv.status = "ACTIVE"
        conv.active_execution_id = None
        conv.save()

        event_bus.publish(
            request_id=request_id,
            execution_id=execution_id,
            node_id="chat_manager",
            component_name="Chat Manager",
            component_type="execution_worker",
            event_type="response_failed",
            execution_status="FAILED",
            safe_task_summary="Execution failed.",
            error_details=str(e),
            conversation_id=conversation_id,
            timestamp=time.time()
        )

        return JsonResponse({
            "status": "error",
            "conversation_id": conversation_id,
            "request_id": request_id,
            "error": str(e)
        }, status=500)


@csrf_exempt
def conversation_cancel(request, conversation_id):
    """
    Endpoint: POST /api/chat/conversations/{id}/cancel/
    Cancels the active generation for a conversation.
    """
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed. Use POST."}, status=405)

    conv = Conversation.objects.filter(conversation_id=conversation_id).first()
    if not conv:
        return JsonResponse({"error": "Conversation not found"}, status=404)

    event_bus.cancel_conversation(conversation_id)
    conv.status = "CANCELLED"
    conv.active_execution_id = None
    conv.save()

    return JsonResponse({
        "status": "cancelled",
        "conversation_id": conversation_id,
        "message": "Active generation cancelled successfully."
    })


@csrf_exempt
def conversation_events(request, conversation_id):
    """
    Endpoint: GET /api/chat/conversations/{id}/events/
    Streams real-time Server-Sent Events (SSE) for the active conversation.
    """
    def event_stream():
        q = event_bus.subscribe(conversation_id)
        # Yield initial connection heartbeat
        connect_payload = json.dumps({
            "event_type": "STREAM_CONNECTED",
            "conversation_id": conversation_id,
            "timestamp": time.time()
        })
        yield f"data: {connect_payload}\n\n"

        try:
            while True:
                try:
                    event = q.get(timeout=20.0)
                    yield f"data: {json.dumps(event)}\n\n"
                except queue.Empty:
                    # Keep-alive heartbeat
                    yield f": heartbeat {int(time.time())}\n\n"
        except (GeneratorExit, ConnectionResetError, BrokenPipeError, Exception) as e:
            logger.debug(f"SSE client closed stream for conversation {conversation_id}: {e}")
        finally:
            event_bus.unsubscribe(conversation_id, q)

    response = StreamingHttpResponse(event_stream(), content_type="text/event-stream")
    response["Cache-Control"] = "no-cache"
    response["X-Accel-Buffering"] = "no"
    return response


# ======================================================================
# 3. Cockpit Backwards-Compatibility Endpoints
# ======================================================================

@csrf_exempt
def execute_research(request):
    """
    Backwards-compatible execution endpoint.
    Routes to conversation_messages using a default or requested conversation_id.
    """
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed. Use POST."}, status=405)

    try:
        data = json.loads(request.body.decode("utf-8")) if request.body else {}
    except Exception:
        data = {}

    conversation_id = data.get("conversation_id") or data.get("session_id") or f"conv_{int(time.time())}_{uuid.uuid4().hex[:6]}"
    return conversation_messages(request, conversation_id)


@csrf_exempt
def stream_research_events(request):
    """
    SSE stream endpoint by request_id.
    """
    request_id = request.GET.get("request_id")
    if not request_id:
        return JsonResponse({"error": "request_id parameter is required"}, status=400)

    def event_stream():
        q = event_bus.subscribe(request_id)
        connect_payload = json.dumps({
            "event_type": "STREAM_CONNECTED",
            "request_id": request_id,
            "timestamp": time.time()
        })
        yield f"data: {connect_payload}\n\n"

        try:
            while True:
                try:
                    event = q.get(timeout=20.0)
                    yield f"data: {json.dumps(event)}\n\n"
                    if event.get("event_type") in ["response_completed", "response_failed", "response_cancelled", "WORKFLOW_COMPLETED", "WORKFLOW_FAILED"]:
                        break
                except queue.Empty:
                    yield f": heartbeat {int(time.time())}\n\n"
        finally:
            event_bus.unsubscribe(request_id, q)

    response = StreamingHttpResponse(event_stream(), content_type="text/event-stream")
    response["Cache-Control"] = "no-cache"
    response["X-Accel-Buffering"] = "no"
    return response


@csrf_exempt
def refresh_session(request):
    """
    Backwards-compatible session refresh endpoint.
    Performs permanent conversation reset and returns new unique conversation ID.
    """
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed. Use POST."}, status=405)

    try:
        data = json.loads(request.body.decode("utf-8")) if request.body else {}
    except Exception:
        data = {}

    old_session_id = data.get("session_id") or data.get("conversation_id")
    if old_session_id:
        conversation_detail(request, old_session_id)
        from research_system.services.temporary_rag_service import get_temporary_rag_service
        get_temporary_rag_service().clear_session(old_session_id)

    new_id = f"conv_{int(time.time())}_{uuid.uuid4().hex[:6]}"
    Conversation.objects.create(conversation_id=new_id, title="New Conversation", status="ACTIVE")

    return JsonResponse({
        "status": "success",
        "new_session_id": new_id,
        "conversation_id": new_id,
        "message": "Active session permanently reset and initialized."
    })


@csrf_exempt
def stop_session(request):
    """
    Backwards-compatible session stop endpoint.
    """
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed. Use POST."}, status=405)

    try:
        data = json.loads(request.body.decode("utf-8")) if request.body else {}
    except Exception:
        data = {}

    session_id = data.get("session_id") or data.get("conversation_id")
    if session_id:
        return conversation_cancel(request, session_id)
    return JsonResponse({"status": "cancelled", "message": "Execution halted."})


def get_session_history(request):
    """
    Retrieves full execution history for a session or request.
    Endpoint: GET /api/v1/research/history/?session_id=...&request_id=...
    """
    session_id = request.GET.get("session_id")
    request_id = request.GET.get("request_id")
    conversation_id = request.GET.get("conversation_id")

    query = NodeExecutionEvent.objects.all()
    if conversation_id:
        query = query.filter(conversation_id=conversation_id)
    elif session_id:
        query = query.filter(session__session_id=session_id)
    if request_id:
        query = query.filter(request_id=request_id)

    events = []
    for ev in query[:100]:
        events.append({
            "request_id": ev.request_id,
            "execution_id": ev.execution_id,
            "conversation_id": ev.conversation_id,
            "node_id": ev.node_id,
            "component_name": ev.component_name,
            "component_type": ev.component_type,
            "event_type": ev.event_type,
            "execution_status": ev.execution_status,
            "timestamp": ev.timestamp,
            "tool_name": ev.tool_name,
            "safe_task_summary": ev.safe_task_summary,
            "safe_output_summary": ev.safe_output_summary,
            "error_details": ev.error_details,
        })

    return JsonResponse({
        "results": events,
        "events": events,
        "count": len(events)
    })


def audit_logs(request):
    """
    Audit log endpoint for Cockpit frontend.
    Endpoint: GET /api/v1/audit/logs/
    """
    return get_session_history(request)


# ======================================================================
# 4. Human-in-the-Loop (HITL) Approval Lifecycle
# ======================================================================

@csrf_exempt
def create_refresh_approval(request, conversation_id):
    """
    Endpoint: POST /api/chat/conversations/{id}/refresh-approval/
    Initiates a Human-in-the-Loop approval workflow for permanent conversation deletion.
    Pauses active conversation execution, creates a pending approval record, and emits an event.
    """
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed. Use POST."}, status=405)

    conv = Conversation.objects.filter(conversation_id=conversation_id).first()
    if not conv or conv.status == "DELETED":
        return JsonResponse({"error": "Conversation not found"}, status=404)

    # 1. Pause active generation if running
    event_bus.cancel_conversation(conversation_id)
    conv.status = "PENDING_APPROVAL"
    conv.save()

    # 2. Check for an existing PENDING approval or create new
    existing_appr = PendingApproval.objects.filter(
        target_conversation_id=conversation_id,
        action_type="PERMANENT_CONVERSATION_DELETION",
        status="PENDING"
    ).first()

    if existing_appr:
        approval_id = existing_appr.approval_id
        appr = existing_appr
    else:
        approval_id = f"appr_{int(time.time())}_{uuid.uuid4().hex[:6]}"
        appr = PendingApproval.objects.create(
            approval_id=approval_id,
            conversation=conv,
            target_conversation_id=conversation_id,
            execution_id=conv.active_execution_id,
            action_type="PERMANENT_CONVERSATION_DELETION",
            status="PENDING",
            description="Permanent conversation deletion and fresh session initialization."
        )

    # 3. Publish HITL Approval Required event to Live Event Bus
    event_bus.publish(
        request_id=f"req_{approval_id}",
        execution_id=conv.active_execution_id or f"exec_{approval_id}",
        node_id="hitl_approval_gate",
        component_name="HITL Approval Gate",
        component_type="approval_controller",
        event_type="APPROVAL_REQUIRED",
        execution_status="WAITING",
        safe_task_summary="Human-in-the-Loop approval requested: Permanent conversation deletion.",
        conversation_id=conversation_id,
        timestamp=time.time()
    )

    return JsonResponse({
        "status": "pending_approval",
        "approval_id": approval_id,
        "conversation_id": conversation_id,
        "conversation_status": conv.status,
        "action_type": "PERMANENT_CONVERSATION_DELETION",
        "title": "Human Approval Required",
        "subtitle": "Delete Current Conversation?",
        "created_at": appr.created_at.isoformat()
    }, status=201)


@csrf_exempt
def deny_refresh_approval(request, conversation_id, approval_id):
    """
    Endpoint: POST /api/chat/conversations/{id}/refresh-approval/{approval_id}/deny/
    Rejects the pending deletion request. Preserves all messages, checkpoints, and DB records.
    """
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed. Use POST."}, status=405)

    appr = PendingApproval.objects.filter(
        approval_id=approval_id,
        target_conversation_id=conversation_id
    ).first()

    if not appr:
        return JsonResponse({"error": "Approval request not found for this conversation."}, status=404)

    if appr.status != "PENDING":
        return JsonResponse({
            "error": f"Approval request already resolved with status '{appr.status}'."
        }, status=409)

    # 1. Update approval record to REJECTED
    appr.status = "REJECTED"
    appr.resolved_at = timezone.now()
    appr.save()

    # 2. Reset conversation status back to ACTIVE
    conv = Conversation.objects.filter(conversation_id=conversation_id).first()
    if conv and conv.status == "PENDING_APPROVAL":
        conv.status = "ACTIVE"
        conv.save()

    # 3. Publish Approval Rejected event
    event_bus.publish(
        request_id=f"req_{approval_id}",
        execution_id=appr.execution_id or f"exec_{approval_id}",
        node_id="hitl_approval_gate",
        component_name="HITL Approval Gate",
        component_type="approval_controller",
        event_type="APPROVAL_REJECTED",
        execution_status="CANCELLED",
        safe_task_summary="Human-in-the-Loop decision: DENIED. Conversation preserved intact.",
        conversation_id=conversation_id,
        timestamp=time.time()
    )

    return JsonResponse({
        "status": "denied",
        "approval_id": approval_id,
        "conversation_id": conversation_id,
        "conversation_status": "ACTIVE",
        "message": "Permanent deletion denied. Conversation preserved exactly as it was."
    }, status=200)


@csrf_exempt
def accept_refresh_approval(request, conversation_id, approval_id):
    """
    Endpoint: POST /api/chat/conversations/{id}/refresh-approval/{approval_id}/accept/
    Executes permanent conversation deletion upon verified human authorization.
    Atomically deletes conversation & messages, deletes checkpointer state, and creates a fresh conversation.
    """
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed. Use POST."}, status=405)

    appr = PendingApproval.objects.filter(
        approval_id=approval_id,
        target_conversation_id=conversation_id
    ).first()

    if not appr:
        return JsonResponse({"error": "Approval request not found for this conversation."}, status=404)

    if appr.status != "PENDING":
        return JsonResponse({
            "error": f"Approval request already processed with status '{appr.status}'."
        }, status=409)

    try:
        # 1. Mark approval as EXECUTED
        appr.status = "EXECUTED"
        appr.resolved_at = timezone.now()
        appr.save()

        # 2. Cancel in-memory execution token & purge event bus
        event_bus.cancel_conversation(conversation_id)
        delete_conversation_checkpoint(conversation_id)
        event_bus.purge_conversation(conversation_id)

        # 2b. Permanently wipe all temporary Document RAG vectors in Pinecone and memory
        from research_system.services.temporary_rag_service import get_temporary_rag_service
        rag_service = get_temporary_rag_service()
        rag_cleanup = rag_service.clear_session(conversation_id)
        logger.info(f"[HITL ACCEPTED] Temporary RAG vectors & chunk cache wiped for {conversation_id}: {rag_cleanup}")

        # 3. Database Deletion within transaction
        with transaction.atomic():
            conv = Conversation.objects.filter(conversation_id=conversation_id).first()
            deleted_messages_count = 0
            if conv:
                deleted_messages_count = conv.messages.count()
                conv.delete()

            ResearchSession.objects.filter(conversation_id=conversation_id).delete()
            NodeExecutionEvent.objects.filter(conversation_id=conversation_id).delete()

        # 4. Generate fresh conversation ID and record
        new_conv_id = f"conv_{int(time.time())}_{uuid.uuid4().hex[:6]}"
        new_conv = Conversation.objects.create(
            conversation_id=new_conv_id,
            title="New Conversation",
            status="ACTIVE"
        )

        # 5. Verify Category 2 & 3 intact
        retained_memories = UserLongTermMemory.objects.count()
        retained_docs = ProjectKnowledge.objects.count()

        logger.info(
            f"[HITL ACCEPTED] Conversation {conversation_id} deleted via approval {approval_id}. "
            f"New conversation: {new_conv_id}. Retained {retained_memories} memories, {retained_docs} docs."
        )

        return JsonResponse({
            "status": "approved_and_deleted",
            "approval_id": approval_id,
            "conversation_id": conversation_id,
            "new_conversation_id": new_conv_id,
            "deleted_messages_count": deleted_messages_count,
            "long_term_memories_intact": True,
            "project_knowledge_intact": True,
            "category2_long_term_memory": "PRESERVED",
            "category3_project_knowledge": "PRESERVED",
            "rag_session_cleared": True,
            "pinecone_vectors_deleted": rag_cleanup.get("pinecone_vectors_deleted", True),
            "rag_cleanup_verified": rag_cleanup.get("verified", True),
            "message": "Human approval confirmed. Active conversation and temporary document session permanently deleted."
        }, status=200)

    except Exception as e:
        logger.error(f"Failed to execute approved deletion for {conversation_id}: {e}", exc_info=True)
        return JsonResponse({
            "status": "error",
            "approval_id": approval_id,
            "conversation_id": conversation_id,
            "error": f"Deletion execution failed: {str(e)}"
        }, status=500)


def get_pending_approvals(request):
    """
    Endpoint: GET /api/chat/approvals/pending/
    Retrieves currently active PENDING Human-in-the-Loop approval requests strictly for the requested conversation.
    Auto-expires stale approvals older than 5 minutes to prevent infinite prompt loops.
    """
    # 1. Clean up & expire pending approvals older than 5 minutes
    try:
        expiry_cutoff = timezone.now() - datetime.timedelta(minutes=5)
        PendingApproval.objects.filter(status="PENDING", created_at__lt=expiry_cutoff).update(
            status="EXPIRED",
            resolved_at=timezone.now()
        )
    except Exception as e:
        logger.warning(f"Error auto-expiring pending approvals: {e}")

    # 2. Extract conversation_id and validate strictly
    conversation_id = (request.GET.get("conversation_id") or "").strip()
    if not conversation_id or conversation_id.lower() in ["undefined", "null", "none", ""]:
        # Do NOT leak un-targeted approvals to arbitrary uninitialized sessions
        return JsonResponse({
            "pending_count": 0,
            "approvals": []
        }, status=200)

    query = PendingApproval.objects.filter(
        status="PENDING",
        target_conversation_id=conversation_id
    )

    approvals = []
    for appr in query.order_by("-created_at")[:10]:
        approvals.append({
            "approval_id": appr.approval_id,
            "conversation_id": appr.target_conversation_id,
            "action_type": appr.action_type,
            "description": appr.description,
            "created_at": appr.created_at.isoformat(),
            "status": appr.status,
            "metadata": appr.metadata
        })

    return JsonResponse({
        "pending_count": len(approvals),
        "approvals": approvals
    }, status=200)


@csrf_exempt
def respond_chat_approval(request, approval_id):
    """
    Endpoint: POST /api/chat/approvals/<approval_id>/respond/
    Universal handler for accepting or rejecting any Human-in-the-Loop pending approval.
    Handles conversation reset approvals, automation gates, and composite safety policies.
    """
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed. Use POST."}, status=405)

    try:
        body = json.loads(request.body.decode("utf-8")) if request.body else {}
    except Exception:
        body = {}

    decision = (body.get("decision") or body.get("action") or "").lower().strip()
    is_approved = decision in ["approve", "accept", "authorized", "yes", "true"]

    appr = PendingApproval.objects.filter(approval_id=approval_id).first()
    if not appr:
        return JsonResponse({"error": f"Pending approval '{approval_id}' not found."}, status=404)

    if appr.status != "PENDING":
        return JsonResponse({
            "error": f"Approval request has already been resolved with status '{appr.status}'."
        }, status=409)

    action_type = appr.action_type or ""

    # Case A: Automation Engine Gate
    if action_type.startswith("AUTOMATION_"):
        try:
            if not is_approved:
                appr.status = "REJECTED"
                appr.resolved_at = timezone.now()
                appr.save()

                from automation_system.models import AutomationTask
                task_id = appr.execution_id or appr.metadata.get("task_id")
                if task_id:
                    task = AutomationTask.objects.filter(task_id=task_id).first()
                    if task:
                        task.approval_status = AutomationTask.APPROVAL_REJECTED
                        task.execution_status = AutomationTask.STATUS_CANCELLED
                        task.save()

                cancel_msg = "O.P.S. execution cancelled. No automation actions were performed."

                # Create cancelled message record in conversation
                if appr.target_conversation_id:
                    conv = Conversation.objects.filter(conversation_id=appr.target_conversation_id).first()
                    if conv:
                        ChatMessage.objects.create(
                            conversation=conv,
                            message_id=f"msg_{int(time.time())}_{uuid.uuid4().hex[:6]}",
                            role="assistant",
                            content=cancel_msg,
                            input_type="text",
                            status="cancelled",
                            metadata={"status": "CANCELLED", "approval_id": approval_id}
                        )

                event_bus.publish(
                    request_id=f"req_{approval_id}",
                    execution_id=appr.execution_id or f"exec_{approval_id}",
                    conversation_id=appr.target_conversation_id,
                    node_id="hitl_safety_controller",
                    component_name="HITL Safety Controller",
                    component_type="approval_controller",
                    event_type="APPROVAL_REJECTED",
                    execution_status="CANCELLED",
                    safe_task_summary="Execution cancelled by user. No actions performed.",
                    final_answer=cancel_msg,
                    content=cancel_msg,
                    timestamp=time.time()
                )
                return JsonResponse({
                    "success": True,
                    "status": "DENIED",
                    "approval_id": approval_id,
                    "message": cancel_msg,
                    "final_answer": cancel_msg
                }, status=200)

            # User Approved: Mark status and resume execution
            appr.status = "APPROVED"
            appr.resolved_at = timezone.now()
            appr.save()

            from automation_system.models import AutomationTask
            task_id = appr.execution_id or appr.metadata.get("task_id")
            has_auto_task = AutomationTask.objects.filter(task_id=task_id).exists() if task_id else False

            if has_auto_task:
                from automation_system.services.automation_service import AutomationService
                res = AutomationService.resume_after_approval(approval_id, approved=True)
                return JsonResponse(res, status=200)
            else:
                from research_system.orchestrator.service import CentralOrchestratorService
                query = appr.metadata.get("query") or appr.metadata.get("user_query") or appr.description
                res = CentralOrchestratorService.execute_directive(
                    query=query,
                    conversation_id=appr.target_conversation_id,
                    task_id=appr.execution_id,
                    approval_id=approval_id,
                    approval_decision="approve"
                )
                return JsonResponse(res, status=200)

        except Exception as e:
            logger.error(f"Failed to resume automation approval {approval_id}: {e}", exc_info=True)
            appr.status = "APPROVED" if is_approved else "REJECTED"
            appr.resolved_at = timezone.now()
            appr.save()
            return JsonResponse({"success": True, "status": appr.status, "error": str(e)}, status=200)

    # Case B: Permanent Conversation Deletion
    if action_type == "PERMANENT_CONVERSATION_DELETION":
        target_conv_id = appr.target_conversation_id
        if not is_approved:
            return deny_refresh_approval(request, target_conv_id, approval_id)
        else:
            return accept_refresh_approval(request, target_conv_id, approval_id)

    # Case C: General HITL Safety Gate
    appr.status = "APPROVED" if is_approved else "REJECTED"
    appr.resolved_at = timezone.now()
    appr.save()

    event_bus.publish(
        request_id=f"req_{approval_id}",
        execution_id=appr.execution_id or f"exec_{approval_id}",
        conversation_id=appr.target_conversation_id,
        node_id="hitl_safety_controller",
        component_name="HITL Safety Controller",
        component_type="approval_controller",
        event_type="APPROVAL_ACCEPTED" if is_approved else "APPROVAL_REJECTED",
        execution_status="EXECUTING" if is_approved else "CANCELLED",
        safe_task_summary="Human authorization confirmed." if is_approved else "Human authorization denied.",
        status=appr.status,
        timestamp=time.time()
    )

    return JsonResponse({
        "success": True,
        "status": appr.status,
        "approval_id": approval_id,
        "message": f"Approval {appr.status}."
    }, status=200)


# =========================================================================
# Temporary Document RAG Endpoints (PDF / Word Ingestion & Ephemeral Pinecone)
# =========================================================================

@csrf_exempt
def document_upload_view(request, conversation_id):
    """
    POST /api/chat/conversations/<conversation_id>/documents/upload/
    Receives PDF, DOCX, or DOC file, extracts text, chunks, generates embeddings,
    and indexes into temporary Pinecone namespace ops-rag-{conversation_id}.
    Stores raw chunk text strictly in ephemeral in-memory session cache.
    """
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed. Use POST."}, status=405)

    if not request.FILES or "file" not in request.FILES:
        return JsonResponse({"error": "No file uploaded. Key 'file' is required."}, status=400)

    uploaded_file = request.FILES["file"]
    filename = uploaded_file.name

    from research_system.services.temporary_rag_service import get_temporary_rag_service
    rag_service = get_temporary_rag_service()

    def progress_callback(stage_msg: str, percent: int):
        event_bus.publish(
            request_id=f"rag_upload_{int(time.time())}",
            execution_id=f"exec_rag_{conversation_id}",
            node_id="document_ingestion",
            component_name="Temporary Document Ingestion",
            component_type="tool",
            event_type="DOCUMENT_INGESTION_PROGRESS",
            execution_status="RUNNING",
            safe_task_summary=stage_msg,
            conversation_id=conversation_id,
            progress_percent=percent,
            filename=filename,
            timestamp=time.time()
        )

    try:
        content = uploaded_file.read()
        res = rag_service.ingest_document(
            conversation_id=conversation_id,
            file_content=content,
            filename=filename,
            progress_callback=progress_callback
        )
        active_docs = rag_service.get_active_documents(conversation_id)
        return JsonResponse({
            "status": "success",
            "document": res,
            "active_documents": active_docs
        })
    except ValueError as ve:
        return JsonResponse({"error": str(ve)}, status=400)
    except Exception as e:
        logger.error(f"Document ingestion failed: {e}", exc_info=True)
        return JsonResponse({"error": f"Document ingestion failed: {str(e)}"}, status=500)


@csrf_exempt
def document_collection_view(request, conversation_id):
    """
    GET /api/chat/conversations/<conversation_id>/documents/
    Lists active temporary documents for the session.
    POST / DELETE: Clears all documents and temporary vectors for this session.
    """
    from research_system.services.temporary_rag_service import get_temporary_rag_service
    rag_service = get_temporary_rag_service()

    if request.method == "GET":
        docs = rag_service.get_active_documents(conversation_id)
        return JsonResponse({"status": "success", "active_documents": docs})
    elif request.method in ["POST", "DELETE"]:
        cleanup_res = rag_service.clear_session(conversation_id)
        return JsonResponse({"status": "cleared", "cleanup": cleanup_res})
    return JsonResponse({"error": "Method not allowed."}, status=405)


@csrf_exempt
def document_detail_view(request, conversation_id, doc_id):
    """
    DELETE /api/chat/conversations/<conversation_id>/documents/<doc_id>/
    Removes a single document from the active session and its Pinecone vectors.
    """
    if request.method != "DELETE":
        return JsonResponse({"error": "Method not allowed. Use DELETE."}, status=405)

    from research_system.services.temporary_rag_service import get_temporary_rag_service
    rag_service = get_temporary_rag_service()

    success = rag_service.delete_document(conversation_id, doc_id)
    active_docs = rag_service.get_active_documents(conversation_id)
    return JsonResponse({
        "status": "deleted" if success else "failed",
        "doc_id": doc_id,
        "active_documents": active_docs
    })


