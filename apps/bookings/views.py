from django.contrib import messages
from django.core.exceptions import ValidationError
from datetime import timedelta

from django.db.models import Prefetch, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from apps.accounts.models import User
from apps.accounts.permissions import role_required
from apps.customers.models import Customer
from apps.rooms.models import Room

from .forms import (
    AvailabilitySearchForm,
    CalendarFilterForm,
    CancellationForm,
    CustomerBookingForm,
    ReceptionistBookingForm,
    attach_service_error,
)
from .models import Booking
from .services import (
    cancel_booking,
    check_in_booking,
    check_out_booking,
    confirm_booking,
    create_booking,
    find_available_rooms,
    mark_room_available_after_cleaning,
)


def availability_search(request):
    form = AvailabilitySearchForm(request.GET or None)
    rooms = []
    searched = bool(request.GET)
    if searched and form.is_valid():
        rooms = find_available_rooms(
            check_in_date=form.cleaned_data["check_in_date"],
            check_out_date=form.cleaned_data["check_out_date"],
            guest_count=form.cleaned_data["guest_count"],
            room_type=form.cleaned_data.get("room_type"),
            max_budget=form.cleaned_data.get("max_budget"),
            amenities=form.amenity_list(),
        )
    return render(request, "bookings/availability_search.html", {"form": form, "rooms": rooms, "searched": searched})


@role_required(User.Role.CUSTOMER)
def customer_booking_list(request):
    bookings = Booking.objects.select_related("room", "room__room_type").filter(customer__user=request.user)
    return render(request, "bookings/customer_booking_list.html", {"bookings": bookings})


@role_required(User.Role.CUSTOMER)
def customer_booking_detail(request, pk):
    booking = get_object_or_404(
        Booking.objects.select_related("customer", "room", "room__room_type").prefetch_related("used_services__service"),
        pk=pk,
        customer__user=request.user,
    )
    return render(request, "bookings/booking_detail.html", {"booking": booking})


def _booking_initial(request):
    return {
        "room": request.GET.get("room"),
        "check_in_date": request.GET.get("check_in_date"),
        "check_out_date": request.GET.get("check_out_date"),
        "guest_count": request.GET.get("guest_count"),
    }


@role_required(User.Role.CUSTOMER)
def customer_booking_create(request):
    customer = get_object_or_404(Customer, user=request.user)
    form = CustomerBookingForm(request.POST or None, initial=_booking_initial(request))
    if request.method == "POST" and form.is_valid():
        try:
            booking = create_booking(
                actor=request.user,
                customer=customer,
                room=form.cleaned_data["room"],
                check_in_date=form.cleaned_data["check_in_date"],
                check_out_date=form.cleaned_data["check_out_date"],
                guest_count=form.cleaned_data["guest_count"],
                notes=form.cleaned_data["notes"],
            )
        except ValidationError as error:
            attach_service_error(form, error)
        else:
            messages.success(request, f"Đã tạo booking {booking.booking_code}. Vui lòng chờ xác nhận.")
            return redirect("customer-bookings:detail", pk=booking.pk)
    return render(request, "bookings/booking_form.html", {"form": form, "title": "Đặt phòng", "back_url": "customer-bookings:list"})


@role_required(User.Role.MANAGER, User.Role.RECEPTIONIST)
def staff_booking_list(request):
    bookings = Booking.objects.select_related("customer", "room", "room__room_type", "created_by")
    status = request.GET.get("status", "")
    query = request.GET.get("q", "").strip()
    if status in Booking.Status.values:
        bookings = bookings.filter(status=status)
    if query:
        bookings = bookings.filter(
            Q(booking_code__icontains=query)
            | Q(customer__full_name__icontains=query)
            | Q(room__room_number__icontains=query)
        )
    return render(
        request,
        "bookings/staff_booking_list.html",
        {"bookings": bookings, "statuses": Booking.Status.choices, "selected_status": status, "query": query},
    )


@role_required(User.Role.MANAGER, User.Role.RECEPTIONIST)
def staff_booking_detail(request, pk):
    booking = get_object_or_404(
        Booking.objects.select_related("customer", "room", "room__room_type", "created_by").prefetch_related("used_services__service"),
        pk=pk,
    )
    return render(request, "bookings/booking_detail.html", {"booking": booking})


@role_required(User.Role.MANAGER, User.Role.RECEPTIONIST)
def staff_booking_create(request):
    form = ReceptionistBookingForm(request.POST or None, initial=_booking_initial(request))
    if request.method == "POST" and form.is_valid():
        try:
            booking = create_booking(
                actor=request.user,
                customer=form.cleaned_data["customer"],
                room=form.cleaned_data["room"],
                check_in_date=form.cleaned_data["check_in_date"],
                check_out_date=form.cleaned_data["check_out_date"],
                guest_count=form.cleaned_data["guest_count"],
                notes=form.cleaned_data["notes"],
            )
        except ValidationError as error:
            attach_service_error(form, error)
        else:
            messages.success(request, f"Đã tạo và xác nhận booking {booking.booking_code}.")
            return redirect("bookings-staff:detail", pk=booking.pk)
    return render(request, "bookings/booking_form.html", {"form": form, "title": "Tạo booking cho khách", "back_url": "bookings-staff:list"})


def _run_booking_action(*, request, booking, action, success_message, reason=""):
    try:
        action(actor=request.user, booking=booking, **({"reason": reason} if action is cancel_booking else {}))
    except ValidationError as error:
        messages.error(request, " ".join(error.messages))
    else:
        messages.success(request, success_message)


@role_required(User.Role.MANAGER, User.Role.RECEPTIONIST)
@require_POST
def staff_booking_confirm(request, pk):
    booking = get_object_or_404(Booking, pk=pk)
    _run_booking_action(
        request=request,
        booking=booking,
        action=confirm_booking,
        success_message=f"Đã xác nhận booking {booking.booking_code}.",
    )
    return redirect("bookings-staff:detail", pk=pk)


@role_required(User.Role.MANAGER, User.Role.RECEPTIONIST)
@require_POST
def staff_booking_check_in(request, pk):
    booking = get_object_or_404(Booking, pk=pk)
    _run_booking_action(
        request=request,
        booking=booking,
        action=check_in_booking,
        success_message=f"Đã check-in booking {booking.booking_code}.",
    )
    return redirect("bookings-staff:detail", pk=pk)


@role_required(User.Role.MANAGER, User.Role.RECEPTIONIST)
@require_POST
def staff_booking_check_out(request, pk):
    booking = get_object_or_404(Booking, pk=pk)
    _run_booking_action(
        request=request,
        booking=booking,
        action=check_out_booking,
        success_message=f"Đã check-out booking {booking.booking_code}. Phòng chuyển sang đang dọn.",
    )
    return redirect("bookings-staff:detail", pk=pk)


@role_required(User.Role.MANAGER, User.Role.RECEPTIONIST)
@require_POST
def staff_booking_cancel(request, pk):
    booking = get_object_or_404(Booking, pk=pk)
    form = CancellationForm(request.POST)
    if form.is_valid():
        _run_booking_action(
            request=request,
            booking=booking,
            action=cancel_booking,
            reason=form.cleaned_data["reason"],
            success_message=f"Đã hủy booking {booking.booking_code}.",
        )
    else:
        messages.error(request, "Lý do hủy không hợp lệ.")
    return redirect("bookings-staff:detail", pk=pk)


@role_required(User.Role.CUSTOMER)
@require_POST
def customer_booking_cancel(request, pk):
    booking = get_object_or_404(Booking, pk=pk, customer__user=request.user)
    form = CancellationForm(request.POST)
    if form.is_valid():
        _run_booking_action(
            request=request,
            booking=booking,
            action=cancel_booking,
            reason=form.cleaned_data["reason"],
            success_message=f"Đã hủy booking {booking.booking_code}.",
        )
    else:
        messages.error(request, "Lý do hủy không hợp lệ.")
    return redirect("customer-bookings:detail", pk=pk)


@role_required(User.Role.MANAGER, User.Role.RECEPTIONIST)
def room_calendar(request):
    today = timezone.localdate()
    data = request.GET or {
        "start_date": today.isoformat(),
        "end_date": (today + timedelta(days=14)).isoformat(),
    }
    form = CalendarFilterForm(data)
    rows = []
    if form.is_valid():
        start_date = form.cleaned_data["start_date"]
        end_date = form.cleaned_data["end_date"]
        calendar_bookings = Booking.objects.filter(
            check_in_date__date__lte=end_date,
            check_out_date__date__gte=start_date,
        ).exclude(status=Booking.Status.CANCELLED).select_related("customer")
        rooms = Room.objects.filter(is_active=True).select_related("room_type").prefetch_related(
            Prefetch("bookings", queryset=calendar_bookings, to_attr="calendar_bookings")
        )
        rows = [{"room": room, "bookings": room.calendar_bookings} for room in rooms]
    return render(request, "bookings/room_calendar.html", {"form": form, "rows": rows})


@role_required(User.Role.MANAGER, User.Role.RECEPTIONIST)
@require_POST
def room_mark_available(request, pk):
    room = get_object_or_404(Room, pk=pk)
    try:
        mark_room_available_after_cleaning(actor=request.user, room=room)
    except ValidationError as error:
        messages.error(request, " ".join(error.messages))
    else:
        messages.success(request, f"Phòng {room.room_number} đã dọn xong và chuyển thành trống.")
    return redirect("rooms-staff:room-list")
