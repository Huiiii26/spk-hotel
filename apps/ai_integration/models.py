from django.conf import settings
from django.db import models


class AILog(models.Model):
    class Feature(models.TextChoices):
        ROOM_ADVISOR = "ROOM_ADVISOR", "Tư vấn phòng"
        EMAIL = "EMAIL", "Sinh email"
        REPORT = "REPORT", "Nhận xét báo cáo"

    class Status(models.TextChoices):
        SUCCESS = "SUCCESS", "Thành công"
        FALLBACK = "FALLBACK", "Dùng phương án dự phòng"
        INVALID = "INVALID", "Kết quả không hợp lệ"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="ai_logs")
    feature = models.CharField(max_length=30, choices=Feature.choices)
    status = models.CharField(max_length=20, choices=Status.choices)
    request_summary = models.JSONField(default=dict, blank=True)
    response_summary = models.JSONField(default=dict, blank=True)
    error_code = models.CharField(max_length=50, blank=True)
    duration_ms = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["feature", "status", "created_at"], name="ai_feature_status_idx")]


class EmailDraft(models.Model):
    class EmailType(models.TextChoices):
        CONFIRMATION = "CONFIRMATION", "Xác nhận đặt phòng"
        CANCELLATION = "CANCELLATION", "Thông báo hủy phòng"
        PAYMENT_REMINDER = "PAYMENT_REMINDER", "Nhắc thanh toán"

    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Bản nháp"
        APPROVED = "APPROVED", "Đã duyệt"
        SIMULATED_SENT = "SIMULATED_SENT", "Đã mô phỏng gửi"
        CANCELLED = "CANCELLED", "Đã hủy"

    booking = models.ForeignKey("bookings.Booking", on_delete=models.PROTECT, related_name="email_drafts")
    email_type = models.CharField(max_length=30, choices=EmailType.choices)
    recipient_email = models.EmailField(blank=True)
    subject = models.CharField(max_length=200)
    body = models.TextField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    generated_by_ai = models.BooleanField(default=False)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="created_email_drafts")
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True, related_name="approved_email_drafts")
    approved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["email_type", "status", "created_at"], name="email_type_status_idx")]

# Create your models here.
