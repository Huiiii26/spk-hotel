from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q
from django.utils import timezone


class Service(models.Model):
    name = models.CharField("tên dịch vụ", max_length=120, unique=True)
    description = models.TextField("mô tả", blank=True)
    unit_price = models.DecimalField("đơn giá", max_digits=12, decimal_places=0, validators=[MinValueValidator(0)])
    unit = models.CharField("đơn vị tính", max_length=30)
    is_active = models.BooleanField("đang hoạt động", default=True)
    created_at = models.DateTimeField("ngày tạo", auto_now_add=True)
    updated_at = models.DateTimeField("ngày cập nhật", auto_now=True)

    class Meta:
        ordering = ["name"]
        constraints = [models.CheckConstraint(condition=Q(unit_price__gte=0), name="service_price_gte_0")]
        indexes = [models.Index(fields=["is_active", "name"], name="service_active_name_idx")]

    def __str__(self):
        return self.name


class BookingService(models.Model):
    booking = models.ForeignKey("bookings.Booking", on_delete=models.PROTECT, related_name="used_services")
    service = models.ForeignKey(Service, on_delete=models.PROTECT, related_name="booking_usages")
    quantity = models.DecimalField("số lượng", max_digits=8, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))])
    unit_price = models.DecimalField("đơn giá lúc sử dụng", max_digits=12, decimal_places=0, validators=[MinValueValidator(0)])
    used_at = models.DateField("ngày sử dụng", default=timezone.localdate)
    line_total = models.DecimalField("thành tiền", max_digits=14, decimal_places=0, validators=[MinValueValidator(0)])
    recorded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="recorded_services")
    created_at = models.DateTimeField("ngày tạo", auto_now_add=True)
    updated_at = models.DateTimeField("ngày cập nhật", auto_now=True)

    class Meta:
        ordering = ["-used_at", "-created_at"]
        constraints = [
            models.CheckConstraint(condition=Q(quantity__gt=0), name="booking_service_qty_gt_0"),
            models.CheckConstraint(condition=Q(unit_price__gte=0), name="booking_service_price_gte_0"),
            models.CheckConstraint(condition=Q(line_total__gte=0), name="booking_service_total_gte_0"),
        ]
        indexes = [
            models.Index(fields=["booking", "used_at"], name="booking_service_date_idx"),
            models.Index(fields=["service"], name="booking_service_service_idx"),
        ]

    def __str__(self):
        return f"{self.booking.booking_code} - {self.service.name}"
