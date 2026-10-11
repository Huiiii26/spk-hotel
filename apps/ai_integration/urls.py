from django.urls import path

from . import views

app_name = "ai-integration"
urlpatterns = [
    path("room-advisor/", views.room_advisor, name="room-advisor"),
    path("email/<int:booking_id>/", views.email_generate, name="email-generate"),
    path("email-drafts/<int:pk>/", views.email_review, name="email-review"),
    path("email-drafts/<int:pk>/cancel/", views.email_cancel, name="email-cancel"),
    path("reports/", views.ai_report, name="report"),
    path("logs/", views.ai_log_list, name="logs"),
]
