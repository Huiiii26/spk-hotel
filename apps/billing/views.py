from django.contrib import messages
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from apps.accounts.models import User
from apps.accounts.permissions import role_required

from .forms import InvoiceAdjustmentForm, PaymentForm
from .models import Invoice
from .services import adjust_invoice, customer_pay_full_demo, record_payment


STAFF_INVOICE_ROLES = (User.Role.MANAGER, User.Role.RECEPTIONIST, User.Role.ACCOUNTANT)


@role_required(*STAFF_INVOICE_ROLES)
def invoice_list(request):
    invoices = Invoice.objects.select_related("booking", "booking__customer", "booking__room")
    status = request.GET.get("status", "")
    if status in Invoice.Status.values:
        invoices = invoices.filter(status=status)
    return render(request, "billing/invoice_list.html", {"invoices": invoices, "statuses": Invoice.Status.choices, "selected_status": status})


@role_required(*STAFF_INVOICE_ROLES)
def invoice_detail(request, pk):
    invoice = get_object_or_404(
        Invoice.objects.select_related("booking", "booking__customer", "booking__room", "booking__room__room_type").prefetch_related("payments", "booking__used_services__service"),
        pk=pk,
    )
    return render(request, "billing/invoice_detail.html", {"invoice": invoice})


@role_required(User.Role.MANAGER, User.Role.RECEPTIONIST)
def invoice_adjust(request, pk):
    invoice = get_object_or_404(Invoice.objects.select_related("booking"), pk=pk)
    form = InvoiceAdjustmentForm(request.POST or None, initial={"surcharge": invoice.surcharge, "discount": invoice.discount})
    if request.method == "POST" and form.is_valid():
        try:
            adjust_invoice(actor=request.user, invoice=invoice, **form.cleaned_data)
        except ValidationError as error:
            form.add_error(None, " ".join(error.messages))
        else:
            messages.success(request, "Đã cập nhật phụ thu và giảm giá.")
            return redirect("billing-staff:detail", pk=invoice.pk)
    return render(request, "billing/invoice_adjust_form.html", {"form": form, "invoice": invoice})


@role_required(User.Role.MANAGER, User.Role.ACCOUNTANT)
def payment_add(request, pk):
    invoice = get_object_or_404(Invoice.objects.select_related("booking"), pk=pk)
    form = PaymentForm(request.POST or None, initial={"amount": invoice.balance_due, "paid_at": timezone.localtime()})
    if request.method == "POST" and form.is_valid():
        try:
            record_payment(actor=request.user, invoice=invoice, **form.cleaned_data)
        except ValidationError as error:
            if hasattr(error, "message_dict"):
                for field, errors in error.message_dict.items():
                    for message in errors:
                        form.add_error(field if field in form.fields else None, message)
            else:
                form.add_error(None, " ".join(error.messages))
        else:
            messages.success(request, "Đã ghi nhận thanh toán.")
            return redirect("billing-staff:detail", pk=invoice.pk)
    return render(request, "billing/payment_form.html", {"form": form, "invoice": invoice})


@role_required(User.Role.CUSTOMER)
def customer_invoice_list(request):
    invoices = Invoice.objects.select_related("booking", "booking__room").filter(booking__customer__user=request.user)
    return render(request, "billing/customer_invoice_list.html", {"invoices": invoices})


@role_required(User.Role.CUSTOMER)
def customer_invoice_detail(request, pk):
    invoice = get_object_or_404(
        Invoice.objects.select_related("booking", "booking__room", "booking__room__room_type").prefetch_related("payments", "booking__used_services__service"),
        pk=pk,
        booking__customer__user=request.user,
    )
    return render(request, "billing/invoice_detail.html", {"invoice": invoice})


@role_required(User.Role.CUSTOMER)
@require_POST
def customer_invoice_pay(request, pk):
    invoice = get_object_or_404(
        Invoice.objects.select_related("booking", "booking__customer"),
        pk=pk,
        booking__customer__user=request.user,
    )
    try:
        customer_pay_full_demo(actor=request.user, invoice=invoice)
    except ValidationError as error:
        messages.error(request, " ".join(error.messages))
    else:
        messages.success(request, "Thanh toán thành công! Hóa đơn đã được thanh toán đầy đủ (giao dịch giả lập).")
    return redirect("customer-billing:detail", pk=invoice.pk)
