from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone


class UserManager(BaseUserManager):
    """Manager tạo tài khoản sử dụng email thay cho username."""

    use_in_migrations = True

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email là bắt buộc.")
        email = self.normalize_email(email).lower()
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("role", User.Role.MANAGER)
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser phải có is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser phải có is_superuser=True.")
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    class Role(models.TextChoices):
        MANAGER = "MANAGER", "Quản lý"
        RECEPTIONIST = "RECEPTIONIST", "Lễ tân"
        ACCOUNTANT = "ACCOUNTANT", "Kế toán"
        CUSTOMER = "CUSTOMER", "Khách hàng"

    email = models.EmailField("email", unique=True)
    full_name = models.CharField("họ tên", max_length=150)
    phone = models.CharField("số điện thoại", max_length=20, blank=True)
    role = models.CharField(
        "vai trò",
        max_length=20,
        choices=Role.choices,
        default=Role.CUSTOMER,
        db_index=True,
    )
    is_active = models.BooleanField("đang hoạt động", default=True)
    is_staff = models.BooleanField("quyền vào Django Admin", default=False)
    created_at = models.DateTimeField("ngày tạo", default=timezone.now, editable=False)
    updated_at = models.DateTimeField("ngày cập nhật", auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["full_name"]

    class Meta:
        verbose_name = "tài khoản"
        verbose_name_plural = "tài khoản"
        indexes = [models.Index(fields=["role", "is_active"], name="user_role_active_idx")]

    def save(self, *args, **kwargs):
        self.email = self.__class__.objects.normalize_email(self.email).lower()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.full_name} ({self.email})"
