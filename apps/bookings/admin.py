from django.contrib import admin

from .models import Booking


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ("booking_code", "customer", "room", "check_in_date", "check_out_date", "status")
    list_filter = ("status", "check_in_date", "room__room_type")
    search_fields = ("booking_code", "customer__full_name", "room__room_number")
    readonly_fields = ("booking_code", "room_price_per_night", "created_at", "updated_at")
