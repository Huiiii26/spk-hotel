from datetime import date, datetime, time, timedelta
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import User
from apps.billing.models import Invoice, Payment
from apps.bookings.models import Booking
from apps.customers.models import Customer
from apps.rooms.models import Room, RoomType
from apps.services.models import BookingService, Service

from .forms import ReportFilterForm
from .services import build_report_data, calculate_occupancy


class ReportTestDataMixin:
    def setUp(self):
        self.manager = User.objects.create_user(email="manager-report@example.com", password="pass", full_name="Quản lý", role=User.Role.MANAGER)
        self.accountant = User.objects.create_user(email="accountant-report@example.com", password="pass", full_name="Kế toán", role=User.Role.ACCOUNTANT)
        self.receptionist = User.objects.create_user(email="reception-report@example.com", password="pass", full_name="Lễ tân", role=User.Role.RECEPTIONIST)
        self.customer_user = User.objects.create_user(email="customer-report@example.com", password="pass", full_name="Khách", role=User.Role.CUSTOMER)
        self.customer = Customer.objects.create(user=self.customer_user, full_name="Khách", email=self.customer_user.email)
        self.room_type = RoomType.objects.create(name="Deluxe báo cáo", capacity=2, price_per_night=1_000_000)
        self.room = Room.objects.create(room_number="R701", room_type=self.room_type, floor=7)
        self.second_room = Room.objects.create(room_number="R702", room_type=self.room_type, floor=7)
        self.start_date = date(2026, 9, 1)
        self.end_date = date(2026, 9, 5)

    def create_booking(self, *, status=Booking.Status.CONFIRMED, check_in=None, check_out=None, room=None):
        booking = Booking.objects.create(
            customer=self.customer, room=room or self.room, created_by=self.receptionist,
            check_in_date=check_in or self.start_date,
            check_out_date=check_out or self.start_date + timedelta(days=2),
            guest_count=1, room_price_per_night=1_000_000, status=status,
        )
        created_at = timezone.make_aware(datetime.combine(self.start_date, time(hour=9)))
        Booking.objects.filter(pk=booking.pk).update(created_at=created_at)
        booking.refresh_from_db()
        return booking


class ReportServiceTests(ReportTestDataMixin, TestCase):
    def test_revenue_uses_payments_in_selected_period(self):
        booking = self.create_booking(status=Booking.Status.CHECKED_OUT)
        invoice = Invoice.objects.create(booking=booking, room_amount=2_000_000, total_amount=2_000_000, paid_amount=750_000, balance_due=1_250_000, status=Invoice.Status.PARTIALLY_PAID)
        Payment.objects.create(invoice=invoice, amount=750_000, method=Payment.Method.CASH, paid_at=timezone.make_aware(datetime(2026, 9, 3, 10)), recorded_by=self.accountant)
        Payment.objects.create(invoice=invoice, amount=100_000, method=Payment.Method.CASH, paid_at=timezone.make_aware(datetime(2026, 8, 30, 10)), recorded_by=self.accountant)

        report = build_report_data(self.start_date, self.end_date)

        self.assertEqual(report["revenue"], Decimal("750000"))
        self.assertEqual(sum(report["revenue_series"]["values"]), 750_000)
        self.assertEqual(report["room_type_revenue"]["labels"], ["Deluxe báo cáo"])

    def test_occupancy_counts_overlapping_nights_and_ignores_pending_cancelled(self):
        self.create_booking(check_in=date(2026, 8, 31), check_out=date(2026, 9, 3))
        self.create_booking(status=Booking.Status.PENDING, check_in=date(2026, 9, 3), check_out=date(2026, 9, 5), room=self.second_room)
        self.create_booking(status=Booking.Status.CANCELLED, check_in=date(2026, 9, 3), check_out=date(2026, 9, 5), room=self.second_room)

        result = calculate_occupancy(self.start_date, self.end_date)

        self.assertEqual(result["occupied_room_nights"], 2)
        self.assertEqual(result["capacity_room_nights"], 10)
        self.assertEqual(result["rate"], 20.0)

    def test_top_room_type_and_service_are_aggregated_from_database(self):
        booking = self.create_booking()
        service = Service.objects.create(name="Ăn sáng báo cáo", unit_price=100_000, unit="suất")
        BookingService.objects.create(booking=booking, service=service, quantity=Decimal("3"), unit_price=100_000, line_total=300_000, used_at=date(2026, 9, 2), recorded_by=self.receptionist)

        report = build_report_data(self.start_date, self.end_date)

        self.assertEqual(report["top_room_type"]["room__room_type__name"], "Deluxe báo cáo")
        self.assertEqual(report["top_service"]["service__name"], "Ăn sáng báo cáo")
        self.assertEqual(report["top_service"]["total"], Decimal("3"))


class ReportViewTests(ReportTestDataMixin, TestCase):
    def test_manager_and_accountant_can_view_report(self):
        url = reverse("reports-staff:dashboard")
        for user in (self.manager, self.accountant):
            self.client.force_login(user)
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, "Báo cáo và thống kê")
            self.assertContains(response, "chart.js")
            self.client.logout()

    def test_receptionist_and_customer_are_denied(self):
        url = reverse("reports-staff:dashboard")
        for user in (self.receptionist, self.customer_user):
            self.client.force_login(user)
            self.assertEqual(self.client.get(url).status_code, 403)
            self.client.logout()

    def test_invalid_date_range_shows_backend_validation_error(self):
        self.client.force_login(self.manager)
        response = self.client.get(reverse("reports-staff:dashboard"), {"start_date": "2026-09-05", "end_date": "2026-09-01", "group_by": "day"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Đến ngày phải lớn hơn hoặc bằng từ ngày.")
        self.assertIsNone(response.context["report"])


class ReportFilterFormTests(TestCase):
    def test_range_over_366_days_is_invalid(self):
        form = ReportFilterForm(data={"start_date": "2025-01-01", "end_date": "2026-02-01", "group_by": "month"})
        self.assertFalse(form.is_valid())
        self.assertIn("366 ngày", str(form.non_field_errors()))
