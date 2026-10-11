from io import StringIO

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse


class ProjectSmokeTests(TestCase):
    def test_home_page_is_available(self):
        response = self.client.get(reverse("core:home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "quản lý khách sạn")
        self.assertContains(response, "SPK Hotel")
        self.assertNotContains(response, "Đồ án Python · Django 5")
        self.assertNotContains(response, "Giai đoạn 1")
        self.assertNotContains(
            response,
            "Khung dự án và cơ sở dữ liệu đã sẵn sàng để phát triển.",
        )

    def test_health_check(self):
        response = self.client.get(reverse("core:health-check"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")

    def test_custom_user_model_uses_email(self):
        user_model = get_user_model()
        user = user_model.objects.create_user(
            email="CUSTOMER@example.com",
            password="StrongPass123!",
            full_name="Khách thử nghiệm",
        )
        self.assertEqual(user.email, "customer@example.com")
        self.assertEqual(user.role, user_model.Role.CUSTOMER)
        self.assertTrue(user.check_password("StrongPass123!"))


class SeedDemoTests(TestCase):
    def test_seed_demo_creates_examples_and_is_idempotent(self):
        from apps.bookings.models import Booking
        from apps.customers.models import Customer
        from apps.rooms.models import Room, RoomType
        from apps.services.models import Service
        from apps.billing.models import Invoice, Payment
        from apps.ai_integration.models import AILog, EmailDraft

        output = StringIO()
        call_command("seed_demo", stdout=output)
        call_command("seed_demo", stdout=output)

        self.assertEqual(RoomType.objects.filter(name__in=["Standard", "Deluxe", "Family Suite"]).count(), 3)
        self.assertEqual(Room.objects.filter(room_number__in=["101", "102", "103", "104", "201", "202", "203", "301", "302", "303"]).count(), 10)
        self.assertEqual(Customer.objects.filter(email__endswith="@spkhotel.vn").count(), 3)
        self.assertEqual(Booking.objects.filter(booking_code__startswith="DEMO-").count(), 5)
        self.assertEqual(Service.objects.count(), 4)
        self.assertEqual(Invoice.objects.count(), 3)
        self.assertEqual(Payment.objects.count(), 2)
        self.assertEqual(AILog.objects.count(), 1)
        self.assertEqual(EmailDraft.objects.count(), 1)
        manager = get_user_model().objects.get(email="quanli@hotel.com")
        self.assertTrue(manager.check_password("1"))
        accountant = get_user_model().objects.get(email="ketoan@hotel.com")
        self.assertTrue(accountant.check_password("1"))
        receptionist = get_user_model().objects.get(email="letan@hotel.com")
        self.assertTrue(receptionist.check_password("1"))
        self.assertFalse(get_user_model().objects.filter(email="receptionist@spkhotel.vn").exists())
        self.assertFalse(get_user_model().objects.filter(email="manager@spkhotel.vn").exists())
        self.assertFalse(get_user_model().objects.filter(email="accountant@spkhotel.vn").exists())
        self.assertContainsText(output.getvalue(), "Đã tạo/cập nhật dữ liệu demo")

    def assertContainsText(self, text, expected):
        self.assertIn(expected, text)
