from django.urls import path

from . import views

app_name = "services-staff"
urlpatterns = [
    path("services/", views.service_list, name="list"),
    path("services/create/", views.service_create, name="create"),
    path("services/<int:pk>/edit/", views.service_update, name="update"),
    path("bookings/<int:booking_id>/services/add/", views.booking_service_add, name="booking-service-add"),
]
