from django.http import JsonResponse
from django.shortcuts import render

from apps.accounts.models import User
from apps.accounts.permissions import role_required
from apps.bookings.models import Booking
from apps.rooms.models import Room
from apps.reports.services import build_dashboard_summary


def home(request):
    return render(request, "core/home.html")


def health_check(request):
    return JsonResponse({"status": "ok", "service": "hotel-management"})


def error_404(request, exception):
    return render(request, "404.html", status=404)


def error_500(request):
    return render(request, "500.html", status=500)


@role_required(User.Role.MANAGER, User.Role.RECEPTIONIST, User.Role.ACCOUNTANT)
def staff_dashboard(request):
    rooms = Room.objects.select_related("room_type").filter(is_active=True)
    context = build_dashboard_summary()
    context.update({
        "recent_bookings": Booking.objects.select_related("customer", "room").order_by("-created_at")[:6],
        "room_rows": rooms.order_by("floor", "room_number")[:8],
    })
    return render(request, "core/staff_dashboard.html", context)
