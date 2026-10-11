from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.bookings.models import Booking
from apps.bookings.services import check_out_booking
from apps.customers.models import Customer
from apps.rooms.models import Room, RoomType
from apps.services.models import BookingService, Service

from .models import Invoice, Payment
from .services import create_or_update_invoice, record_payment


User = get_user_model()


class BillingFixtureMixin:
    @classmethod
    def setUpTestData(cls):
        cls.accountant = User.objects.create_user(email="bill-accountant@example.com", password="x", full_name="Kế toán", role=User.Role.ACCOUNTANT)
        cls.receptionist = User.objects.create_user(email="bill-rec@example.com", password="x", full_name="Lễ tân", role=User.Role.RECEPTIONIST)
        cls.manager = User.objects.create_user(email="bill-manager@example.com", password="x", full_name="Quản lý", role=User.Role.MANAGER)
        cls.customer_user = User.objects.create_user(email="bill-owner@example.com", password="x", full_name="Khách hóa đơn", role=User.Role.CUSTOMER)
        cls.other_user = User.objects.create_user(email="bill-other@example.com", password="x", full_name="Khách khác", role=User.Role.CUSTOMER)
        cls.customer = Customer.objects.create(user=cls.customer_user, full_name="Khách hóa đơn")
        cls.other_customer = Customer.objects.create(user=cls.other_user, full_name="Khách khác")
        cls.room_type = RoomType.objects.create(name="Billing Room", capacity=2, price_per_night=1000000)
        cls.room = Room.objects.create(room_number="I101", room_type=cls.room_type, floor=1, status=Room.Status.OCCUPIED)
        cls.booking = Booking.objects.create(customer=cls.customer, room=cls.room, check_in_date=date(2028, 2, 1), check_out_date=date(2028, 2, 4), guest_count=1, room_price_per_night=Decimal("1000000"), status=Booking.Status.CHECKED_IN)
        service = Service.objects.create(name="Ăn sáng", unit_price=100000, unit="suất")
        BookingService.objects.create(booking=cls.booking, service=service, quantity=2, unit_price=100000, used_at=date(2028, 2, 2), line_total=200000, recorded_by=cls.receptionist)


class InvoiceCalculationTests(BillingFixtureMixin, TestCase):
    def test_room_service_and_total_calculation(self):
        invoice = create_or_update_invoice(booking=self.booking, surcharge=Decimal("50000"), discount=Decimal("100000"))
        self.assertEqual(invoice.room_amount, Decimal("3000000"))
        self.assertEqual(invoice.service_amount, Decimal("200000"))
        self.assertEqual(invoice.total_amount, Decimal("3150000"))
        self.assertEqual(invoice.balance_due, Decimal("3150000"))
        self.assertEqual(invoice.status, Invoice.Status.UNPAID)

    def test_checkout_creates_invoice_and_moves_room_to_cleaning(self):
        checked_out = check_out_booking(actor=self.receptionist, booking=self.booking)
        invoice = Invoice.objects.get(booking=checked_out)
        self.room.refresh_from_db()
        self.assertEqual(invoice.total_amount, Decimal("3200000"))
        self.assertIsNotNone(invoice.finalized_at)
        self.assertEqual(self.room.status, Room.Status.CLEANING)

    def test_discount_cannot_make_total_negative(self):
        with self.assertRaises(ValidationError):
            create_or_update_invoice(booking=self.booking, discount=Decimal("99999999"))


class PaymentTests(BillingFixtureMixin, TestCase):
    def setUp(self):
        self.invoice = create_or_update_invoice(booking=self.booking)

    def pay(self, amount):
        return record_payment(actor=self.accountant, invoice=self.invoice, amount=Decimal(amount), method=Payment.Method.CASH, paid_at=timezone.now())

    def test_partial_payment(self):
        self.pay("1000000")
        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.paid_amount, Decimal("1000000"))
        self.assertEqual(self.invoice.balance_due, Decimal("2200000"))
        self.assertEqual(self.invoice.status, Invoice.Status.PARTIALLY_PAID)

    def test_multiple_payments_can_fully_pay_invoice(self):
        self.pay("1000000")
        self.pay("2200000")
        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.balance_due, 0)
        self.assertEqual(self.invoice.status, Invoice.Status.PAID)
        self.assertEqual(self.invoice.payments.count(), 2)

    def test_overpayment_is_rejected(self):
        with self.assertRaises(ValidationError):
            self.pay("3200001")
        self.assertEqual(Payment.objects.count(), 0)

    def test_receptionist_cannot_record_payment(self):
        with self.assertRaises(PermissionDenied):
            record_payment(actor=self.receptionist, invoice=self.invoice, amount=1000, method=Payment.Method.CASH, paid_at=timezone.now())

    def test_manager_can_record_payment(self):
        payment = record_payment(actor=self.manager, invoice=self.invoice, amount=1000, method=Payment.Method.CASH, paid_at=timezone.now())
        self.assertEqual(payment.recorded_by, self.manager)


class InvoiceOwnershipTests(BillingFixtureMixin, TestCase):
    def setUp(self):
        self.invoice = create_or_update_invoice(booking=self.booking)

    def test_customer_can_view_own_invoice(self):
        self.client.force_login(self.customer_user)
        response = self.client.get(reverse("customer-billing:detail", args=[self.invoice.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Thanh toán ngay")

    def test_customer_cannot_view_another_invoice(self):
        self.client.force_login(self.other_user)
        self.assertEqual(self.client.get(reverse("customer-billing:detail", args=[self.invoice.pk])).status_code, 404)

    def test_receptionist_cannot_record_payment(self):
        self.client.force_login(self.receptionist)
        self.assertEqual(self.client.get(reverse("billing-staff:payment-add", args=[self.invoice.pk])).status_code, 403)

    def test_accountant_cannot_change_surcharge_or_discount(self):
        self.client.force_login(self.accountant)
        self.assertEqual(self.client.get(reverse("billing-staff:adjust", args=[self.invoice.pk])).status_code, 403)

    def test_manager_can_open_invoice_adjustment_and_payment_forms(self):
        self.client.force_login(self.manager)
        self.assertEqual(self.client.get(reverse("billing-staff:adjust", args=[self.invoice.pk])).status_code, 200)
        self.assertEqual(self.client.get(reverse("billing-staff:payment-add", args=[self.invoice.pk])).status_code, 200)

    def test_customer_can_pay_own_invoice_in_one_click(self):
        self.client.force_login(self.customer_user)
        response = self.client.post(
            reverse("customer-billing:pay", args=[self.invoice.pk]),
            follow=True,
        )
        self.invoice.refresh_from_db()
        payment = self.invoice.payments.get()
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Thanh toán thành công")
        self.assertEqual(self.invoice.balance_due, 0)
        self.assertEqual(self.invoice.status, Invoice.Status.PAID)
        self.assertEqual(payment.recorded_by, self.customer_user)
        self.assertEqual(payment.method, Payment.Method.CARD)

    def test_customer_cannot_pay_another_customers_invoice(self):
        self.client.force_login(self.other_user)
        response = self.client.post(reverse("customer-billing:pay", args=[self.invoice.pk]))
        self.assertEqual(response.status_code, 404)
        self.assertFalse(self.invoice.payments.exists())

    def test_customer_payment_endpoint_rejects_get(self):
        self.client.force_login(self.customer_user)
        response = self.client.get(reverse("customer-billing:pay", args=[self.invoice.pk]))
        self.assertEqual(response.status_code, 405)

    def test_paid_invoice_cannot_be_paid_twice(self):
        self.client.force_login(self.customer_user)
        url = reverse("customer-billing:pay", args=[self.invoice.pk])
        self.client.post(url)
        response = self.client.post(url, follow=True)
        self.assertEqual(self.invoice.payments.count(), 1)
        self.assertContains(response, "Hóa đơn đã được thanh toán đầy đủ")
