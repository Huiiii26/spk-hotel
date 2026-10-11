from decimal import Decimal

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models import Sum
from django.utils import timezone

from apps.accounts.models import User
from apps.bookings.models import Booking

from .models import Invoice, Payment


ZERO = Decimal("0")


def _status_for(total, paid):
    if paid <= 0:
        return Invoice.Status.UNPAID
    if paid < total:
        return Invoice.Status.PARTIALLY_PAID
    return Invoice.Status.PAID


@transaction.atomic
def create_or_update_invoice(*, booking, surcharge=None, discount=None):
    locked_booking = Booking.objects.select_for_update().get(pk=booking.pk)
    invoice, _ = Invoice.objects.select_for_update().get_or_create(booking=locked_booking)
    if surcharge is not None:
        invoice.surcharge = surcharge
    if discount is not None:
        invoice.discount = discount
    if invoice.surcharge < 0 or invoice.discount < 0:
        raise ValidationError("Phụ thu và giảm giá không được âm.")

    room_amount = locked_booking.room_charge
    service_amount = locked_booking.used_services.aggregate(total=Sum("line_total"))["total"] or ZERO
    total_amount = room_amount + service_amount + invoice.surcharge - invoice.discount
    if total_amount < 0:
        raise ValidationError("Giảm giá không được lớn hơn tổng tiền trước giảm.")
    paid_amount = invoice.payments.aggregate(total=Sum("amount"))["total"] or ZERO
    if paid_amount > total_amount:
        raise ValidationError("Tổng tiền không được nhỏ hơn số đã thanh toán.")

    invoice.room_amount = room_amount
    invoice.service_amount = service_amount
    invoice.total_amount = total_amount
    invoice.paid_amount = paid_amount
    invoice.balance_due = total_amount - paid_amount
    invoice.status = _status_for(total_amount, paid_amount)
    if locked_booking.status == Booking.Status.CHECKED_OUT:
        invoice.finalized_at = invoice.finalized_at or timezone.now()
    invoice.save()
    return invoice


@transaction.atomic
def adjust_invoice(*, actor, invoice, surcharge, discount):
    if actor.role not in (User.Role.MANAGER, User.Role.RECEPTIONIST):
        raise PermissionDenied("Chỉ quản lý hoặc lễ tân được nhập phụ thu và giảm giá.")
    return create_or_update_invoice(
        booking=invoice.booking,
        surcharge=surcharge,
        discount=discount,
    )


@transaction.atomic
def record_payment(*, actor, invoice, amount, method, paid_at, reference="", notes=""):
    if actor.role not in (User.Role.MANAGER, User.Role.ACCOUNTANT):
        raise PermissionDenied("Chỉ quản lý hoặc kế toán được ghi nhận thanh toán.")
    locked_invoice = Invoice.objects.select_for_update().select_related("booking").get(pk=invoice.pk)
    locked_invoice = create_or_update_invoice(booking=locked_invoice.booking)
    if amount <= 0:
        raise ValidationError({"amount": "Số tiền thanh toán phải lớn hơn 0."})
    if amount > locked_invoice.balance_due:
        raise ValidationError({"amount": "Số tiền vượt quá công nợ còn lại."})
    payment = Payment.objects.create(
        invoice=locked_invoice,
        amount=amount,
        method=method,
        paid_at=paid_at,
        recorded_by=actor,
        reference=reference.strip(),
        notes=notes.strip(),
    )
    create_or_update_invoice(booking=locked_invoice.booking)
    return payment


@transaction.atomic
def customer_pay_full_demo(*, actor, invoice):
    """Thanh toán giả lập toàn bộ công nợ; không kết nối hoặc lưu dữ liệu ngân hàng."""

    if actor.role != User.Role.CUSTOMER or invoice.booking.customer.user_id != actor.pk:
        raise PermissionDenied("Bạn chỉ được thanh toán hóa đơn của chính mình.")
    locked_invoice = Invoice.objects.select_for_update().select_related("booking").get(pk=invoice.pk)
    locked_invoice = create_or_update_invoice(booking=locked_invoice.booking)
    if locked_invoice.balance_due <= 0:
        raise ValidationError("Hóa đơn đã được thanh toán đầy đủ.")
    payment = Payment.objects.create(
        invoice=locked_invoice,
        amount=locked_invoice.balance_due,
        method=Payment.Method.CARD,
        paid_at=timezone.now(),
        recorded_by=actor,
        reference=f"DEMO-CUSTOMER-{locked_invoice.pk}-{timezone.now().strftime('%Y%m%d%H%M%S')}",
        notes="Thanh toán giả lập bởi khách hàng; không phát sinh giao dịch ngân hàng thật.",
    )
    create_or_update_invoice(booking=locked_invoice.booking)
    return payment
