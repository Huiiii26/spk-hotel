from django.contrib import admin

from .models import Room, RoomType


@admin.register(RoomType)
class RoomTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "capacity", "price_per_night", "is_active")
    list_filter = ("is_active", "capacity")
    search_fields = ("name", "description")


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ("room_number", "room_type", "floor", "status", "is_active")
    list_filter = ("status", "is_active", "room_type", "floor")
    search_fields = ("room_number", "notes")
    list_select_related = ("room_type",)
