from django.contrib import admin

from .models import Customer


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ("full_name", "email", "phone", "user", "created_at")
    search_fields = ("full_name", "email", "phone", "identity_document")
    readonly_fields = ("created_at", "updated_at")
