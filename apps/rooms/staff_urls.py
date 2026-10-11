from django.urls import path

from . import views


app_name = "rooms-staff"

urlpatterns = [
    path("rooms/", views.room_list, name="room-list"),
    path("rooms/create/", views.room_create, name="room-create"),
    path("rooms/<int:pk>/edit/", views.room_update, name="room-update"),
    path("room-types/", views.room_type_list, name="room-type-list"),
    path("room-types/create/", views.room_type_create, name="room-type-create"),
    path("room-types/<int:pk>/edit/", views.room_type_update, name="room-type-update"),
]
