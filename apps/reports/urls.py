from django.urls import path

from . import views

app_name = "reports-staff"
urlpatterns = [path("reports/", views.report_dashboard, name="dashboard")]
