from django.contrib import messages
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render

from apps.accounts.models import User
from apps.accounts.permissions import role_required
from apps.bookings.models import Booking

from .forms import BookingServiceForm, ServiceForm
from .models import Service
from .services import add_booking_service, save_service_catalog


@role_required(User.Role.MANAGER)
def service_list(request):
    return render(request, "services/service_list.html", {"services": Service.objects.all()})


@role_required(User.Role.MANAGER)
def service_create(request):
    form = ServiceForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        save_service_catalog(actor=request.user, form=form)
        messages.success(request, "Đã tạo dịch vụ.")
        return redirect("services-staff:list")
    return render(request, "services/service_form.html", {"form": form, "title": "Thêm dịch vụ"})


@role_required(User.Role.MANAGER)
def service_update(request, pk):
    service = get_object_or_404(Service, pk=pk)
    form = ServiceForm(request.POST or None, instance=service)
    if request.method == "POST" and form.is_valid():
        save_service_catalog(actor=request.user, form=form)
        messages.success(request, "Đã cập nhật dịch vụ.")
        return redirect("services-staff:list")
    return render(request, "services/service_form.html", {"form": form, "title": "Sửa dịch vụ"})


@role_required(User.Role.MANAGER, User.Role.RECEPTIONIST)
def booking_service_add(request, booking_id):
    booking = get_object_or_404(Booking.objects.select_related("customer", "room"), pk=booking_id)
    form = BookingServiceForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            add_booking_service(
                actor=request.user,
                booking=booking,
                service=form.cleaned_data["service"],
                quantity=form.cleaned_data["quantity"],
                used_at=form.cleaned_data["used_at"],
            )
        except ValidationError as error:
            form.add_error(None, " ".join(error.messages))
        else:
            messages.success(request, "Đã ghi nhận dịch vụ khách sử dụng.")
            return redirect("bookings-staff:detail", pk=booking.pk)
    return render(request, "services/booking_service_form.html", {"form": form, "booking": booking})
