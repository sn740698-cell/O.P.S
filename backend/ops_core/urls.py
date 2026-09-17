from django.urls import path
from ops_core.views import (
    HealthCheckView,
    IntentRouterView,
    PlanReasoningView,
    CodeSynthesizerView,
    OrchestrationView,
    WebScraperView,
    AutomationDispatcherView
)

urlpatterns = [
    path('health/', HealthCheckView.as_view(), name='health_check'),
    path('router/', IntentRouterView.as_view(), name='intent_router'),
    path('plan/', PlanReasoningView.as_view(), name='plan_reasoning'),
    path('coding/', CodeSynthesizerView.as_view(), name='code_synthesizer'),
    path('orchestrate/', OrchestrationView.as_view(), name='orchestrate_pipeline'),
    path('scrape/', WebScraperView.as_view(), name='web_scraper'),
    path('automation/', AutomationDispatcherView.as_view(), name='automation_dispatcher'),
]
