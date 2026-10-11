from django.urls import path

from . import views

app_name = "bookings-staff"
urlpatterns = [
    path("bookings/", views.staff_booking_list, name="list"),
    path("bookings/create/", views.staff_booking_create, name="create"),
    path("bookings/<int:pk>/confirm/", views.staff_booking_confirm, name="confirm"),
    path("bookings/<int:pk>/check-in/", views.staff_booking_check_in, name="check-in"),
    path("bookings/<int:pk>/check-out/", views.staff_booking_check_out, name="check-out"),
    path("bookings/<int:pk>/cancel/", views.staff_booking_cancel, name="cancel"),
    path("bookings/<int:pk>/", views.staff_booking_detail, name="detail"),
    path("calendar/", views.room_calendar, name="calendar"),
    path("rooms/<int:pk>/mark-available/", views.room_mark_available, name="room-mark-available"),
]
