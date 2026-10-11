from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q


class RoomType(models.Model):
    name = models.CharField("tên loại phòng", max_length=100, unique=True)
    description = models.TextField("mô tả", blank=True)
    capacity = models.PositiveSmallIntegerField(
        "sức chứa",
        validators=[MinValueValidator(1)],
    )
    price_per_night = models.DecimalField(
        "giá mỗi đêm",
        max_digits=12,
        decimal_places=0,
        validators=[MinValueValidator(0)],
    )
    price_per_hour = models.DecimalField(
        "giá mỗi giờ",
        max_digits=12,
        decimal_places=0,
        default=100000,
        validators=[MinValueValidator(0)],
    )
    amenities = models.JSONField("tiện ích", default=list, blank=True)
    image = models.ImageField("hình ảnh", upload_to="room_types/", blank=True)
    is_active = models.BooleanField("đang hoạt động", default=True)
    created_at = models.DateTimeField("ngày tạo", auto_now_add=True)
    updated_at = models.DateTimeField("ngày cập nhật", auto_now=True)

    class Meta:
        verbose_name = "loại phòng"
        verbose_name_plural = "loại phòng"
        ordering = ["price_per_night", "name"]
        constraints = [
            models.CheckConstraint(condition=Q(capacity__gt=0), name="room_type_capacity_gt_0"),
            models.CheckConstraint(
                condition=Q(price_per_night__gte=0),
                name="room_type_price_gte_0",
            ),
            models.CheckConstraint(
                condition=Q(price_per_hour__gte=0),
                name="room_type_hour_price_gte_0",
            ),
        ]
        indexes = [
            models.Index(fields=["is_active"], name="room_type_active_idx"),
            models.Index(fields=["capacity", "is_active"], name="room_type_cap_active_idx"),
        ]

    def __str__(self):
        return self.name


class Room(models.Model):
    class Status(models.TextChoices):
        AVAILABLE = "AVAILABLE", "Trống"
        OCCUPIED = "OCCUPIED", "Đang sử dụng"
        CLEANING = "CLEANING", "Đang dọn"
        MAINTENANCE = "MAINTENANCE", "Bảo trì"

    room_number = models.CharField("số phòng", max_length=20, unique=True)
    room_type = models.ForeignKey(
        RoomType,
        on_delete=models.PROTECT,
        related_name="rooms",
        verbose_name="loại phòng",
    )
    floor = models.IntegerField("tầng", validators=[MinValueValidator(0)])
    status = models.CharField(
        "trạng thái vận hành",
        max_length=20,
        choices=Status.choices,
        default=Status.AVAILABLE,
    )
    notes = models.TextField("ghi chú", blank=True)
    is_active = models.BooleanField("đang hoạt động", default=True)
    created_at = models.DateTimeField("ngày tạo", auto_now_add=True)
    updated_at = models.DateTimeField("ngày cập nhật", auto_now=True)

    class Meta:
        verbose_name = "phòng"
        verbose_name_plural = "phòng"
        ordering = ["floor", "room_number"]
        constraints = [models.CheckConstraint(condition=Q(floor__gte=0), name="room_floor_gte_0")]
        indexes = [
            models.Index(fields=["status", "is_active"], name="room_status_active_idx"),
            models.Index(fields=["room_type", "status"], name="room_type_status_idx"),
        ]

    def __str__(self):
        return self.room_number
