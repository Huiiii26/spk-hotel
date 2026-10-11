from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone

from apps.accounts.models import User
from apps.rooms.models import Room

from .models import Booking


BLOCKING_STATUSES = (
    Booking.Status.PENDING,
    Booking.Status.CONFIRMED,
    Booking.Status.CHECKED_IN,
    Booking.Status.CHECKED_OUT,
)

ALLOWED_TRANSITIONS = {
    Booking.Status.PENDING: {Booking.Status.CONFIRMED, Booking.Status.CANCELLED},
    Booking.Status.CONFIRMED: {Booking.Status.CHECKED_IN, Booking.Status.CANCELLED},
    Booking.Status.CHECKED_IN: {Booking.Status.CHECKED_OUT},
    Booking.Status.CHECKED_OUT: set(),
    Booking.Status.CANCELLED: set(),
}


def validate_date_range(check_in_date, check_out_date):
    if not check_in_date or not check_out_date or check_out_date <= check_in_date:
        raise ValidationError({"check_out_date": "Thời gian trả phòng phải sau thời gian nhận phòng."})


def overlapping_bookings(*, room_id, check_in_date, check_out_date):
    """Công thức: existing_in < requested_out AND existing_out > requested_in."""

    return Booking.objects.filter(
        room_id=room_id,
        status__in=BLOCKING_STATUSES,
        check_in_date__lt=check_out_date,
        check_out_date__gt=check_in_date,
    )


def find_available_rooms(
    *,
    check_in_date,
    check_out_date,
    guest_count,
    room_type=None,
    max_budget=None,
    amenities=None,
):
    validate_date_range(check_in_date, check_out_date)
    if guest_count < 1:
        raise ValidationError({"guest_count": "Số khách phải lớn hơn 0."})

    booked_room_ids = Booking.objects.filter(
        status__in=BLOCKING_STATUSES,
        check_in_date__lt=check_out_date,
        check_out_date__gt=check_in_date,
    ).values_list("room_id", flat=True)

    rooms = Room.objects.select_related("room_type").filter(
        is_active=True,
        room_type__is_active=True,
        room_type__capacity__gte=guest_count,
    ).exclude(status=Room.Status.MAINTENANCE).exclude(pk__in=booked_room_ids)

    if room_type:
        rooms = rooms.filter(room_type=room_type)
    if max_budget is not None:
        rooms = rooms.filter(room_type__price_per_night__lte=max_budget)

    requested_amenities = {item.strip().casefold() for item in (amenities or []) if item.strip()}
    if not requested_amenities:
        return list(rooms.order_by("room_type__price_per_night", "room_number"))

    result = []
    for room in rooms.order_by("room_type__price_per_night", "room_number"):
        room_amenities = {str(item).strip().casefold() for item in room.room_type.amenities}
        if requested_amenities.issubset(room_amenities):
            result.append(room)
    return result


def _validate_actor_and_customer(*, actor, customer):
    if actor.role == User.Role.CUSTOMER:
        if customer.user_id != actor.pk:
            raise PermissionDenied("Bạn chỉ được đặt phòng cho chính mình.")
        return Booking.Status.PENDING
    if actor.role in (User.Role.MANAGER, User.Role.RECEPTIONIST):
        return Booking.Status.CONFIRMED
    raise PermissionDenied("Bạn không có quyền tạo booking.")


def _ensure_receptionist(actor):
    if actor.role not in (User.Role.MANAGER, User.Role.RECEPTIONIST):
        raise PermissionDenied("Chỉ quản lý hoặc lễ tân được thực hiện thao tác này.")


def _apply_transition(booking, target_status):
    if target_status not in ALLOWED_TRANSITIONS.get(booking.status, set()):
        raise ValidationError(
            f"Không thể chuyển booking từ '{booking.get_status_display()}' sang "
            f"'{Booking.Status(target_status).label}'."
        )
    booking.status = target_status


@transaction.atomic
def create_booking(
    *,
    actor,
    customer,
    room,
    check_in_date,
    check_out_date,
    guest_count,
    notes="",
):
    """Khóa Room, kiểm tra lại lịch rồi mới ghi Booking."""

    status = _validate_actor_and_customer(actor=actor, customer=customer)
    validate_date_range(check_in_date, check_out_date)

    locked_room = (
        Room.objects.select_for_update()
        .select_related("room_type")
        .get(pk=room.pk)
    )
    errors = {}
    if not locked_room.is_active or not locked_room.room_type.is_active:
        errors["room"] = "Phòng hoặc loại phòng đã ngừng hoạt động."
    elif locked_room.status == Room.Status.MAINTENANCE:
        errors["room"] = "Phòng đang bảo trì và không thể đặt."
    if guest_count < 1:
        errors["guest_count"] = "Số khách phải lớn hơn 0."
    elif guest_count > locked_room.room_type.capacity:
        errors["guest_count"] = "Số khách vượt quá sức chứa của phòng."
    if errors:
        raise ValidationError(errors)

    if overlapping_bookings(
        room_id=locked_room.pk,
        check_in_date=check_in_date,
        check_out_date=check_out_date,
    ).exists():
        raise ValidationError({"room": "Phòng đã có booking giao với khoảng ngày này."})

    return Booking.objects.create(
        customer=customer,
        room=locked_room,
        created_by=actor,
        check_in_date=check_in_date,
        check_out_date=check_out_date,
        guest_count=guest_count,
        room_price_per_night=locked_room.room_type.price_per_night,
        room_price_per_hour=locked_room.room_type.price_per_hour,
        status=status,
        notes=notes,
    )


@transaction.atomic
def confirm_booking(*, actor, booking):
    _ensure_receptionist(actor)
    locked_booking = Booking.objects.select_for_update().get(pk=booking.pk)
    _apply_transition(locked_booking, Booking.Status.CONFIRMED)
    locked_booking.save(update_fields=["status", "updated_at"])
    return locked_booking


@transaction.atomic
def check_in_booking(*, actor, booking):
    _ensure_receptionist(actor)
    locked_booking = Booking.objects.select_for_update().get(pk=booking.pk)
    locked_room = Room.objects.select_for_update().get(pk=locked_booking.room_id)
    _apply_transition(locked_booking, Booking.Status.CHECKED_IN)
    if locked_room.status != Room.Status.AVAILABLE:
        raise ValidationError(
            {"room": f"Phòng đang ở trạng thái '{locked_room.get_status_display()}', chưa thể check-in."}
        )
    locked_booking.actual_check_in_at = timezone.now()
    locked_booking.save(update_fields=["status", "actual_check_in_at", "updated_at"])
    locked_room.status = Room.Status.OCCUPIED
    locked_room.save(update_fields=["status", "updated_at"])
    return locked_booking


@transaction.atomic
def check_out_booking(*, actor, booking):
    _ensure_receptionist(actor)
    locked_booking = Booking.objects.select_for_update().get(pk=booking.pk)
    locked_room = Room.objects.select_for_update().get(pk=locked_booking.room_id)
    _apply_transition(locked_booking, Booking.Status.CHECKED_OUT)
    if locked_room.status != Room.Status.OCCUPIED:
        raise ValidationError(
            {"room": f"Phòng đang ở trạng thái '{locked_room.get_status_display()}', chưa thể check-out."}
        )
    locked_booking.actual_check_out_at = timezone.now()
    locked_booking.save(update_fields=["status", "actual_check_out_at", "updated_at"])
    locked_room.status = Room.Status.CLEANING
    locked_room.save(update_fields=["status", "updated_at"])
    from apps.billing.services import create_or_update_invoice

    create_or_update_invoice(booking=locked_booking)
    return locked_booking


@transaction.atomic
def cancel_booking(*, actor, booking, reason=""):
    locked_booking = Booking.objects.select_for_update().get(pk=booking.pk)
    if actor.role == User.Role.CUSTOMER:
        if locked_booking.customer.user_id != actor.pk:
            raise PermissionDenied("Bạn chỉ được hủy booking của chính mình.")
    elif actor.role not in (User.Role.MANAGER, User.Role.RECEPTIONIST):
        raise PermissionDenied("Bạn không có quyền hủy booking.")

    _apply_transition(locked_booking, Booking.Status.CANCELLED)
    locked_booking.cancelled_at = timezone.now()
    locked_booking.cancellation_reason = reason.strip()
    locked_booking.save(
        update_fields=["status", "cancelled_at", "cancellation_reason", "updated_at"]
    )
    return locked_booking


@transaction.atomic
def mark_room_available_after_cleaning(*, actor, room):
    _ensure_receptionist(actor)
    locked_room = Room.objects.select_for_update().get(pk=room.pk)
    if locked_room.status != Room.Status.CLEANING:
        raise ValidationError("Chỉ phòng đang dọn mới có thể chuyển thành trống.")
    locked_room.status = Room.Status.AVAILABLE
    locked_room.save(update_fields=["status", "updated_at"])
    return locked_room
