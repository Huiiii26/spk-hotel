from django.conf import settings
from django.db import models


class Customer(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="customer_profile",
        verbose_name="tài khoản",
    )
    full_name = models.CharField("họ tên", max_length=150)
    email = models.EmailField("email", blank=True)
    phone = models.CharField("số điện thoại", max_length=20, blank=True)
    address = models.CharField("địa chỉ", max_length=255, blank=True)
    date_of_birth = models.DateField("ngày sinh", null=True, blank=True)
    identity_document = models.CharField(
        "CCCD hoặc hộ chiếu",
        max_length=50,
        blank=True,
        help_text="Không được gửi trường này cho AI.",
    )
    notes = models.TextField("ghi chú", blank=True)
    created_at = models.DateTimeField("ngày tạo", auto_now_add=True)
    updated_at = models.DateTimeField("ngày cập nhật", auto_now=True)

    class Meta:
        verbose_name = "khách hàng"
        verbose_name_plural = "khách hàng"
        indexes = [
            models.Index(fields=["phone"], name="customer_phone_idx"),
            models.Index(fields=["email"], name="customer_email_idx"),
        ]

    def __str__(self):
        return self.full_name
