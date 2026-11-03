from django.urls import path, include

urlpatterns = [
    path("api/automation/", include("automation_system.urls")),
    path("api/v1/automation/", include("automation_system.urls")),
    path("api/v1/", include("research_system.urls")),
    path("api/", include("research_system.urls")),
]
