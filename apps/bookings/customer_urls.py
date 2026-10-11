from django.urls import path

from . import views

app_name = "customer-bookings"
urlpatterns = [
    path("bookings/", views.customer_booking_list, name="list"),
    path("bookings/create/", views.customer_booking_create, name="create"),
    path("bookings/<int:pk>/cancel/", views.customer_booking_cancel, name="cancel"),
    path("bookings/<int:pk>/", views.customer_booking_detail, name="detail"),
]
