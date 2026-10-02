"""
O.P.S. WebSocket Routing Configuration
Maps WebSocket URLs to corresponding Django Channels consumers.
"""

from django.urls import re_path
from ops_core import consumers

websocket_urlpatterns = [
    re_path(r'^ws/agent/?$', consumers.AgentOrchestrationConsumer.as_asgi()),
    re_path(r'^ws/permissions/?$', consumers.PermissionConsumer.as_asgi()),
    re_path(r'^ws/terminal/?$', consumers.TerminalOutputConsumer.as_asgi()),
    re_path(r'^ws/voice/?$', consumers.VoiceStreamConsumer.as_asgi()),
    re_path(r'^ws/mobile/?$', consumers.MobileSyncConsumer.as_asgi()),
]

