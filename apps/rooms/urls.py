from django.urls import path

from . import views

app_name = "rooms"
urlpatterns = [
    path("types/", views.public_room_type_list, name="public-room-type-list"),
    path("types/<int:pk>/", views.public_room_type_detail, name="public-room-type-detail"),
]
