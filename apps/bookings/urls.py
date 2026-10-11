from django.urls import path

from . import views

app_name = "bookings"
urlpatterns = [path("search/", views.availability_search, name="availability-search")]
