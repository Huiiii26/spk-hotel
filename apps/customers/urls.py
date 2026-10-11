from django.urls import path

from . import views

app_name = "customers"
urlpatterns = [
    path("", views.overview, name="overview"),
    path("profile/", views.profile_update, name="profile"),
]
