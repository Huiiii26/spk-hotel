from datetime import datetime
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import User
from apps.ai_integration.models import EmailDraft
from apps.bookings.models import Booking
from apps.customers.models import Customer
from apps.rooms.models import Room, RoomType


class RestoredFeatureTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.customer_user = User.objects.create_user(
            email="feature-customer@example.com", password="pass12345", full_name="Khách thử", role=User.Role.CUSTOMER
        )
        cls.receptionist = User.objects.create_user(
            email="feature-staff@example.com", password="pass12345", full_name="Lễ tân thử", role=User.Role.RECEPTIONIST
        )
        cls.customer = Customer.objects.create(
            user=cls.customer_user, full_name="Khách thử", email=cls.customer_user.email
        )
        cls.room_type = RoomType.objects.create(
            name="Standard kiểm thử", capacity=2, price_per_hour=100000, price_per_night=650000
        )
        cls.available_room = Room.objects.create(
            room_number="T101", room_type=cls.room_type, floor=1, status=Room.Status.AVAILABLE
        )
        cls.occupied_room = Room.objects.create(
            room_number="T102", room_type=cls.room_type, floor=1, status=Room.Status.OCCUPIED
        )

    def _booking(self, check_in, check_out):
        return Booking.objects.create(
            customer=self.customer,
            room=self.available_room,
            created_by=self.receptionist,
            check_in_date=timezone.make_aware(check_in),
            check_out_date=timezone.make_aware(check_out),
            guest_count=1,
            room_price_per_hour=Decimal("100000"),
            room_price_per_night=Decimal("650000"),
        )

    def test_same_day_stay_is_billed_by_rounded_up_hours(self):
        booking = self._booking(datetime(2026, 10, 10, 8), datetime(2026, 10, 10, 13, 30))
        self.assertTrue(booking.is_hourly)
        self.assertEqual(booking.billable_hours, 6)
        self.assertEqual(booking.room_charge, Decimal("600000"))

    def test_overnight_stay_is_billed_by_calendar_days(self):
        booking = self._booking(datetime(2026, 10, 10, 20), datetime(2026, 10, 12, 9))
        self.assertFalse(booking.is_hourly)
        self.assertEqual(booking.number_of_days, 2)
        self.assertEqual(booking.room_charge, Decimal("1300000"))

    def test_customer_overview_shows_room_grid_and_dims_unavailable_room(self):
        self.client.force_login(self.customer_user)
        response = self.client.get(reverse("customers:overview"))
        self.assertContains(response, "Tình trạng phòng hiện tại")
        self.assertContains(response, "Phòng T101")
        self.assertContains(response, "Phòng T102")
        self.assertContains(response, "is-unavailable")

    def test_staff_can_cancel_ai_email_draft(self):
        booking = self._booking(datetime(2026, 10, 13, 8), datetime(2026, 10, 13, 12))
        draft = EmailDraft.objects.create(
            booking=booking,
            email_type=EmailDraft.EmailType.CONFIRMATION,
            recipient_email=self.customer.email,
            subject="Xác nhận",
            body="Nội dung",
            created_by=self.receptionist,
            generated_by_ai=True,
        )
        self.client.force_login(self.receptionist)
        response = self.client.post(reverse("ai-integration:email-cancel", args=[draft.pk]))
        self.assertRedirects(response, reverse("bookings-staff:detail", args=[booking.pk]))
        draft.refresh_from_db()
        self.assertEqual(draft.status, EmailDraft.Status.CANCELLED)

    def test_room_advisor_explains_when_filters_leave_no_room(self):
        self.client.force_login(self.customer_user)
        response = self.client.post(
            reverse("ai-integration:room-advisor"),
            {
                "check_in_date": "2026-11-10T08:00",
                "check_out_date": "2026-11-10T12:00",
                "guest_count": 3,
                "max_budget": 650000,
                "amenities": "",
                "needs": "Phòng yên tĩnh",
            },
        )
        self.assertContains(response, "Không có phòng phù hợp với bộ lọc hiện tại")
        self.assertNotContains(response, "SPK AI chưa sẵn sàng")

