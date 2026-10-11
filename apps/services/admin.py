from django.contrib import admin

from .models import BookingService, Service

admin.site.register(Service)
admin.site.register(BookingService)
