from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q
from django.utils import timezone


class Invoice(models.Model):
    class Status(models.TextChoices):
        UNPAID = "UNPAID", "Chưa thanh toán"
        PARTIALLY_PAID = "PARTIALLY_PAID", "Thanh toán một phần"
        PAID = "PAID", "Đã thanh toán"

    booking = models.OneToOneField("bookings.Booking", on_delete=models.PROTECT, related_name="invoice")
    room_amount = models.DecimalField("tiền phòng", max_digits=14, decimal_places=0, default=0)
    service_amount = models.DecimalField("tiền dịch vụ", max_digits=14, decimal_places=0, default=0)
    surcharge = models.DecimalField("phụ thu", max_digits=14, decimal_places=0, default=0, validators=[MinValueValidator(0)])
    discount = models.DecimalField("giảm giá", max_digits=14, decimal_places=0, default=0, validators=[MinValueValidator(0)])
    total_amount = models.DecimalField("tổng tiền", max_digits=14, decimal_places=0, default=0)
    paid_amount = models.DecimalField("đã thanh toán", max_digits=14, decimal_places=0, default=0)
    balance_due = models.DecimalField("còn thiếu", max_digits=14, decimal_places=0, default=0)
    status = models.CharField("trạng thái", max_length=20, choices=Status.choices, default=Status.UNPAID)
    finalized_at = models.DateTimeField("thời gian chốt", null=True, blank=True)
    created_at = models.DateTimeField("ngày tạo", auto_now_add=True)
    updated_at = models.DateTimeField("ngày cập nhật", auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(condition=Q(room_amount__gte=0), name="invoice_room_gte_0"),
            models.CheckConstraint(condition=Q(service_amount__gte=0), name="invoice_service_gte_0"),
            models.CheckConstraint(condition=Q(surcharge__gte=0), name="invoice_surcharge_gte_0"),
            models.CheckConstraint(condition=Q(discount__gte=0), name="invoice_discount_gte_0"),
            models.CheckConstraint(condition=Q(total_amount__gte=0), name="invoice_total_gte_0"),
            models.CheckConstraint(condition=Q(paid_amount__gte=0), name="invoice_paid_gte_0"),
            models.CheckConstraint(condition=Q(balance_due__gte=0), name="invoice_balance_gte_0"),
        ]
        indexes = [
            models.Index(fields=["status", "created_at"], name="invoice_status_created_idx"),
            models.Index(fields=["finalized_at"], name="invoice_finalized_idx"),
        ]

    def __str__(self):
        return f"HĐ {self.pk or 'mới'} - {self.booking.booking_code}"


class Payment(models.Model):
    class Method(models.TextChoices):
        CASH = "CASH", "Tiền mặt"
        BANK_TRANSFER = "BANK_TRANSFER", "Chuyển khoản"
        CARD = "CARD", "Thẻ"

    invoice = models.ForeignKey(Invoice, on_delete=models.PROTECT, related_name="payments")
    amount = models.DecimalField("số tiền", max_digits=14, decimal_places=0, validators=[MinValueValidator(1)])
    method = models.CharField("hình thức", max_length=20, choices=Method.choices)
    paid_at = models.DateTimeField("thời gian thanh toán", default=timezone.now)
    recorded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="recorded_payments")
    reference = models.CharField("mã tham chiếu", max_length=100, blank=True)
    notes = models.TextField("ghi chú", blank=True)
    created_at = models.DateTimeField("ngày tạo", auto_now_add=True)
    updated_at = models.DateTimeField("ngày cập nhật", auto_now=True)

    class Meta:
        ordering = ["-paid_at", "-created_at"]
        constraints = [models.CheckConstraint(condition=Q(amount__gt=0), name="payment_amount_gt_0")]
        indexes = [
            models.Index(fields=["invoice", "paid_at"], name="payment_invoice_date_idx"),
            models.Index(fields=["method", "paid_at"], name="payment_method_date_idx"),
        ]

    def __str__(self):
        return f"{self.get_method_display()} - {self.amount}"
