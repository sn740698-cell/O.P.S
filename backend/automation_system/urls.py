from django.urls import path
from automation_system import views

urlpatterns = [
    path("status/", views.automation_status, name="automation_status"),
    path("execute/", views.execute_automation, name="automation_execute"),
    path("plan/", views.plan_automation, name="automation_plan"),
    path("tasks/<str:task_id>/", views.task_detail, name="automation_task_detail"),
    path("tasks/<str:task_id>/cancel/", views.task_detail, name="automation_task_cancel"),
    path("approvals/<str:approval_id>/respond/", views.respond_approval, name="automation_approval_respond"),
]
