from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from apps.accounts.models import User
from apps.accounts.permissions import role_required
from apps.bookings.models import Booking
from apps.billing.models import Invoice
from apps.rooms.models import Room
from django.db.models import Sum

from .forms import CustomerForm, CustomerProfileForm
from .models import Customer
from .services import save_customer_by_receptionist, update_own_profile


@role_required(User.Role.CUSTOMER)
def overview(request):
    bookings = Booking.objects.filter(customer__user=request.user)
    balance_due = Invoice.objects.filter(booking__customer__user=request.user).aggregate(total=Sum("balance_due"))["total"] or 0
    return render(
        request,
        "customers/overview.html",
        {
            "customer": request.user.customer_profile,
            "upcoming_booking_count": bookings.filter(
                status__in=[Booking.Status.PENDING, Booking.Status.CONFIRMED]
            ).count(),
            "stay_count": bookings.filter(status=Booking.Status.CHECKED_OUT).count(),
            "invoice_balance_due": balance_due,
            "rooms": Room.objects.select_related("room_type").filter(
                is_active=True, room_type__is_active=True
            ).order_by("floor", "room_number"),
        },
    )


@role_required(User.Role.CUSTOMER)
def profile_update(request):
    customer = request.user.customer_profile
    form = CustomerProfileForm(request.POST or None, instance=customer)
    if request.method == "POST" and form.is_valid():
        update_own_profile(actor=request.user, form=form)
        messages.success(request, "Đã cập nhật hồ sơ cá nhân.")
        return redirect("customers:profile")
    return render(request, "customers/profile_form.html", {"form": form})


@role_required(User.Role.MANAGER, User.Role.RECEPTIONIST)
def customer_list(request):
    customers = Customer.objects.select_related("user").order_by("full_name")
    return render(request, "customers/customer_list.html", {"customers": customers})


@role_required(User.Role.MANAGER, User.Role.RECEPTIONIST)
def customer_detail(request, pk):
    customer = get_object_or_404(Customer.objects.select_related("user"), pk=pk)
    return render(request, "customers/customer_detail.html", {"customer": customer})


@role_required(User.Role.MANAGER, User.Role.RECEPTIONIST)
def customer_create(request):
    form = CustomerForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        save_customer_by_receptionist(actor=request.user, form=form)
        messages.success(request, "Đã thêm khách hàng.")
        return redirect("customers-staff:customer-list")
    return render(request, "customers/customer_form.html", {"form": form, "title": "Thêm khách hàng"})


@role_required(User.Role.MANAGER, User.Role.RECEPTIONIST)
def customer_update(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    form = CustomerForm(request.POST or None, instance=customer)
    if request.method == "POST" and form.is_valid():
        save_customer_by_receptionist(actor=request.user, form=form)
        messages.success(request, "Đã cập nhật khách hàng.")
        return redirect("customers-staff:customer-detail", pk=customer.pk)
    return render(request, "customers/customer_form.html", {"form": form, "title": "Sửa khách hàng"})
