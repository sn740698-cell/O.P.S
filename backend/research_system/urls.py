from django.urls import path
from research_system import views

urlpatterns = [
    # Continuous Chat & Conversation Lifecycle (Module: Chat Management & Lifecycle)
    path("chat/conversations/", views.conversations_collection, name="chat_conversations"),
    path("chat/conversations/active/", views.get_active_conversation, name="chat_active_conversation"),
    path("chat/conversations/<str:conversation_id>/", views.conversation_detail, name="chat_conversation_detail"),
    path("chat/conversations/<str:conversation_id>/messages/", views.conversation_messages, name="chat_conversation_messages"),
    path("chat/conversations/<str:conversation_id>/cancel/", views.conversation_cancel, name="chat_conversation_cancel"),
    path("chat/conversations/<str:conversation_id>/events/", views.conversation_events, name="chat_conversation_events"),

    # Temporary Document-Based RAG Endpoints
    path("chat/conversations/<str:conversation_id>/documents/upload/", views.document_upload_view, name="chat_document_upload"),
    path("chat/conversations/<str:conversation_id>/documents/", views.document_collection_view, name="chat_document_collection"),
    path("chat/conversations/<str:conversation_id>/documents/<str:doc_id>/", views.document_detail_view, name="chat_document_detail"),
    path("chat/conversations/<str:conversation_id>/documents/clear/", views.document_collection_view, name="chat_document_clear"),

    # Human-in-the-Loop (HITL) Approval Endpoints
    path("chat/approvals/pending/", views.get_pending_approvals, name="chat_pending_approvals"),
    path("chat/approvals/<str:approval_id>/respond/", views.respond_chat_approval, name="chat_approval_respond"),
    path("chat/conversations/<str:conversation_id>/refresh-approval/", views.create_refresh_approval, name="chat_refresh_approval"),
    path("chat/conversations/<str:conversation_id>/refresh-approval/<str:approval_id>/accept/", views.accept_refresh_approval, name="chat_refresh_approval_accept"),
    path("chat/conversations/<str:conversation_id>/refresh-approval/<str:approval_id>/deny/", views.deny_refresh_approval, name="chat_refresh_approval_deny"),

    # Primary Web Research Execution
    path("research/execute/", views.execute_research, name="research_execute"),
    path("research/stream/", views.stream_research_events, name="research_stream"),
    path("research/history/", views.get_session_history, name="research_history"),

    # Cockpit Compatible Endpoints
    path("ops/execute/", views.execute_research, name="ops_execute"),
    path("ops/session/refresh/", views.refresh_session, name="ops_session_refresh"),
    path("ops/session/stop/", views.stop_session, name="ops_session_stop"),
    path("agent/run/", views.execute_research, name="agent_run"),
    path("health/", views.health_check, name="health_check"),
    path("audit/logs/", views.audit_logs, name="audit_logs"),
]
