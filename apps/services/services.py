from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction

from apps.accounts.models import User
from apps.bookings.models import Booking

from .models import BookingService


@transaction.atomic
def save_service_catalog(*, actor, form):
    if actor.role != User.Role.MANAGER:
        raise PermissionDenied("Chỉ quản lý được thay đổi danh mục dịch vụ.")
    return form.save()


@transaction.atomic
def add_booking_service(*, actor, booking, service, quantity, used_at):
    if actor.role not in (User.Role.MANAGER, User.Role.RECEPTIONIST):
        raise PermissionDenied("Chỉ quản lý hoặc lễ tân được ghi nhận dịch vụ khách sử dụng.")
    locked_booking = Booking.objects.select_for_update().get(pk=booking.pk)
    if locked_booking.status != Booking.Status.CHECKED_IN:
        raise ValidationError("Chỉ được ghi dịch vụ khi khách đang lưu trú.")
    if not service.is_active:
        raise ValidationError("Dịch vụ đã ngừng hoạt động.")
    if quantity <= 0:
        raise ValidationError("Số lượng phải lớn hơn 0.")
    unit_price = service.unit_price
    return BookingService.objects.create(
        booking=locked_booking,
        service=service,
        quantity=quantity,
        unit_price=unit_price,
        used_at=used_at,
        line_total=quantity * unit_price,
        recorded_by=actor,
    )
