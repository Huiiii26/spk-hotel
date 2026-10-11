from datetime import date, timedelta
from decimal import Decimal

from django.db.models import Count, DecimalField, Sum
from django.db.models.functions import Coalesce, TruncDay, TruncMonth
from django.utils import timezone

from apps.billing.models import Invoice, Payment
from apps.bookings.models import Booking
from apps.rooms.models import Room
from apps.services.models import BookingService


ZERO_MONEY = Decimal("0")
OCCUPANCY_STATUSES = (
    Booking.Status.CONFIRMED,
    Booking.Status.CHECKED_IN,
    Booking.Status.CHECKED_OUT,
)


def _local_date(value):
    if hasattr(value, "hour"):
        if timezone.is_aware(value):
            value = timezone.localtime(value)
        return value.date()
    return value


def _money_sum(queryset, field="amount"):
    return queryset.aggregate(
        total=Coalesce(Sum(field), ZERO_MONEY, output_field=DecimalField(max_digits=18, decimal_places=0))
    )["total"]


def _period_start(value, group_by):
    value = value.date() if hasattr(value, "date") else value
    return value.replace(day=1) if group_by == "month" else value


def _periods(start_date, end_date, group_by):
    current = start_date.replace(day=1) if group_by == "month" else start_date
    final = end_date.replace(day=1) if group_by == "month" else end_date
    while current <= final:
        yield current
        if group_by == "month":
            current = (current.replace(day=28) + timedelta(days=4)).replace(day=1)
        else:
            current += timedelta(days=1)


def _period_label(value, group_by):
    return value.strftime("%m/%Y") if group_by == "month" else value.strftime("%d/%m")


def _time_series(queryset, datetime_field, value_field, start_date, end_date, group_by):
    trunc = TruncMonth(datetime_field) if group_by == "month" else TruncDay(datetime_field)
    rows = queryset.annotate(period=trunc).values("period").annotate(value=Sum(value_field)).order_by("period")
    totals = {_period_start(row["period"], group_by): row["value"] or 0 for row in rows}
    periods = list(_periods(start_date, end_date, group_by))
    return {
        "labels": [_period_label(period, group_by) for period in periods],
        "values": [float(totals.get(period, 0)) for period in periods],
    }


def _count_series(queryset, datetime_field, start_date, end_date, group_by):
    trunc = TruncMonth(datetime_field) if group_by == "month" else TruncDay(datetime_field)
    rows = queryset.annotate(period=trunc).values("period").annotate(value=Count("pk")).order_by("period")
    totals = {_period_start(row["period"], group_by): row["value"] for row in rows}
    periods = list(_periods(start_date, end_date, group_by))
    return {
        "labels": [_period_label(period, group_by) for period in periods],
        "values": [totals.get(period, 0) for period in periods],
    }


def calculate_occupancy(start_date, end_date):
    """Tính công suất theo số đêm phòng, với khoảng ngày lọc tính cả hai đầu."""

    end_exclusive = end_date + timedelta(days=1)
    active_rooms = Room.objects.filter(is_active=True).count()
    capacity_room_nights = active_rooms * (end_exclusive - start_date).days
    bookings = Booking.objects.filter(
        status__in=OCCUPANCY_STATUSES,
        check_in_date__date__lt=end_exclusive,
        check_out_date__date__gt=start_date,
        room__is_active=True,
    ).only("check_in_date", "check_out_date")
    occupied_room_nights = sum(
        (min(_local_date(booking.check_out_date), end_exclusive) - max(_local_date(booking.check_in_date), start_date)).days
        for booking in bookings
    )
    rate = round(occupied_room_nights * 100 / capacity_room_nights, 2) if capacity_room_nights else 0
    return {
        "occupied_room_nights": occupied_room_nights,
        "capacity_room_nights": capacity_room_nights,
        "available_room_nights": max(capacity_room_nights - occupied_room_nights, 0),
        "rate": rate,
    }


def build_report_data(start_date, end_date, group_by="day"):
    payment_queryset = Payment.objects.filter(paid_at__date__range=(start_date, end_date))
    created_bookings = Booking.objects.filter(created_at__date__range=(start_date, end_date))
    stay_bookings = Booking.objects.filter(
        check_in_date__date__lte=end_date,
        check_out_date__date__gt=start_date,
    ).exclude(status=Booking.Status.CANCELLED)
    occupancy = calculate_occupancy(start_date, end_date)

    top_room_type = (
        stay_bookings.values("room__room_type__name")
        .annotate(total=Count("pk"))
        .order_by("-total", "room__room_type__name")
        .first()
    )
    top_service = (
        BookingService.objects.filter(used_at__range=(start_date, end_date))
        .values("service__name")
        .annotate(total=Coalesce(Sum("quantity"), Decimal("0")))
        .order_by("-total", "service__name")
        .first()
    )
    room_type_revenue_rows = list(
        payment_queryset.values("invoice__booking__room__room_type__name")
        .annotate(total=Sum("amount"))
        .order_by("-total")
    )
    cancelled_count = created_bookings.filter(status=Booking.Status.CANCELLED).count()
    booking_count = created_bookings.count()

    return {
        "start_date": start_date,
        "end_date": end_date,
        "group_by": group_by,
        "revenue": _money_sum(payment_queryset),
        "booking_count": booking_count,
        "cancelled_count": cancelled_count,
        "cancellation_rate": round(cancelled_count * 100 / booking_count, 2) if booking_count else 0,
        "occupancy": occupancy,
        "top_room_type": top_room_type,
        "top_service": top_service,
        "unpaid_invoice_count": Invoice.objects.exclude(status=Invoice.Status.PAID).count(),
        "unpaid_balance": _money_sum(Invoice.objects.exclude(status=Invoice.Status.PAID), "balance_due"),
        "revenue_series": _time_series(payment_queryset, "paid_at", "amount", start_date, end_date, group_by),
        "booking_series": _count_series(created_bookings, "created_at", start_date, end_date, group_by),
        "occupancy_chart": {
            "labels": ["Đã sử dụng", "Còn trống"],
            "values": [occupancy["occupied_room_nights"], occupancy["available_room_nights"]],
        },
        "room_type_revenue": {
            "labels": [row["invoice__booking__room__room_type__name"] for row in room_type_revenue_rows],
            "values": [float(row["total"]) for row in room_type_revenue_rows],
        },
    }


def build_dashboard_summary(today=None):
    today = today or date.today()
    month_start = today.replace(day=1)
    report = build_report_data(month_start, today, "day")
    rooms = Room.objects.filter(is_active=True)
    active_bookings = Booking.objects.filter(
        status__in=(Booking.Status.PENDING, Booking.Status.CONFIRMED, Booking.Status.CHECKED_IN)
    )
    report.update(
        {
            "total_rooms": rooms.count(),
            "available_rooms": rooms.filter(status=Room.Status.AVAILABLE).count(),
            "occupied_rooms": rooms.filter(status=Room.Status.OCCUPIED).count(),
            "cleaning_rooms": rooms.filter(status=Room.Status.CLEANING).count(),
            "maintenance_rooms": rooms.filter(status=Room.Status.MAINTENANCE).count(),
            "active_booking_count": active_bookings.count(),
            "pending_booking_count": active_bookings.filter(status=Booking.Status.PENDING).count(),
            "guest_staying_count": active_bookings.filter(status=Booking.Status.CHECKED_IN).count(),
        }
    )
    return report
