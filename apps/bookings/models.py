import math
import uuid
from datetime import datetime, time
from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q
from django.utils import timezone


def generate_booking_code():
    """Sinh mã ngắn, không chứa dữ liệu cá nhân của khách."""

    return f"BK{uuid.uuid4().hex[:10].upper()}"


class Booking(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Chờ xác nhận"
        CONFIRMED = "CONFIRMED", "Đã xác nhận"
        CHECKED_IN = "CHECKED_IN", "Đã nhận phòng"
        CHECKED_OUT = "CHECKED_OUT", "Đã trả phòng"
        CANCELLED = "CANCELLED", "Đã hủy"

    booking_code = models.CharField("mã booking", max_length=20, unique=True, default=generate_booking_code, editable=False)
    customer = models.ForeignKey("customers.Customer", on_delete=models.PROTECT, related_name="bookings", verbose_name="khách hàng")
    room = models.ForeignKey("rooms.Room", on_delete=models.PROTECT, related_name="bookings", verbose_name="phòng")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_bookings",
        verbose_name="người tạo",
    )
    check_in_date = models.DateTimeField("ngày, giờ nhận phòng")
    check_out_date = models.DateTimeField("ngày, giờ trả phòng")
    guest_count = models.PositiveSmallIntegerField("số khách", validators=[MinValueValidator(1)])
    room_price_per_night = models.DecimalField(
        "giá phòng mỗi đêm lúc đặt",
        max_digits=12,
        decimal_places=0,
        validators=[MinValueValidator(0)],
    )
    room_price_per_hour = models.DecimalField(
        "giá phòng mỗi giờ lúc đặt",
        max_digits=12,
        decimal_places=0,
        default=100000,
        validators=[MinValueValidator(0)],
    )
    status = models.CharField("trạng thái", max_length=20, choices=Status.choices, default=Status.PENDING)
    actual_check_in_at = models.DateTimeField("thời gian nhận phòng thực tế", null=True, blank=True)
    actual_check_out_at = models.DateTimeField("thời gian trả phòng thực tế", null=True, blank=True)
    cancelled_at = models.DateTimeField("thời gian hủy", null=True, blank=True)
    cancellation_reason = models.CharField("lý do hủy", max_length=255, blank=True)
    notes = models.TextField("ghi chú", blank=True)
    created_at = models.DateTimeField("ngày tạo", auto_now_add=True)
    updated_at = models.DateTimeField("ngày cập nhật", auto_now=True)

    class Meta:
        verbose_name = "booking"
        verbose_name_plural = "booking"
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(
                condition=Q(check_out_date__gt=models.F("check_in_date")),
                name="booking_checkout_after_checkin",
            ),
            models.CheckConstraint(condition=Q(guest_count__gt=0), name="booking_guests_gt_0"),
            models.CheckConstraint(condition=Q(room_price_per_night__gte=0), name="booking_room_price_gte_0"),
        ]
        indexes = [
            models.Index(fields=["room", "check_in_date", "check_out_date"], name="booking_room_dates_idx"),
            models.Index(fields=["status", "check_in_date"], name="booking_status_date_idx"),
            models.Index(fields=["customer", "status"], name="booking_customer_status_idx"),
            models.Index(fields=["booking_code"], name="booking_code_idx"),
        ]

    @property
    def number_of_nights(self):
        return self.number_of_days

    @staticmethod
    def _as_datetime(value):
        if isinstance(value, datetime):
            return timezone.localtime(value) if timezone.is_aware(value) else value
        return datetime.combine(value, time.min)

    @property
    def number_of_days(self):
        check_in = self._as_datetime(self.check_in_date)
        check_out = self._as_datetime(self.check_out_date)
        return max((check_out.date() - check_in.date()).days, 1)

    @property
    def billable_hours(self):
        check_in = self._as_datetime(self.check_in_date)
        check_out = self._as_datetime(self.check_out_date)
        return max(math.ceil((check_out - check_in).total_seconds() / 3600), 1)

    @property
    def is_hourly(self):
        check_in = self._as_datetime(self.check_in_date)
        check_out = self._as_datetime(self.check_out_date)
        return check_in.date() == check_out.date()

    @property
    def billing_mode_display(self):
        return "Theo giờ" if self.is_hourly else "Theo ngày"

    @property
    def billable_units(self):
        return self.billable_hours if self.is_hourly else self.number_of_days

    @property
    def room_charge(self):
        price = self.room_price_per_hour if self.is_hourly else self.room_price_per_night
        return Decimal(self.billable_units) * price

    def clean(self):
        super().clean()
        errors = {}
        if self.check_in_date and self.check_out_date and self.check_out_date <= self.check_in_date:
            errors["check_out_date"] = "Thời gian trả phòng phải sau thời gian nhận phòng."
        if self.room_id and self.guest_count and self.guest_count > self.room.room_type.capacity:
            errors["guest_count"] = "Số khách vượt quá sức chứa của loại phòng."
        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return f"{self.booking_code} - Phòng {self.room.room_number}"
