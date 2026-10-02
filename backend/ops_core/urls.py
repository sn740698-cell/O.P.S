from django.urls import path
from ops_core.views import (
    HealthCheckView,
    IntentRouterView,
    PlanReasoningView,
    CodeSynthesizerView,
    OrchestrationView,
    WebScraperView,
    AutomationDispatcherView,
    WisprVoiceStatusView,
    WisprVoiceToggleView,
    WisprVoiceTranscriptView,
    ExecutionAuditLogListView,
    PermissionRequestListView,
    PermissionPendingListView,
    PermissionResolveView,
    SafetyPolicyRuleListView,
    RAGQueryView,
    RAGIndexDirectoryView,
    RAGStatsView,
    SessionMemoryView,
    ChatbotVectorMemoryView,
    AgentRunWorkflowView,
    IntelligenceEscalationView,
    VisionScreenshotView,
    VisionAnalyzeView,
    VoiceSynthesizeView,
    VoiceTranscribeView,
    MobilePairingGenerateView,
    MobilePairingVerifyView,
    MobileDeviceListView,
    MobilePermissionResolveView,
    MobileEmergencyHaltView,
    MobileRemoteDispatchView,
    MobileCameraStreamView,
    UserWorkstationMemoryListView,
    UserWorkstationMemoryDetailView,
    UserWorkstationMemoryExecuteView
)

urlpatterns = [
    path('health/', HealthCheckView.as_view(), name='health_check'),
    path('router/', IntentRouterView.as_view(), name='intent_router'),
    path('plan/', PlanReasoningView.as_view(), name='plan_reasoning'),
    path('coding/', CodeSynthesizerView.as_view(), name='code_synthesizer'),
    path('orchestrate/', OrchestrationView.as_view(), name='orchestrate_pipeline'),
    path('scrape/', WebScraperView.as_view(), name='web_scraper'),
    path('automation/', AutomationDispatcherView.as_view(), name='automation_dispatcher'),
    
    # Wispr Flow Voice Integration Endpoints
    path('voice/status/', WisprVoiceStatusView.as_view(), name='wispr_voice_status'),
    path('voice/toggle/', WisprVoiceToggleView.as_view(), name='wispr_voice_toggle'),
    path('voice/transcript/', WisprVoiceTranscriptView.as_view(), name='wispr_voice_transcript'),
    path('voice/synthesize/', VoiceSynthesizeView.as_view(), name='voice_synthesize'),
    path('voice/transcribe/', VoiceTranscribeView.as_view(), name='voice_transcribe'),

    # Multimodal Vision Endpoints
    path('vision/screenshot/', VisionScreenshotView.as_view(), name='vision_screenshot'),
    path('vision/analyze/', VisionAnalyzeView.as_view(), name='vision_analyze'),

    # Security & Audit Endpoints
    path('audit/logs/', ExecutionAuditLogListView.as_view(), name='audit_logs'),
    path('permissions/history/', PermissionRequestListView.as_view(), name='permission_history'),
    path('permissions/pending/', PermissionPendingListView.as_view(), name='permission_pending'),
    path('permissions/resolve/', PermissionResolveView.as_view(), name='permission_resolve'),
    path('safety/rules/', SafetyPolicyRuleListView.as_view(), name='safety_rules'),

    # Vector RAG & Memory Endpoints
    path('rag/query/', RAGQueryView.as_view(), name='rag_query'),
    path('rag/index/', RAGIndexDirectoryView.as_view(), name='rag_index'),
    path('rag/stats/', RAGStatsView.as_view(), name='rag_stats'),
    path('memory/', SessionMemoryView.as_view(), name='session_memory'),
    path('memory/chatbot-vector/', ChatbotVectorMemoryView.as_view(), name='chatbot_vector_memory'),

    # LangGraph Multi-Agent Orchestration
    path('agent/run/', AgentRunWorkflowView.as_view(), name='agent_run_workflow'),

    # 7-Tier Intelligence Escalation
    path('intelligence/escalate/', IntelligenceEscalationView.as_view(), name='intelligence_escalate'),

    # Mobile Companion Sync & Remote Control (Iteration 7)
    path('mobile/pairing/generate/', MobilePairingGenerateView.as_view(), name='mobile_pairing_generate'),
    path('mobile/pairing/verify/', MobilePairingVerifyView.as_view(), name='mobile_pairing_verify'),
    path('mobile/devices/', MobileDeviceListView.as_view(), name='mobile_devices_list'),
    path('mobile/devices/<str:device_id>/', MobileDeviceListView.as_view(), name='mobile_device_detail'),
    path('mobile/permission/resolve/', MobilePermissionResolveView.as_view(), name='mobile_permission_resolve'),
    path('mobile/emergency-halt/', MobileEmergencyHaltView.as_view(), name='mobile_emergency_halt'),
    path('mobile/dispatch/', MobileRemoteDispatchView.as_view(), name='mobile_remote_dispatch'),
    path('mobile/camera-stream/', MobileCameraStreamView.as_view(), name='mobile_camera_stream'),

    # Personal Workstation Memory (PostgreSQL) Endpoints
    path('workstation-memory/', UserWorkstationMemoryListView.as_view(), name='workstation_memory_list'),
    path('workstation-memory/<uuid:memory_id>/', UserWorkstationMemoryDetailView.as_view(), name='workstation_memory_detail'),
    path('workstation-memory/execute/', UserWorkstationMemoryExecuteView.as_view(), name='workstation_memory_execute'),
]

